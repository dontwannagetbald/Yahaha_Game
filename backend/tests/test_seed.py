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

            assert len(first) == 3
            assert [game.id for game in first] == [game.id for game in second]

            users = (await session.execute(select(User))).scalars().all()
            games = (await session.execute(select(Game).order_by(Game.created_at.asc()))).scalars().all()

            assert len(users) == 1
            assert len(games) == len(SEED_GAME_DEFINITIONS)
            assert [game.title for game in games] == [
                "被误解的女巫：符文真相",
                "哈利的魔法追击",
                "精灵小兽",
            ]

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
                cover_key = f"published/{game.id}/v1/assets/cover.png"

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
                assert manifest["cover"] == "assets/cover.png"
                assert manifest["runtime"] == "html5-iframe"
                assert manifest["title"] == game.title
                assert manifest["description"] == game.description

    asyncio.run(run())


def test_seed_games_use_example_bundles_from_repository(session_factory):
    storage = FakeStorageService()

    async def run():
        async with session_factory() as session:
            games = await seed_published_games(session, storage)
            by_title = {game.title: game for game in games}

            witch = by_title["被误解的女巫：符文真相"]
            harry = by_title["哈利的魔法追击"]
            elf = by_title["精灵小兽"]

            witch_manifest = json.loads(
                storage.uploaded_objects[
                    f"published/{witch.id}/v1/manifest.json"
                ].decode("utf-8")
            )
            harry_manifest = json.loads(
                storage.uploaded_objects[
                    f"published/{harry.id}/v1/manifest.json"
                ].decode("utf-8")
            )
            elf_manifest = json.loads(
                storage.uploaded_objects[
                    f"published/{elf.id}/v1/manifest.json"
                ].decode("utf-8")
            )

            witch_html = storage.uploaded_objects[
                f"published/{witch.id}/v1/index.html"
            ].decode("utf-8")
            harry_html = storage.uploaded_objects[
                f"published/{harry.id}/v1/index.html"
            ].decode("utf-8")
            elf_html = storage.uploaded_objects[
                f"published/{elf.id}/v1/index.html"
            ].decode("utf-8")

            witch_js = storage.uploaded_objects[
                f"published/{witch.id}/v1/game.js"
            ].decode("utf-8")
            harry_js = storage.uploaded_objects[
                f"published/{harry.id}/v1/game.js"
            ].decode("utf-8")
            elf_js = storage.uploaded_objects[
                f"published/{elf.id}/v1/game.js"
            ].decode("utf-8")

            assert witch_manifest["title"] == "被误解的女巫：符文真相"
            assert harry_manifest["title"] == "哈利的魔法追击"
            assert elf_manifest["title"] == "精灵小兽"

            assert witch_manifest["controls"] == [
                "鼠标点击/拖拽或键盘输入符文；与机关进行交互确认。"
            ]
            assert harry_manifest["controls"] == [
                "方向键或WASD移动；Shift冲刺；无复杂技能栏。"
            ]
            assert elf_manifest["controls"] == ["点击地面移动；接触收集目标；无需复杂按键。"]

            assert "女巫" in witch_html
            assert "哈利" in harry_html
            assert "精灵小兽" in elf_html
            assert "requestAnimationFrame" in witch_js
            assert "requestAnimationFrame" in harry_js
            assert "requestAnimationFrame" in elf_js

            assert "符文" in witch_js
            assert "伏地魔" in harry_js
            assert "图鉴" in elf_js

    asyncio.run(run())
