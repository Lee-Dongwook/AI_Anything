"""Unit tests for app.shadow.normalizer.RequestNormalizer.

RequestNormalizer is a pure, deterministic transform, so these tests run
fully in-memory with no network access or external dependencies, per the
issue's acceptance criteria.
"""

import pytest

from app.shadow.normalizer import RequestNormalizer


@pytest.fixture
def normalizer():
    return RequestNormalizer()


# --- normalize_value ----------------------------------------------------------


def test_normalize_value_replaces_uuid(normalizer):
    val = "id-550e8400-e29b-41d4-a716-446655440000-end"
    assert normalizer.normalize_value(val) == "id-<UUID>-end"


def test_normalize_value_replaces_iso_timestamp(normalizer):
    val = "created at 2024-01-01T12:00:00Z"
    assert normalizer.normalize_value(val) == "created at <TIMESTAMP>"


def test_normalize_value_replaces_iso_timestamp_with_offset(normalizer):
    val = "created at 2024-01-01T12:00:00+05:30"
    assert normalizer.normalize_value(val) == "created at <TIMESTAMP>"


def test_normalize_value_replaces_epoch_timestamp(normalizer):
    val = "ts=1718000000000 done"
    assert normalizer.normalize_value(val) == "ts=<TIMESTAMP> done"


def test_normalize_value_replaces_multiple_patterns_in_one_string(normalizer):
    val = "req 550e8400-e29b-41d4-a716-446655440000 at 2024-01-01T12:00:00Z"
    assert normalizer.normalize_value(val) == "req <UUID> at <TIMESTAMP>"


def test_normalize_value_leaves_plain_text_unchanged(normalizer):
    assert normalizer.normalize_value("hello world") == "hello world"


def test_normalize_value_converts_non_string_to_string(normalizer):
    assert normalizer.normalize_value(123) == "123"
    assert normalizer.normalize_value(True) == "True"


# --- normalize_url: path canonicalization --------------------------------------


def test_normalize_url_replaces_uuid_in_path(normalizer):
    path, _ = normalizer.normalize_url(
        "http://example.com/api/users/550e8400-e29b-41d4-a716-446655440000"
    )
    assert path == "/api/users/<UUID>"


def test_normalize_url_static_path_is_unchanged(normalizer):
    path, _ = normalizer.normalize_url("http://example.com/api/users/list")
    assert path == "/api/users/list"


def test_normalize_url_two_different_uuids_normalize_to_same_path(normalizer):
    path1, _ = normalizer.normalize_url("/api/users/550e8400-e29b-41d4-a716-446655440000")
    path2, _ = normalizer.normalize_url("/api/users/123e4567-e89b-12d3-a456-426614174000")
    assert path1 == path2


# --- normalize_url: query canonicalization --------------------------------------


def test_normalize_url_keeps_static_query_params(normalizer):
    _, query = normalizer.normalize_url("/api/x?a=1&b=2")
    assert query == {"a": ["1"], "b": ["2"]}


def test_normalize_url_strips_dynamic_query_keys(normalizer):
    _, query = normalizer.normalize_url("/api/x?a=1&timestamp=999&nonce=abc&sig=xyz")
    assert query == {"a": ["1"]}
    assert "timestamp" not in query
    assert "nonce" not in query
    assert "sig" not in query


def test_normalize_url_dynamic_key_check_is_case_insensitive(normalizer):
    _, query = normalizer.normalize_url("/api/x?Timestamp=999&a=1")
    assert query == {"a": ["1"]}


def test_normalize_url_normalizes_values_within_query_params(normalizer):
    _, query = normalizer.normalize_url("/api/x?req_id=550e8400-e29b-41d4-a716-446655440000")
    assert query == {"req_id": ["<UUID>"]}


def test_normalize_url_no_query_string_returns_empty_dict(normalizer):
    _, query = normalizer.normalize_url("/api/x")
    assert query == {}


def test_normalize_url_repeated_query_key_keeps_all_values(normalizer):
    _, query = normalizer.normalize_url("/api/x?tag=a&tag=b")
    assert query == {"tag": ["a", "b"]}


def test_normalize_url_query_param_order_does_not_affect_result(normalizer):
    _, query1 = normalizer.normalize_url("/api/x?a=1&b=2")
    _, query2 = normalizer.normalize_url("/api/x?b=2&a=1")
    assert query1 == query2


# --- normalize_headers ----------------------------------------------------------


