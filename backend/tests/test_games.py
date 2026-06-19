from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import select
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


def seed_games(session_factory):
    owner_id = uuid.uuid4()
    other_owner_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    async def run():
        async with session_factory() as session:
            owner = User(
                user_id=owner_id,
                email="owner@example.com",
                password_hash=hash_password("password123"),
                display_name="Owner One",
            )
            other = User(
                user_id=other_owner_id,
                email="other@example.com",
                password_hash=hash_password("password123"),
                display_name="Other Two",
            )
            session.add_all([owner, other])

            published_latest = Game(
                owner_id=owner_id,
                title="Latest Runner",
                description="A fast game",
                cover_url="https://example.com/latest.png",
                tags=["runner", "arcade"],
                status="published",
                manifest_url="https://example.com/latest-manifest.json",
                artifact_base_url="https://example.com/latest/",
                play_count=5,
                like_count=2,
                published_at=now,
                created_at=now,
            )
            published_popular = Game(
                owner_id=other_owner_id,
                title="Popular Quest",
                description="Adventure with loops",
                cover_url="https://example.com/popular.png",
                tags=["adventure", "quest"],
                status="published",
                manifest_url="https://example.com/popular-manifest.json",
                artifact_base_url="https://example.com/popular/",
                play_count=99,
                like_count=42,
                published_at=now - timedelta(days=1),
                created_at=now - timedelta(days=1),
            )
            draft_game = Game(
                owner_id=owner_id,
                title="Draft Secret",
                description="Hidden build",
                cover_url="https://example.com/draft.png",
                tags=["draft"],
                status="draft",
                manifest_url="https://example.com/draft-manifest.json",
                artifact_base_url="https://example.com/draft/",
                created_at=now - timedelta(days=2),
            )
            deleted_game = Game(
                owner_id=other_owner_id,
                title="Deleted Ghost",
                description="Should not be visible",
                cover_url="https://example.com/deleted.png",
                tags=["ghost"],
                status="deleted",
                created_at=now - timedelta(days=3),
            )
            session.add_all(
                [published_latest, published_popular, draft_game, deleted_game]
            )
            await session.commit()
            return {
                "owner_id": str(owner_id),
                "other_owner_id": str(other_owner_id),
                "published_latest": str(published_latest.id),
                "published_popular": str(published_popular.id),
                "draft_game": str(draft_game.id),
                "deleted_game": str(deleted_game.id),
            }

    return asyncio.run(run())


def login(client: TestClient, email: str) -> None:
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": "password123"},
    )
    assert response.status_code == 200


def register(client: TestClient, email: str) -> None:
    response = client.post(
        "/api/auth/register",
        json={"email": email, "password": "password123"},
    )
    assert response.status_code == 201


def test_list_published_games_only(client: TestClient, session_factory):
    ids = seed_games(session_factory)

    response = client.get("/api/games")

    assert response.status_code == 200
    body = response.json()
    returned_ids = {game["id"] for game in body["games"]}
    assert returned_ids == {ids["published_latest"], ids["published_popular"]}
    assert body["total"] == 2
    assert {"title", "description", "cover_url", "tags", "published_at"}.issubset(
        body["games"][0].keys()
    )


def test_games_sorting_and_filters(client: TestClient, session_factory):
    seed_games(session_factory)

    latest = client.get("/api/games", params={"sort": "latest"})
    play_count = client.get("/api/games", params={"sort": "play_count"})
    like_count = client.get("/api/games", params={"sort": "like_count"})
    search = client.get("/api/games", params={"q": "quest"})
    tag = client.get("/api/games", params={"tag": "runner"})
    invalid = client.get("/api/games", params={"sort": "weird"})

    assert latest.status_code == 200
    assert latest.json()["games"][0]["title"] == "Latest Runner"
    assert play_count.json()["games"][0]["title"] == "Popular Quest"
    assert like_count.json()["games"][0]["title"] == "Popular Quest"
    assert [game["title"] for game in search.json()["games"]] == ["Popular Quest"]
    assert [game["title"] for game in tag.json()["games"]] == ["Latest Runner"]
    assert invalid.status_code == 400


def test_game_meta_permissions(client: TestClient, session_factory):
    ids = seed_games(session_factory)

    published = client.get(f"/api/games/{ids['published_latest']}")
    guest_draft = client.get(f"/api/games/{ids['draft_game']}")

    owner_client = TestClient(app)
    try:
        login(owner_client, "owner@example.com")
        owner_draft = owner_client.get(f"/api/games/{ids['draft_game']}")
    finally:
        owner_client.close()

    other_client = TestClient(app)
    try:
        register(other_client, "viewer@example.com")
        other_draft = other_client.get(f"/api/games/{ids['draft_game']}")
    finally:
        other_client.close()

    assert published.status_code == 200
    assert {"manifest_url", "artifact_base_url", "title", "description"}.issubset(
        published.json().keys()
    )
    assert guest_draft.status_code == 404
    assert owner_draft.status_code == 200
    assert owner_draft.json()["status"] == "draft"
    assert other_draft.status_code == 404
