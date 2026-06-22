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


def test_settings_defaults_to_real_generation_chain_when_env_not_loaded():
    settings = Settings(_env_file=None)

    assert settings.model_provider == "openai-compatible"
    assert settings.agent_runner == "langgraph"


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
        "AGENT_RUNNER",
        "OPENAI_COMPATIBLE_API_KEY",
        "OPENAI_COMPATIBLE_BASE_URL",
        "OPENAI_COMPATIBLE_MODEL",
        "LLM_PROVIDER",
        "LAN_AGENTS_SRC_PATH",
        "LANGSMITH_TRACING",
        "LANGSMITH_API_KEY",
        "LANGSMITH_PROJECT",
        "LANGSMITH_ENDPOINT",
    ]:
        assert f"{variable}=" in env_example


def test_env_example_defaults_to_real_generation_chain_without_committed_secrets():
    env_example = (REPO_ROOT / ".env.example").read_text(encoding="utf-8")

    assert "MODEL_PROVIDER=openai-compatible" in env_example
    assert "AGENT_RUNNER=langgraph" in env_example
    assert "LLM_PROVIDER=openai-compatible" in env_example
    assert "ASSET_IMAGE_PROVIDER=openai-compatible" in env_example
    assert "OPENAI_COMPATIBLE_API_KEY=\n" in env_example
    assert "OPENAI_IMAGE_API_KEY=\n" in env_example


def test_backend_dockerfile_installs_node_for_agent_runtime_validation():
    dockerfile = (REPO_ROOT / "backend" / "Dockerfile").read_text(encoding="utf-8")

    assert "nodejs" in dockerfile


def test_backend_requirements_include_pillow_for_uploaded_image_processing():
    requirements = (REPO_ROOT / "backend" / "requirements.txt").read_text(
        encoding="utf-8"
    )

    assert "pillow" in requirements.lower()


def test_backend_dockerfile_copies_examples_and_runs_seed_before_server_start():
    dockerfile = (REPO_ROOT / "backend" / "Dockerfile").read_text(encoding="utf-8")

    assert "COPY examples ./examples" in dockerfile
    assert "COPY scripts ./scripts" in dockerfile
    assert "python scripts/seed_backend.py" in dockerfile


def test_frontend_dockerfile_builds_static_bundle_and_serves_with_nginx():
    dockerfile = (REPO_ROOT / "frontend" / "Dockerfile").read_text(encoding="utf-8")

    assert "FROM public.ecr.aws/docker/library/node:22-alpine AS build" in dockerfile
    assert "RUN npm install" in dockerfile
    assert "RUN npm run build" in dockerfile
    assert "FROM public.ecr.aws/nginx/nginx:alpine" in dockerfile
    assert "COPY nginx.conf /etc/nginx/conf.d/default.conf" in dockerfile
    assert "COPY --from=build /app/dist /usr/share/nginx/html" in dockerfile


def test_frontend_nginx_config_handles_spa_and_api_proxy():
    nginx_config = (REPO_ROOT / "frontend" / "nginx.conf").read_text(encoding="utf-8")

    assert "location /api/" in nginx_config
    assert "proxy_pass http://backend:8000/api/" in nginx_config
    assert "try_files $uri $uri/ /index.html;" in nginx_config


def test_docker_compose_starts_frontend_by_default():
    compose = (REPO_ROOT / "docker-compose.yml").read_text(encoding="utf-8")

    assert 'profiles: ["docker-frontend"]' not in compose
    assert 'context: ./frontend' in compose
    assert '- "5173:80"' in compose
    assert "VITE_API_PROXY_TARGET" not in compose


def test_docker_compose_defaults_to_real_generation_chain():
    compose = (REPO_ROOT / "docker-compose.yml").read_text(encoding="utf-8")

    assert 'MODEL_PROVIDER: ${MODEL_PROVIDER:-openai-compatible}' in compose
    assert 'AGENT_RUNNER: ${AGENT_RUNNER:-langgraph}' in compose
    assert (
        'LLM_PROVIDER: ${LLM_PROVIDER:-${MODEL_PROVIDER:-openai-compatible}}'
        in compose
    )
    assert 'ASSET_IMAGE_PROVIDER: ${ASSET_IMAGE_PROVIDER:-openai-compatible}' in compose
