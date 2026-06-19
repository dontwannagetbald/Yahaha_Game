from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db import get_session as app_get_session
from app.main import app
from app.models import Base, UploadedAsset


@pytest_asyncio.fixture()
async def session_factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        yield factory
    finally:
        await engine.dispose()


@pytest.fixture()
def client(session_factory):
    async def override_get_session():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[app_get_session] = override_get_session
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


@pytest.fixture()
def authenticated_client(client: TestClient) -> TestClient:
    response = client.post(
        "/api/auth/register",
        json={"email": "upload-user@example.com", "password": "password123"},
    )
    assert response.status_code == 201
    return client


@dataclass
class StubPresignedUrlResult:
    url: str
    expires_in: int


class StubStorageService:
    def build_upload_object_key(self, *, user_id, upload_id, filename: str) -> str:
        return f"uploads/{user_id}/{upload_id}/cover-final.png"

    def build_presigned_upload_url(
        self, object_key: str, *, expires_in: int = 900
    ) -> StubPresignedUrlResult:
        return StubPresignedUrlResult(
            url=f"http://minio.local/presigned/{object_key}",
            expires_in=expires_in,
        )


def test_presign_requires_login(client: TestClient):
    response = client.post(
        "/api/uploads/presign",
        json={
            "filename": "cover.png",
            "mime_type": "image/png",
            "size_bytes": 1024,
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "error": {
            "code": "unauthorized",
            "message": "Not authenticated",
        }
    }


def test_presign_success_returns_upload_contract(
    authenticated_client: TestClient, monkeypatch: pytest.MonkeyPatch
):
    import app.uploads as uploads_module

    app.dependency_overrides[uploads_module.get_storage_service] = (
        lambda: StubStorageService()
    )
    try:
        response = authenticated_client.post(
            "/api/uploads/presign",
            json={
                "filename": "Cover Final.png",
                "mime_type": "image/png",
                "size_bytes": 1024,
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert set(body.keys()) == {
            "upload_id",
            "object_key",
            "upload_url",
            "expires_in",
        }
        assert body["object_key"].startswith("uploads/")
        assert body["object_key"].endswith("/Cover-Final.png") is False
        assert body["upload_url"].startswith("http://minio.local/presigned/uploads/")
        assert body["expires_in"] == 900
    finally:
        app.dependency_overrides.pop(uploads_module.get_storage_service, None)


def test_presign_rejects_file_larger_than_20mb(authenticated_client: TestClient):
    response = authenticated_client.post(
        "/api/uploads/presign",
        json={
            "filename": "video.mov",
            "mime_type": "video/quicktime",
            "size_bytes": 20 * 1024 * 1024 + 1,
        },
    )

    assert response.status_code == 413
    assert response.json() == {
        "error": {
            "code": "file_too_large",
            "message": "File exceeds 20MB limit",
        }
    }


def test_complete_requires_login(client: TestClient):
    response = client.post(
        "/api/uploads/complete",
        json={
            "upload_id": "11111111-1111-1111-1111-111111111111",
            "object_key": "uploads/11111111-1111-1111-1111-111111111111/22222222-2222-2222-2222-222222222222/cover.png",
            "filename": "cover.png",
            "mime_type": "image/png",
            "size_bytes": 1024,
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "error": {
            "code": "unauthorized",
            "message": "Not authenticated",
        }
    }


def test_complete_persists_uploaded_asset(
    authenticated_client: TestClient, session_factory
):
    presign_response = authenticated_client.post(
        "/api/uploads/presign",
        json={
            "filename": "cover.png",
            "mime_type": "image/png",
            "size_bytes": 1024,
        },
    )
    assert presign_response.status_code == 200
    presign_body = presign_response.json()

    response = authenticated_client.post(
        "/api/uploads/complete",
        json={
            "upload_id": presign_body["upload_id"],
            "object_key": presign_body["object_key"],
            "filename": "cover.png",
            "mime_type": "image/png",
            "size_bytes": 1024,
        },
    )

    assert response.status_code == 200
    assert response.json()["filename"] == "cover.png"
    assert response.json()["mime_type"] == "image/png"
    assert response.json()["size_bytes"] == 1024
    assert response.json()["asset_id"]

    async def inspect() -> None:
        async with session_factory() as session:
            assets = (await session.execute(select(UploadedAsset))).scalars().all()
            assert len(assets) == 1
            assert assets[0].filename == "cover.png"
            assert assets[0].mime_type == "image/png"
            assert assets[0].size_bytes == 1024
            assert assets[0].object_key == presign_body["object_key"]
            assert assets[0].job_id is None
            assert assets[0].user_id is not None

    asyncio.run(inspect())
