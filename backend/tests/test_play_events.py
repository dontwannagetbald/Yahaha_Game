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
from app.models import Base, Game, PlayEvent, User


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


def seed_published_game(session_factory):
    async def run():
        async with session_factory() as session:
            owner = User(email="owner@example.com", password_hash="hash")
            session.add(owner)
            await session.flush()
            game = Game(
                owner_id=owner.user_id,
                title="Playable",
                description="published",
                cover_url="x",
                tags=["x"],
                status="published",
                published_at=datetime.now(timezone.utc),
            )
            session.add(game)
            await session.commit()
            return str(game.id)

    return asyncio.run(run())


def login(client: TestClient, email: str):
    response = client.post(
        "/api/auth/register",
        json={"email": email, "password": "password123"},
    )
    assert response.status_code == 201


def test_guest_view_event(client: TestClient, session_factory):
    game_id = seed_published_game(session_factory)

    response = client.post(
        "/api/play-events",
        json={"game_id": game_id, "event_type": "view", "metadata": {"stage": "meta"}},
    )

    assert response.status_code == 200

    async def inspect():
        async with session_factory() as session:
            events = (await session.execute(select(PlayEvent))).scalars().all()
            assert len(events) == 1
            assert events[0].user_id is None

    asyncio.run(inspect())


def test_authenticated_events_and_invalid_type(client: TestClient, session_factory):
    game_id = seed_published_game(session_factory)
    login(client, "player@example.com")

    manifest = client.post(
        "/api/play-events",
        json={"game_id": game_id, "event_type": "manifest_loaded"},
    )
    started = client.post(
        "/api/play-events",
        json={"game_id": game_id, "event_type": "started"},
    )
    invalid = client.post(
        "/api/play-events",
        json={"game_id": game_id, "event_type": "oops"},
    )

    assert manifest.status_code == 200
    assert started.status_code == 200
    assert invalid.status_code == 422


def test_play_count_counts_view_only(client: TestClient, session_factory):
    game_id = seed_published_game(session_factory)

    client.post("/api/play-events", json={"game_id": game_id, "event_type": "view"})
    client.post("/api/play-events", json={"game_id": game_id, "event_type": "started"})
    client.post("/api/play-events", json={"game_id": game_id, "event_type": "failed"})

    async def inspect():
        async with session_factory() as session:
            game = await session.get(Game, uuid.UUID(game_id))
            assert game.play_count == 1

    asyncio.run(inspect())


def test_metadata_is_sanitized(client: TestClient, session_factory):
    game_id = seed_published_game(session_factory)

    client.post(
        "/api/play-events",
        json={
            "game_id": game_id,
            "event_type": "failed",
            "metadata": {
                "stage": "bundle",
                "token": "secret-token",
                "password": "secret",
                "asset_url": "http://minio.local/file?X-Amz-Signature=abc123",
            },
        },
    )

    async def inspect():
        async with session_factory() as session:
            event = (await session.execute(select(PlayEvent))).scalars().one()
            metadata = event.metadata_ or {}
            assert "token" not in metadata
            assert "password" not in metadata
            assert "X-Amz-Signature" not in str(metadata)

    asyncio.run(inspect())
