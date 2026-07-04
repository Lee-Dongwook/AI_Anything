"""CLI core: the single entry point for a repair run (also what CI invokes)."""

import subprocess
from pathlib import Path
from typing import Optional

import structlog
import typer
from rich.console import Console

from app.config import settings
from app.graph import build_graph
from app.logging import configure_logging
from app.preprocess.diff_ast_analyzer import analyze_diff
from app.preprocess.error_log_parser import parse_error_log
from app.schemas import RepairSummary
from app.state import AgentState

app = typer.Typer(help="AI-driven E2E test self-healing engine")
console = Console(stderr=True)  # human output on stderr; JSON summary on stdout
logger = structlog.get_logger(__name__)


def _read_diff(diff_file: Optional[Path]) -> str:
    """Return the git diff from a file, or fall back to `git diff`."""
    if diff_file is not None:
        return diff_file.read_text()
    result = subprocess.run(["git", "diff"], capture_output=True, text=True, check=True)
    return result.stdout


@app.command()
def heal(
    test_path: Path = typer.Argument(..., exists=True, help="failing Playwright test file"),
    log_file: Path = typer.Option(..., "--log", exists=True, help="raw Playwright failure log"),
    diff_file: Optional[Path] = typer.Option(None, "--diff", help="git diff file; defaults to `git diff`"),
    json_output: bool = typer.Option(False, "--json", help="emit RepairSummary JSON to stdout"),
) -> None:
    """Repair a single failing test. Exit 0 if fixed, non-zero otherwise."""
    configure_logging(settings.log_level)

    error_log = parse_error_log(log_file.read_text())
    dom_diff = analyze_diff(_read_diff(diff_file))
    original_code = test_path.read_text()

    initial_state: AgentState = {
        "test_script_path": str(test_path),
        "original_code": original_code,
        "current_code": original_code,
        "error_log": error_log,
        "dom_diff_context": [d.model_dump() for d in dom_diff],
        "analysis_report": "",
        "patch_instructions": {},
        "loop_count": 0,
        "is_success": False,
    }

    logger.info("repair_run_started", test_script_path=str(test_path))
    final_state: AgentState = build_graph().invoke(initial_state)

    summary = RepairSummary(
        test_script_path=final_state["test_script_path"],
        is_success=final_state["is_success"],
        loop_count=final_state["loop_count"],
    )

    if json_output:
        typer.echo(summary.model_dump_json())
    status = "fixed" if summary.is_success else "not fixed"
    console.print(f"[bold]{status}[/bold] after {summary.loop_count} loop(s)")

    logger.info("repair_run_finished", is_success=summary.is_success, loop_count=summary.loop_count)
    raise typer.Exit(code=0 if summary.is_success else 1)


if __name__ == "__main__":
    app()
