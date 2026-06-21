"""Safe provider configuration preflight helpers."""

from __future__ import annotations

import json
from typing import Any

from agent.providers.base import ProviderConfig

RECOMMENDED_CONVERSATION_MODEL = "gpt-5.4-mini"


def provider_preflight_summary(config: ProviderConfig) -> dict[str, Any]:
    """Return a secret-safe summary of the active LLM provider config."""
    return {
        "provider": config.provider,
        "api_key": _set_status(config.api_key),
        "base_url": _set_status(config.base_url),
        "model": config.model or "UNSET",
        "timeout_seconds": config.timeout_seconds,
        "recommended_conversation_model": RECOMMENDED_CONVERSATION_MODEL,
    }


def _set_status(value: str) -> str:
    return "SET" if value else "UNSET"


def main() -> None:
    """Print the active provider config without exposing secrets."""
    summary = provider_preflight_summary(ProviderConfig.from_env())
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
