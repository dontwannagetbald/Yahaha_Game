from pathlib import Path

from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


REPO_ROOT = Path(__file__).resolve().parents[2]
ROOT_ENV_FILE = REPO_ROOT / ".env"


class ConfigurationError(RuntimeError):
    pass


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = ""
    frontend_origin: str = "http://localhost:5173"
    frontend_origins: str = ""

    session_secret: str = "change-me-local-session-secret"
    session_cookie_name: str = "yahaha_session"
    session_cookie_secure: bool = False
    session_cookie_samesite: str = "lax"
    session_ttl_seconds: int = 604800
    oauth_state_cookie_name: str = "yahaha_oauth_state"

    minio_endpoint: str = "http://minio:9000"
    minio_public_endpoint: str = "http://localhost:9000"
    minio_access_key: str = "change-me-local"
    minio_secret_key: str = "change-me-local"
    minio_bucket: str = "yahaha-game"
    minio_region: str = "us-east-1"
    minio_use_ssl: bool = False

    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/auth/oauth/google/callback"

    github_client_id: str = ""
    github_client_secret: str = ""
    github_redirect_uri: str = "http://localhost:8000/api/auth/oauth/github/callback"

    model_provider: str = "mock"
    mock_provider_enabled: bool = True
    openai_compatible_base_url: str = "https://api.example.com/v1"
    openai_compatible_api_key: str = ""
    openai_compatible_model: str = "example-model"
    openai_compatible_timeout_seconds: int = 120

    @property
    def cors_allowed_origins(self) -> list[str]:
        raw_origins = self.frontend_origins.strip()
        if raw_origins:
            origins = [
                origin.strip().rstrip("/")
                for origin in raw_origins.split(",")
                if origin.strip()
            ]
        else:
            origins = [
                self.frontend_origin.rstrip("/"),
                "http://127.0.0.1:5173",
            ]

        deduped: list[str] = []
        for origin in origins:
            if origin not in deduped:
                deduped.append(origin)
        return deduped


def validate_required_settings(current_settings: Settings) -> None:
    missing: list[str] = []

    if not current_settings.database_url:
        missing.append("DATABASE_URL")

    provider = current_settings.model_provider.lower()
    if provider == "openai-compatible":
        if not current_settings.openai_compatible_api_key:
            missing.append("OPENAI_COMPATIBLE_API_KEY")
        if not current_settings.openai_compatible_base_url:
            missing.append("OPENAI_COMPATIBLE_BASE_URL")
        if not current_settings.openai_compatible_model:
            missing.append("OPENAI_COMPATIBLE_MODEL")
    elif provider == "mock":
        if not current_settings.mock_provider_enabled:
            missing.append("MOCK_PROVIDER_ENABLED")
    else:
        raise ConfigurationError(
            "MODEL_PROVIDER must be either 'mock' or 'openai-compatible'"
        )

    if missing:
        joined = ", ".join(missing)
        raise ConfigurationError(f"Missing required configuration: {joined}")


def load_settings() -> Settings:
    try:
        current_settings = Settings()
        validate_required_settings(current_settings)
        return current_settings
    except ValidationError as exc:
        raise ConfigurationError(f"Invalid configuration: {exc}") from exc


settings = load_settings()
