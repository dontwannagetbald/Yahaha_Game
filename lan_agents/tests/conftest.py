import pytest


@pytest.fixture(autouse=True)
def force_mock_llm_provider(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("ASSET_IMAGE_PROVIDER", "mock")
    monkeypatch.delenv("OPENAI_COMPATIBLE_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_COMPATIBLE_BASE_URL", raising=False)
    monkeypatch.delenv("OPENAI_COMPATIBLE_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_IMAGE_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_IMAGE_BASE_URL", raising=False)
    monkeypatch.delenv("OPENAI_IMAGE_MODEL", raising=False)


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"
