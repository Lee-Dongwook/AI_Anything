"""Concrete Playwright ``trace.zip`` parser for the Shadow Runtime.

The archive holds JSONL trace streams (``*.trace`` / ``*.network``) plus a
``resources/`` folder of SHA-1 addressed response bodies. Network activity lives
in ``resource-snapshot`` events, each a HAR entry already pairing a request with
its response. We map those entries onto the existing schema models
(:class:`CapturedRequest`, :class:`CapturedResponse`, :class:`NetworkSnapshot`);
snapshot assembly, persistence and replay are later stages.
"""

import base64
import json
import zipfile
from datetime import datetime
from pathlib import Path

import structlog

from app.shadow.interfaces import ITraceParser
from app.shadow.schemas import CapturedRequest, CapturedResponse, NetworkSnapshot

logger = structlog.get_logger(__name__)

# Newer Playwright writes resources to ``*.network``, older embeds them in
# ``*.trace``; preferring ``*.network`` avoids double-counting across streams.
_NETWORK_SUFFIX = ".network"
_TRACE_SUFFIX = ".trace"
_RESOURCE_SNAPSHOT = "resource-snapshot"  # trace event holding a HAR entry
_RESOURCES_PREFIX = "resources/"


class TraceParseError(Exception):
    """Base exception for trace parsing failures."""


class InvalidTraceArchiveError(TraceParseError):
    """Raised when a trace archive is missing, unreadable, or not a Playwright trace."""


