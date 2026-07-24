"""Standalone HTTP Archive (HAR) parser for the Shadow Runtime."""

import json
from pathlib import Path

import structlog

from app.shadow.har_entry import (
    duration_ms_from_har,
    inline_body_from_har,
    request_from_har,
    response_from_har,
    started_at_from_har,
)
from app.shadow.interfaces import ITraceParser
from app.shadow.schemas import NetworkSnapshot
from app.shadow.trace_parser import TraceParseError

logger = structlog.get_logger(__name__)


class InvalidHarFileError(TraceParseError):
    """Raised when a standalone HAR file is missing, unreadable, or malformed."""


class HarTraceParser(ITraceParser):
    """Parse standalone HAR 1.x files into normalized network snapshots."""

    def parse(self, trace_path: Path) -> list[NetworkSnapshot]:
        """Parse ``trace_path`` and return its complete request/response entries."""
        path = Path(trace_path)
        if not path.exists():
            raise InvalidHarFileError(f"HAR file does not exist: {path}")
        if not path.is_file():
            raise InvalidHarFileError(f"HAR path is not a file: {path}")

        logger.info("har_parse_started", path=str(path))
        try:
            document = json.loads(path.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError as exc:
            logger.exception("har_json_invalid", path=str(path))
            raise InvalidHarFileError(f"HAR file is not valid JSON: {path}") from exc
        except (OSError, UnicodeError) as exc:
            logger.exception("har_file_unreadable", path=str(path))
            raise InvalidHarFileError(f"Failed to read HAR file: {path}") from exc

        entries = self._ordered_entries(self._entries_from_document(document, path))
        snapshots: list[NetworkSnapshot] = []
        for entry_index, entry in enumerate(entries):
            snapshot = self._to_network_snapshot(entry, len(snapshots))
            if snapshot is None:
                logger.warning("har_entry_skipped", entry=entry_index)
                continue
            snapshots.append(snapshot)

        logger.info("har_parse_finished", path=str(path), event_count=len(snapshots))
        return snapshots

    @staticmethod
    def _entries_from_document(document: object, path: Path) -> list[object]:
        """Read the standard ``log.entries`` list or raise a typed parse error."""
        if not isinstance(document, dict):
            raise InvalidHarFileError(f"HAR root must be an object: {path}")
        log = document.get("log")
        if not isinstance(log, dict) or not isinstance(log.get("entries"), list):
            raise InvalidHarFileError(f"HAR file has no log.entries list: {path}")
        return log["entries"]

    @staticmethod
    def _ordered_entries(entries: list[object]) -> list[object]:
        """Order timestamped entries chronologically and keep fallback ordering stable."""
        return sorted(entries, key=HarTraceParser._entry_sort_key)

    @staticmethod
    def _entry_sort_key(entry: object) -> tuple[bool, float]:
        """Sort invalid or missing timestamps after valid timestamps."""
        if not isinstance(entry, dict):
            return True, 0.0
        started_at = started_at_from_har(entry)
        return started_at is None, started_at or 0.0

    @staticmethod
    def _to_network_snapshot(entry: object, sequence: int) -> NetworkSnapshot | None:
        """Normalize one complete HAR entry, skipping invalid or pending entries."""
        if not isinstance(entry, dict):
            return None
        request = request_from_har(entry.get("request"))
        response = response_from_har(entry.get("response"), inline_body_from_har)
        if request is None or response is None:
            return None
        return NetworkSnapshot(
            request=request,
            response=response,
            sequence=sequence,
            started_at=started_at_from_har(entry),
            duration_ms=duration_ms_from_har(entry),
        )
