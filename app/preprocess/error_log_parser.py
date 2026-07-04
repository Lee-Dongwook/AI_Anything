"""Error Log Parser: distill a full Playwright log into the core failure reason."""

import structlog

logger = structlog.get_logger(__name__)


def parse_error_log(raw_log: str) -> str:
    """Extract only the essentials from a raw Playwright failure log.

    Target output: the ``Error:`` line, the failing line number, and the top stack
    frame reason (e.g. ``locator.click: Timeout 5000ms waiting for selector...``).

    TODO: implement extraction (regex over ``Error:`` / ``at`` frames + call location).
    """
    logger.debug("parse_error_log_called", raw_len=len(raw_log))
    raise NotImplementedError
