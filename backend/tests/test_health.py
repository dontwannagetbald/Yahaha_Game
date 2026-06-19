from fastapi.testclient import TestClient

from app.db import get_session
from app.main import app


def test_health_returns_ok():
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_allows_local_frontend_origin():
    client = TestClient(app)

    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_http_errors_use_uniform_error_response():
    client = TestClient(app)

    response = client.get("/missing")

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "not_found",
            "message": "Not Found",
        }
    }


def test_ready_returns_ok_when_database_query_succeeds():
    class SessionStub:
        async def execute(self, statement):
            return None

    async def override_get_session():
        yield SessionStub()

    app.dependency_overrides[get_session] = override_get_session
    try:
        client = TestClient(app)

        response = client.get("/ready")

        assert response.status_code == 200
        assert response.json() == {"status": "ok", "database": "ok"}
    finally:
        app.dependency_overrides.clear()


def test_ready_returns_clear_error_when_database_query_fails():
    class SessionStub:
        async def execute(self, statement):
            raise RuntimeError("database unavailable")

    async def override_get_session():
        yield SessionStub()

    app.dependency_overrides[get_session] = override_get_session
    try:
        client = TestClient(app, raise_server_exceptions=False)

        response = client.get("/ready")

        assert response.status_code == 503
        assert response.json() == {
            "error": {
                "code": "service_unavailable",
                "message": "Database connection failed",
            }
        }
    finally:
        app.dependency_overrides.clear()
