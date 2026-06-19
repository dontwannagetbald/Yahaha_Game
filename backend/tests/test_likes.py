from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db import get_session as app_get_session
from app.main import app
from app.models import Base, Game, GameLike, User


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


def seed_game(session_factory):
    async def run():
        async with session_factory() as session:
            owner = User(email="owner@example.com", password_hash="hash")
            session.add(owner)
            await session.flush()
            game = Game(
                owner_id=owner.user_id,
                title="Like Me",
                description="published",
                cover_url="x",
                tags=["x"],
                status="published",
                like_count=0,
                play_count=0,
                published_at=datetime.now(timezone.utc),
            )
            draft = Game(
                owner_id=owner.user_id,
                title="Draft",
                description="draft",
                cover_url="x",
                tags=["x"],
                status="draft",
            )
            deleted = Game(
                owner_id=owner.user_id,
                title="Deleted",
                description="deleted",
                cover_url="x",
                tags=["x"],
                status="deleted",
            )
            session.add_all([game, draft, deleted])
            await session.commit()
            return str(game.id), str(draft.id), str(deleted.id)

    return asyncio.run(run())


def login(client: TestClient, email: str):
    response = client.post(
        "/api/auth/register",
        json={"email": email, "password": "password123"},
    )
    assert response.status_code == 201


def test_like_requires_login(client: TestClient, session_factory):
    game_id, _, _ = seed_game(session_factory)

    response = client.post(f"/api/games/{game_id}/like")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"


def test_first_like_and_idempotency(client: TestClient, session_factory):
    game_id, _, _ = seed_game(session_factory)
    login(client, "liker@example.com")

    first = client.post(f"/api/games/{game_id}/like")
    second = client.post(f"/api/games/{game_id}/like")

    assert first.status_code == 200
    assert first.json()["game_id"] == game_id
    assert first.json()["like_count"] == 1
    assert first.json()["liked_by_me"] is True
    assert second.status_code == 200
    assert second.json()["like_count"] == 1

    async def inspect():
        async with session_factory() as session:
            likes = (await session.execute(select(GameLike))).scalars().all()
            game = await session.get(Game, uuid.UUID(game_id))
            assert len(likes) == 1
            assert game.like_count == 1

    asyncio.run(inspect())


def test_multiple_users_and_invalid_status(client: TestClient, session_factory):
    game_id, draft_id, deleted_id = seed_game(session_factory)
    login(client, "first@example.com")
    client.post(f"/api/games/{game_id}/like")
    client.post("/api/auth/logout")
    login(client, "second@example.com")
    second = client.post(f"/api/games/{game_id}/like")
    draft = client.post(f"/api/games/{draft_id}/like")
    deleted = client.post(f"/api/games/{deleted_id}/like")

    assert second.status_code == 200
    assert second.json()["like_count"] == 2
    assert draft.status_code == 404
    assert deleted.status_code == 404
