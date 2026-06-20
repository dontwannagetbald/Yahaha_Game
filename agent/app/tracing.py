from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any


def _env_bool(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


def resolve_langsmith_settings() -> dict[str, Any]:
    enabled = _env_bool(os.getenv("LANGSMITH_TRACING"))
    api_key = os.getenv("LANGSMITH_API_KEY")
    endpoint = os.getenv("LANGSMITH_ENDPOINT")
    project = os.getenv("LANGSMITH_PROJECT", "yahaha-agent")

    if enabled and not api_key:
        raise RuntimeError("LANGSMITH_API_KEY is required when LANGSMITH_TRACING=true")

    return {
        "enabled": enabled,
        "api_key": api_key,
        "endpoint": endpoint,
        "project": project,
    }


def build_run_config(
    *,
    command: str,
    payload: dict[str, Any],
    provider: str | None = None,
    output_dir: str | None = None,
) -> dict[str, Any]:
    metadata = {
        "command": command,
        "provider": provider or "n/a",
        "asset_count": len(payload.get("uploaded_assets", [])),
        "has_confirmation_card": "confirmation_card" in payload,
    }
    if output_dir is not None:
        metadata["output_dir"] = output_dir

    return {
        "run_name": f"yahaha-agent-{command}",
        "tags": ["yahaha-agent", command] + ([provider] if provider else []),
        "metadata": metadata,
    }


@contextmanager
def open_langsmith_tracing(
    *,
    command: str,
    payload: dict[str, Any],
    provider: str | None = None,
    output_dir: str | None = None,
):
    settings = resolve_langsmith_settings()
    run_config = build_run_config(
        command=command,
        payload=payload,
        provider=provider,
        output_dir=output_dir,
    )

    if not settings["enabled"]:
        yield run_config
        return

    try:
        from langsmith import Client, tracing_context
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "langsmith package is required when LANGSMITH_TRACING=true"
        ) from exc

    client = Client(
        api_key=settings["api_key"],
        api_url=settings["endpoint"],
    )
    with tracing_context(
        enabled=True,
        project_name=settings["project"],
        tags=run_config["tags"],
        metadata=run_config["metadata"],
        client=client,
    ):
        yield run_config