class PlaywrightTraceParser(ITraceParser):
    """Reads a Playwright ``trace.zip`` and extracts its network interactions.

    :meth:`parse` returns request/response pairs as chronologically ordered
    :class:`NetworkSnapshot`. Non-network events are ignored; malformed lines and
    incomplete interactions are skipped with a warning rather than aborting.
    """

    def parse(self, trace_path: Path) -> list[NetworkSnapshot]:
        """Parse ``trace_path`` into its captured network interactions.

        Raises :class:`InvalidTraceArchiveError` when the path is missing, is not
        a readable zip, or has no trace streams. No network activity yields ``[]``.
        """
        path = Path(trace_path)
        if not path.exists():
            raise InvalidTraceArchiveError(f"Trace archive does not exist: {path}")
        if not path.is_file():
            raise InvalidTraceArchiveError(f"Trace path is not a file: {path}")

        logger.info("trace_parse_started", path=str(path))

        try:
            with zipfile.ZipFile(path) as archive:
                if archive.testzip() is not None:
                    raise InvalidTraceArchiveError(f"Trace archive is corrupted: {path}")

                stream_names = self._select_trace_streams(archive.namelist())
                if not stream_names:
                    raise InvalidTraceArchiveError(
                        f"No Playwright trace streams found in archive: {path}"
                    )

                entries = self._collect_har_entries(archive, stream_names)
                snapshots = self._build_snapshots(archive, entries)
        except zipfile.BadZipFile as exc:
            logger.exception("trace_archive_invalid", path=str(path))
            raise InvalidTraceArchiveError(f"Not a valid zip archive: {path}") from exc
        except OSError as exc:
            logger.exception("trace_archive_unreadable", path=str(path))
            raise InvalidTraceArchiveError(f"Failed to read trace archive: {path}") from exc

        logger.info("trace_parse_finished", path=str(path), event_count=len(snapshots))
        return snapshots

    @staticmethod
    def _select_trace_streams(names: list[str]) -> list[str]:
        """Pick the JSONL streams to read, preferring ``*.network`` over ``*.trace``."""
        network = [name for name in names if name.endswith(_NETWORK_SUFFIX)]
        if network:
            return network
        return [name for name in names if name.endswith(_TRACE_SUFFIX)]

    def _collect_har_entries(self, archive: zipfile.ZipFile, stream_names: list[str]) -> list[dict]:
        """Read the selected streams and return the HAR entries of network events."""
        entries: list[dict] = []
        for name in stream_names:
            raw = archive.read(name).decode("utf-8", errors="replace")
            for line_no, line in enumerate(raw.splitlines(), start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    logger.warning("trace_line_skipped", stream=name, line=line_no)
                    continue
                if not isinstance(event, dict) or event.get("type") != _RESOURCE_SNAPSHOT:
                    continue  # ignore non-network trace events
                snapshot = event.get("snapshot")
                if isinstance(snapshot, dict):
                    entries.append(snapshot)
        return entries

    def _build_snapshots(
        self, archive: zipfile.ZipFile, entries: list[dict]
    ) -> list[NetworkSnapshot]:
        """Map HAR entries onto ordered :class:`NetworkSnapshot` models."""
        # Order by monotonic time; entries lacking it keep order (stable sort).
        ordered = sorted(entries, key=lambda entry: self._monotonic_time(entry))

        snapshots: list[NetworkSnapshot] = []
        sequence = 0
        for entry in ordered:
            snapshot = self._to_network_snapshot(archive, entry, sequence)
            if snapshot is None:
                continue
            snapshots.append(snapshot)
            sequence += 1
        return snapshots

    def _to_network_snapshot(
        self, archive: zipfile.ZipFile, entry: dict, sequence: int
    ) -> NetworkSnapshot | None:
        """Build a single :class:`NetworkSnapshot`, or ``None`` if incomplete."""
        request = self._to_request(entry.get("request"))
        if request is None:
            logger.warning("network_event_skipped", reason="missing_request")
            return None

        response = self._to_response(archive, entry.get("response"))
        if response is None:
            # Pending/failed request; NetworkSnapshot needs both halves, so drop.
            logger.warning("network_event_skipped", reason="missing_response", url=request.url)
            return None

        return NetworkSnapshot(
            request=request,
            response=response,
            sequence=sequence,
            started_at=self._started_at(entry),
            duration_ms=self._duration_ms(entry),
        )

    def _to_request(self, request: dict | None) -> CapturedRequest | None:
        """Map a HAR request object onto :class:`CapturedRequest`."""
        if not isinstance(request, dict):
            return None
        method = request.get("method")
        url = request.get("url")
        if not isinstance(method, str) or not isinstance(url, str) or not method or not url:
            return None

        post_data = request.get("postData")
        body = post_data.get("text") if isinstance(post_data, dict) else None
        return CapturedRequest(
            method=method,
            url=url,
            headers=self._headers_to_dict(request.get("headers")),
            body=body if isinstance(body, str) else None,
        )

    def _to_response(
        self, archive: zipfile.ZipFile, response: dict | None
    ) -> CapturedResponse | None:
        """Map a HAR response object onto :class:`CapturedResponse`."""
        if not isinstance(response, dict):
            return None
        status = response.get("status")
        # Playwright records 0/-1 when no response ever arrived.
        if not isinstance(status, int) or status <= 0:
            return None

        body, is_base64 = self._resolve_response_body(archive, response.get("content"))
        return CapturedResponse(
            status=status,
            headers=self._headers_to_dict(response.get("headers")),
            body=body,
            is_base64=is_base64,
        )

    def _resolve_response_body(
        self, archive: zipfile.ZipFile, content: dict | None
    ) -> tuple[str | None, bool]:
        """Resolve a HAR ``content`` into ``(body, is_base64)``.

        Body is inline (``text``) or a SHA-1 resource (``_sha1``); binary payloads
        are base64-encoded with the flag set.
        """
        if not isinstance(content, dict):
            return None, False

        text = content.get("text")
        if isinstance(text, str):
            return text, content.get("encoding") == "base64"

        sha1 = content.get("_sha1")
        if not isinstance(sha1, str) or not sha1:
            return None, False

        raw = self._read_resource(archive, sha1)
        if raw is None:
            return None, False

        try:
            return raw.decode("utf-8"), False
        except UnicodeDecodeError:
            return base64.b64encode(raw).decode("ascii"), True

    @staticmethod
    def _read_resource(archive: zipfile.ZipFile, sha1: str) -> bytes | None:
        """Read a response body from the archive's ``resources/`` folder by SHA-1."""
        name = f"{_RESOURCES_PREFIX}{sha1}"
        try:
            return archive.read(name)
        except KeyError:
            logger.warning("trace_resource_missing", sha1=sha1)
            return None

    @staticmethod
    def _headers_to_dict(headers: object) -> dict[str, str]:
        """Convert HAR ``[{"name", "value"}]`` header lists into a plain dict."""
        result: dict[str, str] = {}
        if not isinstance(headers, list):
            return result
        for header in headers:
            if not isinstance(header, dict):
                continue
            name = header.get("name")
            if not isinstance(name, str) or not name:
                continue
            value = header.get("value")
            result[name] = value if isinstance(value, str) else ""
        return result

    @staticmethod
    def _monotonic_time(entry: dict) -> float:
        """Return the entry's monotonic time for ordering; missing sorts first."""
        value = entry.get("_monotonicTime")
        return float(value) if isinstance(value, (int, float)) else float("-inf")

    @staticmethod
    def _started_at(entry: dict) -> float | None:
        """Parse the HAR ``startedDateTime`` (ISO 8601) into epoch seconds."""
        started = entry.get("startedDateTime")
        if not isinstance(started, str) or not started:
            return None
        try:
            return datetime.fromisoformat(started.replace("Z", "+00:00")).timestamp()
        except ValueError:
            return None

    @staticmethod
    def _duration_ms(entry: dict) -> float | None:
        """Return the HAR ``time`` (total duration in ms) when numeric."""
        value = entry.get("time")
        return float(value) if isinstance(value, (int, float)) else None
