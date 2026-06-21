from agent.providers import ProviderConfig
from agent.providers.preflight import (
    RECOMMENDED_CONVERSATION_MODEL,
    provider_preflight_summary,
)


def test_provider_preflight_redacts_secret_values() -> None:
    config = ProviderConfig(
        provider="openai-compatible",
        api_key="sk-secret",
        base_url="https://api.openai.com/v1",
        model="gpt-5.4-mini",
        timeout_seconds=30,
    )

    summary = provider_preflight_summary(config)

    assert summary == {
        "provider": "openai-compatible",
        "api_key": "SET",
        "base_url": "SET",
        "model": "gpt-5.4-mini",
        "timeout_seconds": 30,
        "recommended_conversation_model": RECOMMENDED_CONVERSATION_MODEL,
    }
    assert "sk-secret" not in str(summary)
    assert "https://api.openai.com/v1" not in str(summary)


def test_provider_preflight_marks_missing_values() -> None:
    summary = provider_preflight_summary(ProviderConfig(provider="mock"))

    assert summary["provider"] == "mock"
    assert summary["api_key"] == "UNSET"
    assert summary["base_url"] == "UNSET"
    assert summary["model"] == "UNSET"
    assert summary["recommended_conversation_model"] == "gpt-5.4-mini"
