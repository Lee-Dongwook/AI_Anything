"""Test Runner node: write the patched test and run Playwright."""

import subprocess

import structlog

from app.config import settings
from app.state import AgentState

logger = structlog.get_logger(__name__)


def test_runner(state: AgentState) -> dict:
    """Write ``current_code`` to disk and run Playwright via subprocess.

    Returns a partial state update: on pass ``{"is_success": True}``; on fail
    ``{"is_success": False, "error_log": <new log>, "loop_count": n + 1}``.

    TODO: write file, run ``settings.playwright_cmd`` on ``test_script_path``,
    branch on the return code, and re-parse the log on failure.
    """
    logger.info("test_runner_started", test_script_path=state["test_script_path"])
    _ = (subprocess, settings)  # wired for use once the run logic lands
    raise NotImplementedError
