"""Extract Playwright's failure-time page (ARIA) snapshot from ``error-context.md``.

On failure, recent Playwright writes ``test-results/<name>/error-context.md`` containing a
``# Page snapshot`` section — a YAML accessibility tree of the page **at the moment of
failure** (after navigation/interaction). This is a hallucination-resistant, deep-state
view of the page, captured with no test modification and no trace parsing.
"""

import re
from pathlib import Path

import structlog

from app.sandbox import SandboxViolation, assert_read_allowed

logger = structlog.get_logger(__name__)

# The "# Page snapshot" section holds a ```yaml ... ``` fenced ARIA tree.
_SNAPSHOT_RE = re.compile(r"#\s*Page snapshot\s*```ya?ml\s*\n(.*?)\n```", re.DOTALL)


def extract_page_snapshot(error_context_md: str) -> str:
    """Return the ARIA page-snapshot YAML from an error-context.md body, or '' if absent."""
    match = _SNAPSHOT_RE.search(error_context_md)
    return match.group(1).strip() if match else ""


def read_failure_snapshot(results_dir: Path) -> str:
    """Return the ARIA page snapshot from the newest error-context.md under ``results_dir``.

    Returns '' when no results dir or snapshot exists, so callers degrade gracefully.
    """
    if not results_dir.exists():
        return ""
    try:
        assert_read_allowed(results_dir)
    except SandboxViolation as exc:
        logger.warning("failure_snapshot_sandbox_denied", path=str(results_dir), error=str(exc))
        return ""

    contexts = []
    for path in results_dir.rglob("*error-context*.md"):
        try:
            assert_read_allowed(path)
        except SandboxViolation as exc:
            logger.warning("failure_snapshot_file_sandbox_denied", path=str(path), error=str(exc))
            continue
        contexts.append(path)

    contexts = sorted(contexts, key=lambda p: p.stat().st_mtime, reverse=True)
    if not contexts:
        return ""

    snapshot = extract_page_snapshot(contexts[0].read_text())
    logger.info("failure_snapshot_read", chars=len(snapshot), source=str(contexts[0]))
    return snapshot
