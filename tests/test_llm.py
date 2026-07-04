"""The LLM client must be import-safe: no credentials needed to import or collect."""

import pytest

from app import llm
from app.config import settings


def test_get_client_requires_key(monkeypatch):
    llm._get_client.cache_clear()
    monkeypatch.setattr(settings, "nvidia_api_key", "")
    with pytest.raises(RuntimeError, match="NVIDIA_API_KEY"):
        llm._get_client()
    llm._get_client.cache_clear()  # don't leak the empty-key client to other tests


def test_import_does_not_build_client():
    # Importing app.llm must not instantiate a client; _get_client is lazy + cached.
    llm._get_client.cache_clear()
    assert llm._get_client.cache_info().currsize == 0
