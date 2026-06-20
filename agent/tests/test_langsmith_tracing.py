from __future__ import annotations

from argparse import Namespace
from contextlib import contextmanager

import pytest

from app import runner
from app.tracing import build_run_config, resolve_langsmith_settings


def test_build_run_config_contains_run_name_tags_and_metadata():
    config = build_run_config(
        command="generate",
        payload={"confirmation_card": {"title": "霓虹生存者"}, "uploaded_assets": [1, 2]},
        provider="mock",
        output_dir="output/demo",
    )

    assert config["run_name"] == "yahaha-agent-generate"
    assert "yahaha-agent" in config["tags"]
    assert "generate" in config["tags"]
    assert config["metadata"]["asset_count"] == 2
    assert config["metadata"]["provider"] == "mock"
    assert config["metadata"]["has_confirmation_card"] is True


def test_resolve_langsmith_settings_requires_api_key_when_enabled(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("LANGSMITH_TRACING", "true")
    monkeypatch.delenv("LANGSMITH_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="LANGSMITH_API_KEY"):
        resolve_langsmith_settings()


def test_conversation_command_uses_langsmith_context(monkeypatch: pytest.MonkeyPatch, tmp_path):
    captured: dict[str, object] = {}

    def fake_read_input(_path: str) -> dict[str, object]:
        return {"prompt": "make a game", "uploaded_assets": []}

    def fake_run_conversation(payload: dict[str, object], config: dict[str, object] | None = None):
        captured["payload"] = payload
        captured["config"] = config
        return {"ok": True}

    @contextmanager
    def fake_tracing(*, command: str, payload: dict[str, object], provider=None, output_dir=None):
        captured["trace_command"] = command
        captured["trace_payload"] = payload
        yield {"run_name": "trace-run", "tags": ["conversation"], "metadata": {"asset_count": 0}}

    monkeypatch.setattr(runner, "_read_input", fake_read_input)
    monkeypatch.setattr(runner, "run_conversation", fake_run_conversation)
    monkeypatch.setattr(runner, "open_langsmith_tracing", fake_tracing)

    exit_code = runner._conversation_command(Namespace(input=str(tmp_path / "request.json")))

    assert exit_code == 0
    assert captured["trace_command"] == "conversation"
    assert captured["config"]["run_name"] == "trace-run"
