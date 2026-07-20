"""Provider-neutral LLM configuration: generic llm_* fields and nvidia_* back-compat."""

from typing import Any

import pytest
from pydantic import ValidationError

from app.config import Settings


def make_settings(**overrides: Any) -> Settings:
    """Build Settings ignoring any local .env so tests stay hermetic."""
    return Settings(_env_file=None, **overrides)  # type: ignore[call-arg]


def test_defaults_to_nvidia_provider():
    assert make_settings().llm_provider == "nvidia"


def test_legacy_nvidia_key_backfills_generic_field():
    # An existing E2E_HEALER_NVIDIA_API_KEY-only setup must keep working: the legacy key
    # is folded into the generic llm_api_key, along with the nvidia base_url/model defaults.
    settings = make_settings(nvidia_api_key="nvapi-legacy")
    assert settings.llm_api_key == "nvapi-legacy"
    assert settings.llm_base_url == "https://integrate.api.nvidia.com/v1"
    assert settings.llm_model == "openai/gpt-oss-120b"


def test_explicit_generic_field_overrides_legacy():
    settings = make_settings(nvidia_api_key="nvapi-legacy", llm_api_key="explicit")
    assert settings.llm_api_key == "explicit"


def test_legacy_max_tokens_only_maps_when_set():
    assert make_settings(nvidia_max_tokens=8192).llm_max_tokens == 8192


def test_non_nvidia_provider_ignores_legacy_fields():
    # A different provider must not inherit NVIDIA's key/base_url/model.
    settings = make_settings(
        llm_provider="openai",
        nvidia_api_key="nvapi-legacy",
        llm_api_key="sk-openai",
    )
    assert settings.llm_api_key == "sk-openai"
    assert settings.llm_base_url == ""
    assert settings.llm_model == ""


@pytest.mark.parametrize("provider", ["nvidia", "openai", "anthropic", "ollama"])
def test_known_providers_are_accepted(provider):
    assert make_settings(llm_provider=provider).llm_provider == provider


def test_unknown_provider_is_rejected():
    with pytest.raises(ValidationError):
        make_settings(llm_provider="foobar")


def test_jsx_chunk_margin_lines_rejects_negative_values():
    with pytest.raises(ValidationError):
        make_settings(jsx_chunk_margin_lines=-1)
