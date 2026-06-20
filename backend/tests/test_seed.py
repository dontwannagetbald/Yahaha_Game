from __future__ import annotations

import asyncio
import json
import uuid

import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.models import Base, Game, User
from app.seed import SEED_GAME_DEFINITIONS, seed_published_games


class FakeStorageService:
    def __init__(self) -> None:
        self.uploaded_objects: dict[str, bytes] = {}

    def build_published_object_key(
        self, *, game_id, version: str, relative_path: str
    ) -> str:
        return f"published/{game_id}/{version}/{relative_path}"

    def build_public_read_url(self, object_key: str) -> str:
        return f"http://localhost:9000/yahaha-game/{object_key}"

    def put_object(
        self,
        object_key: str,
        *,
        body: bytes,
        content_type: str,
    ) -> None:
        self.uploaded_objects[object_key] = body


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


def test_seed_games_creates_published_records_and_is_idempotent(session_factory):
    storage = FakeStorageService()

    async def run():
        async with session_factory() as session:
            first = await seed_published_games(session, storage)
            second = await seed_published_games(session, storage)

            assert len(first) >= 2
            assert [game.id for game in first] == [game.id for game in second]

            users = (await session.execute(select(User))).scalars().all()
            games = (await session.execute(select(Game).order_by(Game.created_at.asc()))).scalars().all()

            assert len(users) == 1
            assert len(games) == len(SEED_GAME_DEFINITIONS)

            for game in games:
                assert game.status == "published"
                assert game.cover_url
                assert game.title
                assert game.description
                assert game.tags
                assert game.published_at is not None
                assert game.manifest_url
                assert game.artifact_base_url
                assert game.play_count >= 0
                assert game.like_count >= 0

            expected_files_per_game = 5
            assert len(storage.uploaded_objects) == len(SEED_GAME_DEFINITIONS) * expected_files_per_game

    asyncio.run(run())


def test_seed_artifacts_are_public_and_match_manifest_contract(session_factory):
    storage = FakeStorageService()

    async def run():
        async with session_factory() as session:
            games = await seed_published_games(session, storage)

            for game in games:
                manifest_key = f"published/{game.id}/v1/manifest.json"
                entry_key = f"published/{game.id}/v1/index.html"
                style_key = f"published/{game.id}/v1/style.css"
                script_key = f"published/{game.id}/v1/game.js"
                cover_key = f"published/{game.id}/v1/assets/cover.svg"

                assert game.manifest_url == f"http://localhost:9000/yahaha-game/{manifest_key}"
                assert game.artifact_base_url == f"http://localhost:9000/yahaha-game/published/{game.id}/v1/"
                assert game.cover_url == f"http://localhost:9000/yahaha-game/{cover_key}"

                assert manifest_key in storage.uploaded_objects
                assert entry_key in storage.uploaded_objects
                assert style_key in storage.uploaded_objects
                assert script_key in storage.uploaded_objects
                assert cover_key in storage.uploaded_objects

                manifest = json.loads(storage.uploaded_objects[manifest_key].decode("utf-8"))
                assert manifest["entry"] == "index.html"
                assert manifest["styles"] == ["style.css"]
                assert manifest["scripts"] == ["game.js"]
                assert manifest["cover"] == "assets/cover.svg"
                assert manifest["runtime"] == "html5-iframe"
                assert manifest["title"] == game.title
                assert manifest["description"] == game.description

    asyncio.run(run())


def test_seed_games_ship_distinct_playable_bundles(session_factory):
    storage = FakeStorageService()

    async def run():
        async with session_factory() as session:
            games = await seed_published_games(session, storage)
            by_title = {game.title: game for game in games}

            sky_runner = by_title["Sky Runner"]
            pixel_raid = by_title["Pixel Raid"]

            sky_manifest = json.loads(
                storage.uploaded_objects[
                    f"published/{sky_runner.id}/v1/manifest.json"
                ].decode("utf-8")
            )
            pixel_manifest = json.loads(
                storage.uploaded_objects[
                    f"published/{pixel_raid.id}/v1/manifest.json"
                ].decode("utf-8")
            )

            sky_html = storage.uploaded_objects[
                f"published/{sky_runner.id}/v1/index.html"
            ].decode("utf-8")
            pixel_html = storage.uploaded_objects[
                f"published/{pixel_raid.id}/v1/index.html"
            ].decode("utf-8")

            sky_js = storage.uploaded_objects[
                f"published/{sky_runner.id}/v1/game.js"
            ].decode("utf-8")
            pixel_js = storage.uploaded_objects[
                f"published/{pixel_raid.id}/v1/game.js"
            ].decode("utf-8")

            assert sky_manifest["controls"] == [
                "ArrowLeft / ArrowRight to move",
                "Space to jump",
            ]
            assert pixel_manifest["controls"] == [
                "WASD to move",
                "Move cursor to aim",
            ]

            assert '<canvas id="game-canvas"' in sky_html
            assert '<canvas id="game-canvas"' in pixel_html
            assert "requestAnimationFrame" in sky_js
            assert "requestAnimationFrame" in pixel_js

            assert "coinsCollected" in sky_js
            assert "spawnObstacle" in sky_js
            assert "spawnEnemy" in pixel_js
            assert "player.hp" in pixel_js
            assert "<aside" not in sky_html
            assert "<aside" not in pixel_html
            assert "Controls" not in sky_html
            assert "Controls" not in pixel_html

    asyncio.run(run())
