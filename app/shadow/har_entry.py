"""Shared normalization helpers for HAR-backed trace parsers."""

from collections.abc import Callable
from datetime import datetime

from app.shadow.schemas import CapturedRequest, CapturedResponse

BodyResolver = Callable[[object], tuple[str | None, bool]]


def headers_to_dict(headers: object) -> dict[str, str]:
    """Convert HAR header lists into the normalized dictionary representation."""
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


def request_from_har(request: object) -> CapturedRequest | None:
    """Map a HAR request object onto the normalized request schema."""
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
        headers=headers_to_dict(request.get("headers")),
        body=body if isinstance(body, str) else None,
    )


def response_from_har(
    response: object,
    resolve_body: BodyResolver,
) -> CapturedResponse | None:
    """Map a HAR response object using the supplied content-body resolver."""
    if not isinstance(response, dict):
        return None
    status = response.get("status")
    if not isinstance(status, int) or status <= 0:
        return None

    body, is_base64 = resolve_body(response.get("content"))
    return CapturedResponse(
        status=status,
        headers=headers_to_dict(response.get("headers")),
        body=body,
        is_base64=is_base64,
    )


def inline_body_from_har(content: object) -> tuple[str | None, bool]:
    """Resolve a standard HAR inline response body and its base64 marker."""
    if not isinstance(content, dict):
        return None, False
    text = content.get("text")
    if not isinstance(text, str):
        return None, False
    return text, content.get("encoding") == "base64"


def started_at_from_har(entry: dict) -> float | None:
    """Parse HAR ``startedDateTime`` into epoch seconds."""
    started = entry.get("startedDateTime")
    if not isinstance(started, str) or not started:
        return None
    try:
        return datetime.fromisoformat(started.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def duration_ms_from_har(entry: dict) -> float | None:
    """Return the HAR total duration in milliseconds when numeric."""
    value = entry.get("time")
    return float(value) if isinstance(value, (int, float)) else None
