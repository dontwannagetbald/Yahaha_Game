from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db import get_session as app_get_session
from app.main import app
from app.models import Base, Game, User
from app.security import hash_password


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


def login(client: TestClient, email: str) -> None:
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": "password123"},
    )
    assert response.status_code == 200


def seed_publish_fixture(session_factory) -> dict[str, str]:
    owner_id = uuid.uuid4()
    other_id = uuid.uuid4()
    draft_id = uuid.uuid4()
    published_id = uuid.uuid4()

    async def run() -> None:
        async with session_factory() as session:
            owner = User(
                user_id=owner_id,
                email="owner@example.com",
                password_hash=hash_password("password123"),
                display_name="Owner One",
            )
            other = User(
                user_id=other_id,
                email="other@example.com",
                password_hash=hash_password("password123"),
                display_name="Other Two",
            )
            draft = Game(
                id=draft_id,
                owner_id=owner_id,
                title="Draft Cat Runner",
                description="A private draft game",
                cover_url="http://localhost:9000/yahaha-game/drafts/owner/job/v1/assets/cover.png",
                tags=["runner", "cat"],
                status="draft",
                manifest_url="http://localhost:9000/yahaha-game/drafts/owner/job/v1/manifest.json?X-Amz-Signature=secret",
                artifact_base_url="http://localhost:9000/yahaha-game/drafts/owner/job/v1/",
                created_at=datetime.now(timezone.utc),
            )
            published = Game(
                id=published_id,
                owner_id=owner_id,
                title="Already Published",
                description="Public game",
                cover_url="http://localhost:9000/yahaha-game/published/already/v1/assets/cover.png",
                tags=["public"],
                status="published",
                manifest_url="http://localhost:9000/yahaha-game/published/already/v1/manifest.json",
                artifact_base_url="http://localhost:9000/yahaha-game/published/already/v1/",
                published_at=datetime.now(timezone.utc),
            )
            session.add_all([owner, other, draft, published])
            await session.commit()

    asyncio.run(run())
    return {
        "draft_id": str(draft_id),
        "published_id": str(published_id),
    }


def test_publish_permissions(client: TestClient, session_factory):
    ids = seed_publish_fixture(session_factory)

    guest = client.post(f"/api/games/{ids['draft_id']}/publish")
    assert guest.status_code == 401

    login(client, "other@example.com")
    other = client.post(f"/api/games/{ids['draft_id']}/publish")
    assert other.status_code == 404

    client.post("/api/auth/logout")
    login(client, "owner@example.com")
    owner = client.post(f"/api/games/{ids['draft_id']}/publish")
    repeat = client.post(f"/api/games/{ids['draft_id']}/publish")
    already_published = client.post(f"/api/games/{ids['published_id']}/publish")

    assert owner.status_code == 200
    assert owner.json()["status"] == "published"
    assert repeat.status_code == 409
    assert already_published.status_code == 409


def test_artifact_publish_rewrites_to_public_published_prefix(
    client: TestClient, session_factory
):
    ids = seed_publish_fixture(session_factory)
    login(client, "owner@example.com")

    response = client.post(f"/api/games/{ids['draft_id']}/publish")

    assert response.status_code == 200
    body = response.json()
    assert body["manifest_url"].endswith(
        f"/published/{ids['draft_id']}/v1/manifest.json"
    )
    assert body["artifact_base_url"].endswith(f"/published/{ids['draft_id']}/v1/")
    assert "X-Amz-Signature" not in body["manifest_url"]
    assert "/uploads/" not in body["manifest_url"]
    assert "/drafts/" not in body["artifact_base_url"]


def test_published_visible_and_no_meta_edit_endpoint(
    client: TestClient, session_factory
):
    ids = seed_publish_fixture(session_factory)
    login(client, "owner@example.com")

    published = client.post(f"/api/games/{ids['draft_id']}/publish")
    listed = client.get("/api/games")
    patched = client.patch(
        f"/api/games/{ids['draft_id']}",
        json={"title": "Edited after publish"},
    )

    assert published.status_code == 200
    assert published.json()["published_at"] is not None
    assert ids["draft_id"] in {game["id"] for game in listed.json()["games"]}
    assert patched.status_code == 405
