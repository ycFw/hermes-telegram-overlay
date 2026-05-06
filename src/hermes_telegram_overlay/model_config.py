"""Helpers for fixed model configuration."""

from __future__ import annotations

from urllib.parse import urlparse, urlunparse

from .constants import DEFAULT_LITELLM_BASE_URL, DEFAULT_MODEL


class ModelConfigError(ValueError):
    """Raised when the LiteLLM endpoint config is invalid."""


def validate_litellm_base_url(base_url: str) -> str:
    """Validate that the custom endpoint is a concrete `/v1` URL."""
    candidate = (base_url or "").strip()
    if not candidate:
        raise ModelConfigError("LiteLLM base_url is required.")

    parsed = urlparse(candidate)
    if not parsed.scheme or not parsed.netloc:
        raise ModelConfigError(f"LiteLLM base_url is invalid: {candidate}")

    clean_path = parsed.path.rstrip("/")
    if clean_path != "/v1":
        raise ModelConfigError(
            f"LiteLLM base_url must end with /v1 for chat_completions mode: {candidate}"
        )

    return urlunparse(parsed._replace(path="/v1"))


def build_model_config(base_url: str = DEFAULT_LITELLM_BASE_URL, model: str = DEFAULT_MODEL) -> dict:
    """Build the fixed Hermes model config required by the overlay."""
    return {
        "model": {
            "default": model,
            "provider": "custom",
            "base_url": validate_litellm_base_url(base_url),
            "api_mode": "chat_completions",
        }
    }

