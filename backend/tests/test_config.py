import pytest

from app.config import (
    ConfigurationError,
    REPO_ROOT,
    Settings,
    validate_required_settings,
)


def test_settings_uses_root_env_file_when_cwd_is_backend(monkeypatch):
    monkeypatch.chdir(REPO_ROOT / "backend")

    settings = Settings()

    assert settings.model_config["env_file"] == REPO_ROOT / ".env"


def test_missing_database_url_fails_configuration_validation():
    settings = Settings(database_url="", model_provider="mock")

    with pytest.raises(ConfigurationError, match="DATABASE_URL"):
        validate_required_settings(settings)


def test_mock_provider_allows_empty_openai_api_key():
    settings = Settings(
        database_url="postgresql+asyncpg://user:pass@db:5432/app",
        model_provider="mock",
        openai_compatible_api_key="",
    )

    validate_required_settings(settings)


def test_openai_compatible_provider_requires_api_key():
    settings = Settings(
        database_url="postgresql+asyncpg://user:pass@db:5432/app",
        model_provider="openai-compatible",
        openai_compatible_api_key="",
    )

    with pytest.raises(ConfigurationError, match="OPENAI_COMPATIBLE_API_KEY"):
        validate_required_settings(settings)


def test_default_cors_origins_cover_localhost_and_loopback():
    settings = Settings(
        database_url="postgresql+asyncpg://user:pass@db:5432/app",
        frontend_origin="http://localhost:5173",
        frontend_origins="",
    )

    assert settings.cors_allowed_origins == [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]


def test_env_example_covers_validated_settings():
    env_example = (REPO_ROOT / ".env.example").read_text(encoding="utf-8")

    for variable in [
        "DATABASE_URL",
        "MODEL_PROVIDER",
        "OPENAI_COMPATIBLE_API_KEY",
        "OPENAI_COMPATIBLE_BASE_URL",
        "OPENAI_COMPATIBLE_MODEL",
    ]:
        assert f"{variable}=" in env_example
