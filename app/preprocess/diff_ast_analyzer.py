"""Diff-JSX AST Analyzer: turn a git diff into before/after DOM node trees."""

import structlog

from app.schemas import DomDiff

logger = structlog.get_logger(__name__)


def analyze_diff(git_diff: str) -> list[DomDiff]:
    """Parse the JSX/TSX regions of a git diff into lightweight DOM diffs.

    For each changed element, capture the tag and attributes (id, className, data-*,
    role, etc.) before and after, so the Diagnoser can map a broken selector to the
    exact attribute that changed.

    TODO: parse JSX/TSX with tree-sitter (tree-sitter-typescript); walk changed
    hunks and emit one DomDiff per modified element.
    """
    logger.debug("analyze_diff_called", diff_len=len(git_diff))
    raise NotImplementedError