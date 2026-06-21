from __future__ import annotations

import json
import mimetypes
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Game, User


SEED_AUTHOR_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")


@dataclass(frozen=True)
class SeedGameDefinition:
    game_id: uuid.UUID
    bundle_id: str
    tags: list[str]
    play_count: int
    like_count: int
    published_days_ago: int


SEED_GAME_DEFINITIONS: Sequence[SeedGameDefinition] = (
    SeedGameDefinition(
        game_id=uuid.UUID("0274de1c-54b5-4e22-8930-71979217717d"),
        bundle_id="0274de1c-54b5-4e22-8930-71979217717d",
        tags=["解谜", "冒险"],
        play_count=19,
        like_count=0,
        published_days_ago=0,
    ),
    SeedGameDefinition(
        game_id=uuid.UUID("0b7be5ff-bf91-465d-87bb-e3aa8a916606"),
        bundle_id="0b7be5ff-bf91-465d-87bb-e3aa8a916606",
        tags=["冒险", "动作"],
        play_count=9,
        like_count=1,
        published_days_ago=0,
    ),
    SeedGameDefinition(
        game_id=uuid.UUID("4b258dae-ed4d-4653-95f1-0c20ca80893e"),
        bundle_id="4b258dae-ed4d-4653-95f1-0c20ca80893e",
        tags=["休闲"],
        play_count=13,
        like_count=1,
        published_days_ago=1,
    ),
)


def _seed_author_defaults() -> dict[str, Any]:
    return {
        "user_id": SEED_AUTHOR_ID,
        "email": "zihanqiu21@example.com",
        "display_name": "zihanqiu21",
        "password_hash": None,
    }


def _examples_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "examples"
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError("examples directory not found")


def _bundle_root(definition: SeedGameDefinition) -> Path:
    bundle_root = _examples_root() / definition.bundle_id / "v1"
    if not bundle_root.is_dir():
        raise FileNotFoundError(f"Example bundle is missing: {bundle_root}")
    return bundle_root


def _load_example_bundle(
    definition: SeedGameDefinition,
) -> tuple[dict[str, Any], dict[str, tuple[bytes, str]]]:
    bundle_root = _bundle_root(definition)
    manifest_path = bundle_root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    relative_paths = ["manifest.json", manifest["entry"]]
    relative_paths.extend(manifest.get("styles") or [])
    relative_paths.extend(manifest.get("scripts") or [])
    relative_paths.extend(manifest.get("assets") or [])
    cover_path = str(manifest.get("cover") or "").strip()
    if cover_path:
        relative_paths.append(cover_path)

    files: dict[str, tuple[bytes, str]] = {}
    for relative_path in dict.fromkeys(relative_paths):
        file_path = bundle_root / relative_path
        if not file_path.is_file():
            raise FileNotFoundError(f"Bundle file is missing: {file_path}")
        files[str(relative_path)] = (
            file_path.read_bytes(),
            _content_type_for_path(str(relative_path)),
        )

    return manifest, files


def _content_type_for_path(relative_path: str) -> str:
    explicit_map = {
        ".css": "text/css; charset=utf-8",
        ".html": "text/html; charset=utf-8",
        ".js": "application/javascript; charset=utf-8",
        ".json": "application/json",
    }
    suffix = Path(relative_path).suffix.lower()
    if suffix in explicit_map:
        return explicit_map[suffix]
    guessed_type, _ = mimetypes.guess_type(relative_path)
    return guessed_type or "application/octet-stream"


async def seed_published_games(session: AsyncSession, storage) -> list[Game]:
    author = await session.get(User, SEED_AUTHOR_ID)
    if author is None:
        author = User(**_seed_author_defaults())
        session.add(author)
        await session.flush()

    now = datetime.now(timezone.utc)

    for definition in SEED_GAME_DEFINITIONS:
        manifest, bundle_files = _load_example_bundle(definition)
        version = "v1"
        manifest_key = storage.build_published_object_key(
            game_id=definition.game_id,
            version=version,
            relative_path="manifest.json",
        )
        entry_key = storage.build_published_object_key(
            game_id=definition.game_id,
            version=version,
            relative_path=str(manifest["entry"]),
        )
        cover_relative_path = str(manifest["cover"])
        cover_key = storage.build_published_object_key(
            game_id=definition.game_id,
            version=version,
            relative_path=cover_relative_path,
        )
        artifact_base_url = (
            storage.build_public_read_url(entry_key).rsplit("/", 1)[0] + "/"
        )

        game = await session.get(Game, definition.game_id)
        if game is None:
            game = Game(
                id=definition.game_id,
                owner_id=author.user_id,
                title=str(manifest["title"]),
                description=str(manifest["description"]),
                cover_url=storage.build_public_read_url(cover_key),
                tags=definition.tags,
                status="published",
                manifest_url=storage.build_public_read_url(manifest_key),
                artifact_base_url=artifact_base_url,
                play_count=definition.play_count,
                like_count=definition.like_count,
                published_at=now - timedelta(days=definition.published_days_ago),
            )
            session.add(game)
        else:
            game.owner_id = author.user_id
            game.title = str(manifest["title"])
            game.description = str(manifest["description"])
            game.cover_url = storage.build_public_read_url(cover_key)
            game.tags = definition.tags
            game.status = "published"
            game.manifest_url = storage.build_public_read_url(manifest_key)
            game.artifact_base_url = artifact_base_url
            game.play_count = definition.play_count
            game.like_count = definition.like_count
            game.published_at = now - timedelta(days=definition.published_days_ago)

        for relative_path, (body, content_type) in bundle_files.items():
            object_key = storage.build_published_object_key(
                game_id=definition.game_id,
                version=version,
                relative_path=relative_path,
            )
            storage.put_object(object_key, body=body, content_type=content_type)

    await session.commit()

    result = (
        await session.execute(
            select(Game)
            .where(
                Game.id.in_([definition.game_id for definition in SEED_GAME_DEFINITIONS])
            )
            .order_by(Game.created_at.asc())
        )
    ).scalars().all()
    return result
