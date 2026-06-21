"""Smoke-test the shared provider from the second-stage generation boundary."""

from __future__ import annotations

import json
from typing import Any

from agent.providers import LLMMessage, LLMProvider, ProviderError, provider_from_env

GENERATION_PROVIDER_SMOKE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["ok", "stage", "summary"],
    "properties": {
        "ok": {"type": "boolean"},
        "stage": {"type": "string"},
        "summary": {"type": "string"},
    },
}


def build_generation_smoke_messages() -> list[LLMMessage]:
    """Return a tiny JSON-only prompt for generation provider verification."""
    return [
        LLMMessage(
            role="system",
            content=(
                "You are validating the Yahaha generation graph LLM provider. "
                "Return only a JSON object matching the requested schema."
            ),
        ),
        LLMMessage(
            role="user",
            content=(
                "Return {\"ok\": true, \"stage\": "
                "\"generation_provider_smoke\", \"summary\": \"ready\"}."
            ),
        ),
    ]


def run_provider_smoke(provider: LLMProvider | None = None) -> dict[str, Any]:
    """Call the configured provider and require a minimal JSON response."""
    active_provider = provider or provider_from_env()
    try:
        response = active_provider.complete_json(
            messages=build_generation_smoke_messages(),
            response_schema=GENERATION_PROVIDER_SMOKE_SCHEMA,
            temperature=1.0,
            max_completion_tokens=200,
        )
    except Exception as exc:
        return {
            "ok": False,
            "stage": "generation_provider_smoke",
            "summary": _safe_provider_error_summary(str(exc)),
        }
    return _normalize_smoke_response(response)


def _normalize_smoke_response(response: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": bool(response.get("ok")),
        "stage": str(response.get("stage", "")),
        "summary": str(response.get("summary", "")),
    }


def _safe_provider_error_summary(message: str) -> str:
    lowered = message.lower()
    if "429" in message:
        return "LLM provider rate limited: 429"
    if "configuration" in lowered or "missing" in lowered:
        return "LLM provider configuration incomplete"
    if "invalid json preview:" in lowered:
        return message
    if "invalid json" in lowered:
        return "LLM provider returned invalid JSON"
    if message.startswith("LLM provider JSON "):
        return message
    if "request failed" in lowered:
        return "LLM provider request failed"
    return "LLM provider smoke failed"


def main() -> None:
    """Print a secret-safe provider smoke result."""
    result = run_provider_smoke()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result.get("ok"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
