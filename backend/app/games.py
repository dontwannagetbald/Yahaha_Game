from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user, get_optional_current_user
from app.db import get_session
from app.models import Game, GameLike, User


router = APIRouter(prefix="/api/games", tags=["games"])


def _serialize_game_card(
    game: Game, author: User, liked_by_me: bool = False
) -> dict[str, object]:
    return {
        "id": str(game.id),
        "title": game.title,
        "description": game.description,
        "cover_url": game.cover_url,
        "author": {"display_name": author.display_name or author.email or "Unknown"},
        "tags": game.tags,
        "published_at": game.published_at.isoformat() if game.published_at else None,
        "play_count": game.play_count,
        "like_count": game.like_count,
        "liked_by_me": liked_by_me,
    }


def _serialize_game_detail(
    game: Game, author: User, liked_by_me: bool = False
) -> dict[str, object]:
    payload = _serialize_game_card(game, author, liked_by_me)
    payload.update(
        {
            "status": game.status,
            "manifest_url": game.manifest_url,
            "artifact_base_url": game.artifact_base_url,
        }
    )
    return payload


@router.get("")
async def list_games(
    request: Request,
    sort: str = Query("latest"),
    q: str = Query(""),
    tag: str = Query(""),
    db: Annotated[AsyncSession, Depends(get_session)] = None,
) -> dict[str, object]:
    if sort not in {"latest", "play_count", "like_count"}:
        raise HTTPException(status_code=400, detail="Unsupported sort value")

    current_user = await get_optional_current_user(request, db)

    rows = (
        await db.execute(
            select(Game, User)
            .join(User, User.user_id == Game.owner_id)
            .where(Game.status == "published")
        )
    ).all()

    normalized_q = q.strip().lower()
    normalized_tag = tag.strip().lower()
    filtered: list[tuple[Game, User]] = []
    for game, author in rows:
        if normalized_q:
            haystack = " ".join(
                [
                    game.title or "",
                    game.description or "",
                    author.display_name or "",
                ]
            ).lower()
            if normalized_q not in haystack:
                continue
        if normalized_tag and normalized_tag not in {
            (item or "").lower() for item in (game.tags or [])
        }:
            continue
        filtered.append((game, author))

    if sort == "latest":
        filtered.sort(
            key=lambda item: (
                item[0].published_at or item[0].created_at,
                item[0].created_at,
            ),
            reverse=True,
        )
    elif sort == "play_count":
        filtered.sort(
            key=lambda item: (
                item[0].play_count,
                item[0].published_at or item[0].created_at,
            ),
            reverse=True,
        )
    else:
        filtered.sort(
            key=lambda item: (
                item[0].like_count,
                item[0].published_at or item[0].created_at,
            ),
            reverse=True,
        )

    liked_ids: set[uuid.UUID] = set()
    if current_user:
        likes = (
            await db.execute(
                select(GameLike.game_id).where(GameLike.user_id == current_user.user_id)
            )
        ).scalars()
        liked_ids = set(likes)

    games = [
        _serialize_game_card(game, author, game.id in liked_ids)
        for game, author in filtered
    ]
    return {"games": games, "total": len(games)}


@router.get("/{game_id}")
async def get_game(
    game_id: uuid.UUID,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, object]:
    current_user = await get_optional_current_user(request, db)
    row = (
        await db.execute(
            select(Game, User)
            .join(User, User.user_id == Game.owner_id)
            .where(Game.id == game_id)
        )
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Game not found")

    game, author = row
    if game.status == "deleted":
        raise HTTPException(status_code=404, detail="Game not found")
    if game.status != "published":
        if not current_user or current_user.user_id != game.owner_id:
            raise HTTPException(status_code=404, detail="Game not found")

    liked_by_me = False
    if current_user:
        liked_by_me = (
            await db.execute(
                select(GameLike).where(
                    GameLike.game_id == game.id,
                    GameLike.user_id == current_user.user_id,
                )
            )
        ).scalar_one_or_none() is not None

    return _serialize_game_detail(game, author, liked_by_me)


@router.post("/{game_id}/like")
async def like_game(
    game_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, object]:
    game = await db.get(Game, game_id)
    if game is None or game.status != "published":
        raise HTTPException(status_code=404, detail="Game not found")

    existing = (
        await db.execute(
            select(GameLike).where(
                GameLike.game_id == game.id, GameLike.user_id == user.user_id
            )
        )
    ).scalar_one_or_none()
    if existing is None:
        db.add(GameLike(game_id=game.id, user_id=user.user_id))
        game.like_count += 1
        await db.commit()

    return {
        "game_id": str(game.id),
        "like_count": game.like_count,
        "liked_by_me": True,
    }
