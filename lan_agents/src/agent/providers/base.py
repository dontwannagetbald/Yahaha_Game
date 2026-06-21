"""Provider interfaces and configuration helpers."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


class ProviderError(RuntimeError):
    """Base class for provider failures safe to summarize upstream."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.details = details


class ProviderConfigurationError(ProviderError):
    """Raised when provider configuration is incomplete."""


@dataclass(frozen=True)
class LLMMessage:
    """A chat message sent to an LLM provider."""

    role: str
    content: str


@dataclass(frozen=True)
class ReferenceAttachment:
    """A user-uploaded non-image/video file passed as model reference input."""

    asset_id: str
    filename: str
    mime_type: str
    local_path: str = ""
    user_hint: str = ""


@dataclass(frozen=True)
class ProviderConfig:
    """Environment-backed LLM provider configuration."""

    provider: str = "mock"
    api_key: str = ""
    base_url: str = ""
    model: str = ""
    timeout_seconds: float = 180.0

    @classmethod
    def from_env(
        cls,
        *,
        model_env_name: str = "OPENAI_COMPATIBLE_MODEL",
        fallback_model_env_name: str | None = None,
    ) -> "ProviderConfig":
        """Build provider configuration from environment variables."""
        dotenv_values = _load_nearest_dotenv()
        timeout = _env_value(
            "LLM_TIMEOUT_SECONDS",
            dotenv_values,
            _env_value("OPENAI_COMPATIBLE_TIMEOUT_SECONDS", dotenv_values, "180"),
        )
        try:
            timeout_seconds = float(timeout)
        except ValueError:
            timeout_seconds = 180.0
        model = _env_value(model_env_name, dotenv_values, "")
        if not model and fallback_model_env_name:
            model = _env_value(fallback_model_env_name, dotenv_values, "")
        return cls(
            provider=_env_value("LLM_PROVIDER", dotenv_values, "mock") or "mock",
            api_key=_env_value("OPENAI_COMPATIBLE_API_KEY", dotenv_values, ""),
            base_url=_env_value("OPENAI_COMPATIBLE_BASE_URL", dotenv_values, ""),
            model=model,
            timeout_seconds=timeout_seconds,
        )


class LLMProvider(Protocol):
    """Minimal JSON-completion interface shared by graph services."""

    def complete_json(
        self,
        *,
        messages: list[LLMMessage],
        response_schema: dict[str, Any],
        temperature: float = 1.0,
        max_completion_tokens: int = 1200,
    ) -> dict[str, Any]:
        """Return a JSON object for the requested task."""

    def complete_json_with_attachments(
        self,
        *,
        messages: list[LLMMessage],
        response_schema: dict[str, Any],
        attachments: list[dict[str, Any]],
        temperature: float = 1.0,
        max_completion_tokens: int = 1200,
    ) -> dict[str, Any]:
        """Return a JSON object while passing temporary reference attachments."""


def provider_from_env(
    *,
    model_env_name: str = "OPENAI_COMPATIBLE_MODEL",
    fallback_model_env_name: str | None = None,
) -> LLMProvider:
    """Create the configured provider from process environment."""
    return provider_from_config(
        ProviderConfig.from_env(
            model_env_name=model_env_name,
            fallback_model_env_name=fallback_model_env_name,
        )
    )


def provider_from_config(config: ProviderConfig) -> LLMProvider:
    """Create a provider implementation from config."""
    provider = config.provider.lower()
    if provider == "mock":
        from agent.providers.mock import MockLLMProvider

        return MockLLMProvider()
    if provider in {"openai", "openai-compatible", "openai_compatible"}:
        from agent.providers.openai_compatible import OpenAICompatibleLLMProvider

        return OpenAICompatibleLLMProvider(config)
    raise ProviderConfigurationError(f"Unsupported LLM provider: {config.provider}")


def _env_value(name: str, dotenv_values: dict[str, str], default: str) -> str:
    value = os.getenv(name)
    if value is None:
        value = dotenv_values.get(name, default)
    return value.strip()


def _load_nearest_dotenv() -> dict[str, str]:
    """Load `.env` values from cwd or its parents without overriding process env."""
    values: dict[str, str] = {}
    for directory in [Path.cwd(), *Path.cwd().parents]:
        env_path = directory / ".env"
        if not env_path.exists():
            continue
        for line in env_path.read_text().splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            values.setdefault(key.strip(), value.strip().strip('"').strip("'"))
    return values
