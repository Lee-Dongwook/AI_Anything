"""Tests for the standalone HAR trace parser."""

import json
from pathlib import Path

import pytest

from app.shadow.har_parser import HarTraceParser, InvalidHarFileError
from app.shadow.interfaces import ITraceParser
from app.shadow.trace_parser import TraceParseError

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample.har"


def test_implements_trace_parser_contract() -> None:
    assert isinstance(HarTraceParser(), ITraceParser)


def test_parses_standalone_har_fixture() -> None:
    snapshots = HarTraceParser().parse(FIXTURE_PATH)

    assert len(snapshots) == 2
    first, second = snapshots

    assert first.request.method == "POST"
    assert first.request.url == "https://api.example.com/items"
    assert first.request.headers == {"Accept": "application/json"}
    assert first.request.body == '{"name":"widget"}'
    assert first.response.status == 201
    assert first.response.headers == {"Content-Type": "application/json"}
    assert first.response.body == '{"id":42}'
    assert first.response.is_base64 is False
    assert first.sequence == 0
    assert first.duration_ms == 15.5
    assert first.started_at is not None

    assert second.request.method == "GET"
    assert second.response.body == "iVBORw0KGgo="
    assert second.response.is_base64 is True
    assert second.sequence == 1
    assert second.duration_ms == 4.0


def test_skips_incomplete_entries_and_keeps_sequences_contiguous(tmp_path: Path) -> None:
    document = {
        "log": {
            "entries": [
                {"request": {"method": "GET", "url": "https://example.com/pending"}},
                {
                    "request": {"method": "GET", "url": "https://example.com/ok"},
                    "response": {"status": 200, "headers": [], "content": {"text": "ok"}},
                },
            ]
        }
    }
    path = tmp_path / "partial.har"
    path.write_text(json.dumps(document), encoding="utf-8")

    snapshots = HarTraceParser().parse(path)

    assert len(snapshots) == 1
    assert snapshots[0].request.url == "https://example.com/ok"
    assert snapshots[0].sequence == 0


def test_empty_entries_returns_empty_list(tmp_path: Path) -> None:
    path = tmp_path / "empty.har"
    path.write_text('{"log":{"version":"1.2","entries":[]}}', encoding="utf-8")

    assert HarTraceParser().parse(path) == []


@pytest.mark.parametrize(
    "content",
    [
        "not json",
        "[]",
        '{"log": {}}',
        '{"log": {"entries": {}}}',
    ],
)
def test_invalid_har_document_raises(tmp_path: Path, content: str) -> None:
    path = tmp_path / "invalid.har"
    path.write_text(content, encoding="utf-8")

    with pytest.raises(InvalidHarFileError):
        HarTraceParser().parse(path)


def test_missing_file_and_directory_raise(tmp_path: Path) -> None:
    with pytest.raises(InvalidHarFileError):
        HarTraceParser().parse(tmp_path / "missing.har")
    with pytest.raises(InvalidHarFileError):
        HarTraceParser().parse(tmp_path)


def test_invalid_utf8_raises_typed_error(tmp_path: Path) -> None:
    path = tmp_path / "invalid-encoding.har"
    path.write_bytes(b"\xff\xfe")

    with pytest.raises(InvalidHarFileError):
        HarTraceParser().parse(path)


def test_error_derives_from_trace_parse_error() -> None:
    assert issubclass(InvalidHarFileError, TraceParseError)