def test_normalize_headers_lowercases_keys(normalizer):
    result = normalizer.normalize_headers({"Content-Type": "application/json"})
    assert result == {"content-type": "application/json"}


def test_normalize_headers_strips_dynamic_headers(normalizer):
    result = normalizer.normalize_headers(
        {
            "Authorization": "Bearer secret",
            "Cookie": "session=abc",
            "Date": "Mon, 01 Jan 2024 00:00:00 GMT",
            "Content-Type": "application/json",
        }
    )
    assert result == {"content-type": "application/json"}


def test_normalize_headers_normalizes_values(normalizer):
    result = normalizer.normalize_headers({"X-Request-Id": "550e8400-e29b-41d4-a716-446655440000"})
    assert result == {"x-request-id": "<UUID>"}


def test_normalize_headers_empty_input_returns_empty_dict(normalizer):
    assert normalizer.normalize_headers({}) == {}


def test_normalize_headers_keeps_all_non_dynamic_headers(normalizer):
    result = normalizer.normalize_headers({"Accept": "application/json", "X-Custom": "value"})
    assert result == {"accept": "application/json", "x-custom": "value"}


# --- normalize_body: None / empty ------------------------------------------------


def test_normalize_body_none_returns_empty_string(normalizer):
    assert normalizer.normalize_body(None) == ""


def test_normalize_body_empty_string_returns_empty_string(normalizer):
    assert normalizer.normalize_body("") == ""


# --- normalize_body: JSON --------------------------------------------------------


def test_normalize_body_parses_and_normalizes_json_object(normalizer):
    body = '{"x": 1, "req_id": "550e8400-e29b-41d4-a716-446655440000"}'
    result = normalizer.normalize_body(body)
    assert result == {"x": 1, "req_id": "<UUID>"}


def test_normalize_body_replaces_dynamic_keys_with_placeholder(normalizer):
    body = '{"session_id": "abc123", "x": 1}'
    result = normalizer.normalize_body(body)
    assert result == {"session_id": "<DYNAMIC>", "x": 1}


def test_normalize_body_dynamic_key_check_is_case_insensitive(normalizer):
    body = '{"Token": "abc123", "x": 1}'
    result = normalizer.normalize_body(body)
    assert result == {"Token": "<DYNAMIC>", "x": 1}


def test_normalize_body_recurses_into_nested_objects(normalizer):
    body = '{"outer": {"session_id": "abc", "y": 2}}'
    result = normalizer.normalize_body(body)
    assert result == {"outer": {"session_id": "<DYNAMIC>", "y": 2}}


def test_normalize_body_recurses_into_lists(normalizer):
    body = '{"items": [{"x": 1}, {"session_id": "abc"}]}'
    result = normalizer.normalize_body(body)
    assert result == {"items": [{"x": 1}, {"session_id": "<DYNAMIC>"}]}


def test_normalize_body_normalizes_string_values_in_json(normalizer):
    body = '{"created_at": "2024-01-01T12:00:00Z"}'
    result = normalizer.normalize_body(body)
    assert result == {"created_at": "<TIMESTAMP>"}


def test_normalize_body_non_string_json_values_are_untouched(normalizer):
    body = '{"count": 5, "active": true, "ratio": 1.5, "missing": null}'
    result = normalizer.normalize_body(body)
    assert result == {"count": 5, "active": True, "ratio": 1.5, "missing": None}


# --- normalize_body: non-JSON text ----------------------------------------------


def test_normalize_body_falls_back_to_text_scrubbing_for_non_json(normalizer):
    body = "user 550e8400-e29b-41d4-a716-446655440000 logged in"
    result = normalizer.normalize_body(body)
    assert result == "user <UUID> logged in"


def test_normalize_body_scrubs_timestamp_in_plain_text(normalizer):
    body = "event at 2024-01-01T12:00:00Z"
    result = normalizer.normalize_body(body)
    assert result == "event at <TIMESTAMP>"


# --- Determinism ---------------------------------------------------------------


def test_normalize_url_is_deterministic(normalizer):
    url = "/api/x?a=1&b=2"
    assert normalizer.normalize_url(url) == normalizer.normalize_url(url)


def test_normalize_body_is_deterministic(normalizer):
    body = '{"x": 1, "session_id": "abc"}'
    assert normalizer.normalize_body(body) == normalizer.normalize_body(body)


def test_normalize_headers_is_deterministic(normalizer):
    headers = {"Content-Type": "application/json", "Authorization": "Bearer x"}
    assert normalizer.normalize_headers(headers) == normalizer.normalize_headers(headers)
