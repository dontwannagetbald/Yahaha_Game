from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
import uuid

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db import get_session as app_get_session
from app.main import app
from app.models import AgentLog, Base, GenerationJob, UploadedAsset, User


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


def login(client: TestClient, email: str):
    response = client.post(
        "/api/auth/register",
        json={"email": email, "password": "password123"},
    )
    assert response.status_code == 201


def create_asset(client: TestClient) -> str:
    presign = client.post(
        "/api/uploads/presign",
        json={"filename": "asset.png", "mime_type": "image/png", "size_bytes": 1024},
    )
    body = presign.json()
    complete = client.post(
        "/api/uploads/complete",
        json={
            "upload_id": body["upload_id"],
            "object_key": body["object_key"],
            "filename": "asset.png",
            "mime_type": "image/png",
            "size_bytes": 1024,
        },
    )
    return complete.json()["asset_id"]


def test_create_requires_login(client: TestClient):
    response = client.post(
        "/api/jobs",
        json={"prompt": "make game", "asset_ids": [], "confirmation": {"title": "x"}},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"


def test_create_success_and_asset_rules(client: TestClient, session_factory):
    login(client, "owner@example.com")
    asset_id = create_asset(client)

    created = client.post(
        "/api/jobs",
        json={
            "prompt": "make game",
            "asset_ids": [asset_id],
            "confirmation": {"title": "My Game", "tags": ["runner"]},
        },
    )

    assert created.status_code == 201
    assert created.json()["status"] == "pending"
    assert created.json()["job_id"]
    assert created.json()["created_at"]

    too_many = client.post(
        "/api/jobs",
        json={
            "prompt": "too many",
            "asset_ids": [asset_id] * 6,
            "confirmation": {"title": "Overflow"},
        },
    )
    assert too_many.status_code == 400

    other_client = TestClient(app)
    try:
        app.dependency_overrides[app_get_session] = app.dependency_overrides[
            app_get_session
        ]
        login(other_client, "other@example.com")
        forbidden = other_client.post(
            "/api/jobs",
            json={
                "prompt": "steal",
                "asset_ids": [asset_id],
                "confirmation": {"title": "Steal"},
            },
        )
        assert forbidden.status_code == 403
    finally:
        other_client.close()

    async def inspect():
        async with session_factory() as session:
            jobs = (await session.execute(select(GenerationJob))).scalars().all()
            assets = (await session.execute(select(UploadedAsset))).scalars().all()
            assert len(jobs) == 1
            assert assets[0].job_id == jobs[0].id

    asyncio.run(inspect())


def test_list_detail_and_logs_permissions(client: TestClient, session_factory):
    login(client, "owner@example.com")
    first = client.post(
        "/api/jobs",
        json={"prompt": "first", "asset_ids": [], "confirmation": {"title": "First"}},
    )
    second = client.post(
        "/api/jobs",
        json={"prompt": "second", "asset_ids": [], "confirmation": {"title": "Second"}},
    )
    first_id = first.json()["job_id"]
    second_id = second.json()["job_id"]

    async def seed_logs():
        async with session_factory() as session:
            job = await session.get(GenerationJob, uuid.UUID(second_id))
            session.add_all(
                [
                    AgentLog(
                        job_id=job.id,
                        step="start",
                        level="info",
                        message="token=secret hidden",
                        created_at=datetime.now(timezone.utc) - timedelta(seconds=1),
                    ),
                    AgentLog(
                        job_id=job.id,
                        step="done",
                        level="info",
                        message="ok",
                        created_at=datetime.now(timezone.utc),
                    ),
                ]
            )
            await session.commit()

    asyncio.run(seed_logs())

    listed = client.get("/api/jobs")
    detail = client.get(f"/api/jobs/{second_id}")
    logs = client.get(f"/api/jobs/{second_id}/logs")

    assert listed.status_code == 200
    assert [job["job_id"] for job in listed.json()["jobs"]] == [second_id, first_id]
    assert detail.status_code == 200
    assert detail.json()["job_id"] == second_id
    assert logs.status_code == 200
    assert [log["step"] for log in logs.json()["logs"]] == ["start", "done"]
    assert "secret" not in str(logs.json())

    other_client = TestClient(app)
    try:
        app.dependency_overrides[app_get_session] = app.dependency_overrides[
            app_get_session
        ]
        login(other_client, "viewer@example.com")
        assert other_client.get(f"/api/jobs/{second_id}").status_code == 404
        assert other_client.get(f"/api/jobs/{second_id}/logs").status_code == 404
    finally:
        other_client.close()
