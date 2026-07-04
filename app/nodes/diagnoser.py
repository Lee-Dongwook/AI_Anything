"""Diagnoser node: infer why the test broke."""

import structlog

from app.state import AgentState

logger = structlog.get_logger(__name__)


def diagnoser(state: AgentState) -> dict:
    """Map the failing selector in ``error_log`` to the DOM change in
    ``dom_diff_context`` and produce an ``analysis_report``.

    Returns a partial state update: ``{"analysis_report": ...}``.

    TODO: build the diagnosis prompt from error_log + dom_diff_context + current_code.
    """
    logger.info("diagnoser_started", loop_count=state["loop_count"])
    raise NotImplementedError
