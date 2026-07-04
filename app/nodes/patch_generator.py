"""Patch Generator node: produce a narrow, schema-constrained fix."""

import structlog

from app.llm import generate_patch
from app.state import AgentState

logger = structlog.get_logger(__name__)

SYSTEM_PROMPT = (
    "You repair Playwright E2E tests. You may ONLY fix failing locators (selectors) "
    "and optimize wait conditions. Never change assertions or test business logic. "
    "Return edits strictly as the provided schema."
)


def patch_generator(state: AgentState) -> dict:
    """Generate a targeted patch via Structured Outputs and apply it to ``current_code``.

    Returns a partial state update: ``{"current_code": ..., "patch_instructions": ...}``.

    On JSON/parse failure, feed the error back into the LLM instead of crashing the
    graph (internal exception loop). TODO: implement prompt build + apply patch.
    """
    logger.info("patch_generator_started", loop_count=state["loop_count"])
    _ = generate_patch  # wired for use once the prompt/apply logic lands
    raise NotImplementedError
