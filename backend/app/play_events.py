from __future__ import annotations

import re
import uuid
from typing import Annotated, Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_optional_current_user
from app.db import get_session
from app.models import Game, PlayEvent


router = APIRouter(prefix="/api/play-events", tags=["play-events"])

ALLOWED_EVENT_TYPES = {
    "view",
    "manifest_loaded",
    "started",
    "failed",
    "timeout",
    "exited",
}
SENSITIVE_KEY_PATTERN = re.compile(r"(secret|token|password|code)", re.IGNORECASE)


class PlayEventRequest(BaseModel):
    game_id: uuid.UUID
    event_type: str
    metadata: Optional[Dict[str, Any]] = None


def _sanitize_metadata(value: Any) -> Any:
    if isinstance(value, dict):
        cleaned: dict[str, Any] = {}
        for key, item in value.items():
            if SENSITIVE_KEY_PATTERN.search(key):
                continue
            sanitized_item = _sanitize_metadata(item)
            if sanitized_item is not None:
                cleaned[key] = sanitized_item
        return cleaned
    if isinstance(value, list):
        return [_sanitize_metadata(item) for item in value]
    if isinstance(value, str):
        if "X-Amz-Signature=" in value:
            return value.split("?", 1)[0]
        return value
    return value


@router.post("")
async def create_play_event(
    payload: PlayEventRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, str]:
    if payload.event_type not in ALLOWED_EVENT_TYPES:
        raise HTTPException(status_code=422, detail="Invalid event type")

    game = await db.get(Game, payload.game_id)
    if game is None or game.status != "published":
        raise HTTPException(status_code=404, detail="Game not found")

    current_user = await get_optional_current_user(request, db)
    metadata = _sanitize_metadata(payload.metadata or {})
    event = PlayEvent(
        game_id=game.id,
        user_id=current_user.user_id if current_user else None,
        event_type=payload.event_type,
        metadata_=metadata,
    )
    db.add(event)
    if payload.event_type == "view":
        game.play_count += 1
    await db.commit()
    return {"status": "ok"}
