from agent.generation_graph.tools.provider_smoke import (
    GENERATION_PROVIDER_SMOKE_SCHEMA,
    build_generation_smoke_messages,
    run_provider_smoke,
)
from agent.providers import MockLLMProvider, ProviderConfig, ProviderError, provider_from_config


def test_generation_provider_reuses_shared_provider_config() -> None:
    config = ProviderConfig(provider="mock")

    provider = provider_from_config(config)

    assert isinstance(provider, MockLLMProvider)


def test_generation_graph_coding_provider_uses_coding_agent_model(monkeypatch) -> None:
    from agent.generation_graph import graph as graph_module
    from agent.generation_graph.state import GenerationState
    from agent.providers import OpenAICompatibleLLMProvider

    monkeypatch.setenv("LLM_PROVIDER", "openai-compatible")
    monkeypatch.setenv("OPENAI_COMPATIBLE_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_COMPATIBLE_BASE_URL", "https://llm.example/v1")
    monkeypatch.setenv("OPENAI_COMPATIBLE_MODEL", "general-model")
    monkeypatch.setenv("CODING_AGENT_MODEL", "gpt-5.5")

    provider = graph_module._coding_provider_from_env(GenerationState())

    assert isinstance(provider, OpenAICompatibleLLMProvider)
    assert provider._config.model == "gpt-5.5"


def test_generation_provider_smoke_uses_json_schema_and_safe_summary() -> None:
    provider = MockLLMProvider(
        response={
            "ok": True,
            "stage": "generation_provider_smoke",
            "summary": "ready",
        }
    )

    result = run_provider_smoke(provider=provider)

    assert result == {
        "ok": True,
        "stage": "generation_provider_smoke",
        "summary": "ready",
    }
    assert provider.calls[0]["response_schema"] == GENERATION_PROVIDER_SMOKE_SCHEMA
    assert provider.calls[0]["messages"] == build_generation_smoke_messages()


def test_generation_provider_smoke_returns_safe_failure_without_traceback() -> None:
    provider = MockLLMProvider(raises=ProviderError("LLM provider HTTP error: 429"))

    result = run_provider_smoke(provider=provider)

    assert result == {
        "ok": False,
        "stage": "generation_provider_smoke",
        "summary": "LLM provider rate limited: 429",
    }
    assert "Traceback" not in result["summary"]
    assert "http" not in result["summary"].lower()


def test_generation_provider_smoke_keeps_safe_provider_error_category() -> None:
    provider = MockLLMProvider(raises=ProviderError("LLM provider returned invalid JSON"))

    result = run_provider_smoke(provider=provider)

    assert result == {
        "ok": False,
        "stage": "generation_provider_smoke",
        "summary": "LLM provider returned invalid JSON",
    }


def test_generation_provider_smoke_keeps_debug_preview_when_enabled() -> None:
    provider = MockLLMProvider(
        raises=ProviderError("LLM provider returned invalid JSON preview: not-json")
    )

    result = run_provider_smoke(provider=provider)

    assert result == {
        "ok": False,
        "stage": "generation_provider_smoke",
        "summary": "LLM provider returned invalid JSON preview: not-json",
    }


def test_generation_provider_smoke_keeps_safe_json_structure_error() -> None:
    provider = MockLLMProvider(
        raises=ProviderError("LLM provider JSON response must be an object")
    )

    result = run_provider_smoke(provider=provider)

    assert result == {
        "ok": False,
        "stage": "generation_provider_smoke",
        "summary": "LLM provider JSON response must be an object",
    }
