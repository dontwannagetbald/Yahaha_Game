from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Annotated, Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.conversation_runner import run_conversation_graph
from app.db import get_session
from app.models import CreateSession, CreateSessionMessage, UploadedAsset, User


router = APIRouter(prefix="/api/create-sessions", tags=["create-sessions"])

ALLOWED_EVENT_TYPES = {"chat", "upload_assets", "regenerate", "confirm"}
WELCOME_MESSAGE = "您好呀，今天想要尝试做个什么样的游戏呢✨🧙‍♀️？"


async def _run_graph_or_raise_http(state: dict[str, Any]) -> dict[str, Any]:
    try:
        return await run_conversation_graph(state)
    except Exception as exc:
        message = str(exc).strip() or "Agent 对话生成失败，请稍后重试。"
        if getattr(exc, "details", None):
            raise HTTPException(
                status_code=502,
                detail={
                    "code": "provider_error",
                    "message": message,
                    "retry_hint": "请稍后重试。",
                    "details": exc.details,
                },
            ) from exc
        raise HTTPException(status_code=502, detail=message) from exc


class CreateSessionRequest(BaseModel):
    initial_message: Optional[str] = Field(default=None, max_length=4000)
    asset_ids: list[str] = Field(default_factory=list)


class UploadedAssetEventPayload(BaseModel):
    asset_id: str
    filename: Optional[str] = None
    mime_type: Optional[str] = None
    size_bytes: Optional[int] = None
    object_key: Optional[str] = None
    user_hint: Optional[str] = None


class CreateSessionEventRequest(BaseModel):
    type: str = Field(min_length=1)
    message: Optional[str] = Field(default=None, max_length=4000)
    uploaded_assets: list[UploadedAssetEventPayload] = Field(default_factory=list)
    replace_existing_assets: bool = False
    selected_plan_id: Optional[str] = None


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _empty_user_requirements() -> dict[str, Any]:
    return {
        "intent_summary": "",
        "must_have": [],
        "nice_to_have": [],
        "constraints": [],
        "open_questions": [],
        "answered_questions": [],
        "preference_profile": {
            "genre_candidates": [],
            "visual_style": None,
            "tone": None,
            "target_session_length": None,
            "difficulty": None,
        },
        "revision_count": 0,
    }


def _empty_game_plan() -> dict[str, Any]:
    return {
        "plan_id": None,
        "title": "",
        "introduction": "",
        "tags": [],
        "gameplay": "",
        "core_loop": [],
        "style": "",
        "characters": [],
        "win_condition": "",
        "lose_condition": "",
        "controls": "",
        "suggestions": [],
        "confidence": "low",
    }


def _empty_assistant_response() -> dict[str, Any]:
    return {
        "message": "",
        "suggestions": [],
        "card": None,
        "actions": [],
    }


def _serialize_session(
    create_session: CreateSession,
    *,
    messages: list[CreateSessionMessage],
    handoff_to_generation: bool = False,
) -> dict[str, Any]:
    return {
        "session_id": str(create_session.id),
        "conversation_status": create_session.status,
        "user_requirements": create_session.user_requirements,
        "game_plan": create_session.game_plan or None,
        "material_usage": create_session.material_usage,
        "assistant_response": create_session.assistant_response,
        "messages": [_serialize_message(message) for message in messages],
        "handoff_to_generation": handoff_to_generation,
        "created_at": create_session.created_at.isoformat(),
        "updated_at": create_session.updated_at.isoformat(),
    }


def _serialize_message(message: CreateSessionMessage) -> dict[str, Any]:
    return {
        "id": str(message.id),
        "role": message.role,
        "content": message.content,
        "payload": message.payload,
        "created_at": message.created_at.isoformat(),
    }


async def _load_messages(
    db: AsyncSession, *, session_id: uuid.UUID
) -> list[CreateSessionMessage]:
    return (
        await db.execute(
            select(CreateSessionMessage)
            .where(CreateSessionMessage.session_id == session_id)
            .order_by(CreateSessionMessage.created_at, CreateSessionMessage.id)
        )
    ).scalars().all()


async def _load_assets(
    db: AsyncSession, *, asset_ids: list[str], user_id: uuid.UUID
) -> list[UploadedAsset]:
    if not asset_ids:
        return []
    try:
        asset_uuids = [uuid.UUID(asset_id) for asset_id in asset_ids]
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid asset id") from exc
    assets = (
        await db.execute(select(UploadedAsset).where(UploadedAsset.id.in_(asset_uuids)))
    ).scalars().all()
    if len(assets) != len(asset_uuids) or any(asset.user_id != user_id for asset in assets):
        raise HTTPException(status_code=403, detail="Asset does not belong to user")
    return assets


def _asset_usage(asset: UploadedAsset, *, user_hint: Optional[str] = None) -> dict[str, Any]:
    return {
        "asset_id": str(asset.id),
        "filename": asset.filename,
        "mime_type": asset.mime_type,
        "size_bytes": asset.size_bytes,
        "object_key": asset.object_key,
        "user_hint": user_hint or asset.purpose or "",
    }


async def _get_owned_session(
    db: AsyncSession, *, session_id: uuid.UUID, user_id: uuid.UUID
) -> CreateSession:
    create_session = await db.get(CreateSession, session_id)
    if create_session is None or create_session.user_id != user_id:
        raise HTTPException(status_code=404, detail="Create session not found")
    return create_session


def _append_user_message(
    db: AsyncSession,
    *,
    session_id: uuid.UUID,
    content: str,
    event_type: str = "chat",
) -> None:
    db.add(
        CreateSessionMessage(
            session_id=session_id,
            role="user",
            content=content,
            payload={"event_type": event_type},
            created_at=_now(),
        )
    )


def _append_event_message(
    db: AsyncSession,
    *,
    session_id: uuid.UUID,
    event_type: str,
    content: str,
    payload: Optional[dict[str, Any]] = None,
) -> None:
    message_payload = {"event_type": event_type}
    if payload:
        message_payload.update(payload)
    db.add(
        CreateSessionMessage(
            session_id=session_id,
            role="system",
            content=content,
            payload=message_payload,
            created_at=_now(),
        )
    )


def _append_assistant_message(
    db: AsyncSession,
    *,
    session_id: uuid.UUID,
    assistant_response: dict[str, Any],
) -> None:
    content = str(assistant_response.get("message") or "")
    if not content:
        return
    db.add(
        CreateSessionMessage(
            session_id=session_id,
            role="assistant",
            content=content,
            payload={
                "event_type": "assistant_response",
                "suggestions": assistant_response.get("suggestions") or [],
                "card": assistant_response.get("card"),
                "actions": assistant_response.get("actions") or [],
            },
            created_at=_now(),
        )
    )


def _append_event_input_message(
    db: AsyncSession,
    *,
    session_id: uuid.UUID,
    event: dict[str, Any],
) -> None:
    event_type = event["type"]
    if event_type == "chat":
        _append_user_message(
            db,
            session_id=session_id,
            content=str(event.get("message") or ""),
            event_type="chat",
        )
        return
    if event_type == "upload_assets":
        uploaded_assets = event.get("uploaded_assets") or []
        filenames = [
            asset.get("filename") or asset.get("asset_id")
            for asset in uploaded_assets
            if isinstance(asset, dict)
        ]
        summary = "上传素材" if not filenames else f"上传素材：{', '.join(filenames)}"
        _append_event_message(
            db,
            session_id=session_id,
            event_type="upload_assets",
            content=summary,
            payload={
                "assets": [
                    {
                        "asset_id": asset.get("asset_id"),
                        "filename": asset.get("filename"),
                        "mime_type": asset.get("mime_type"),
                        "size_bytes": asset.get("size_bytes"),
                        "user_hint": asset.get("user_hint"),
                    }
                    for asset in uploaded_assets
                    if isinstance(asset, dict)
                ]
            },
        )
        return
    if event_type == "regenerate":
        _append_event_message(
            db,
            session_id=session_id,
            event_type="regenerate",
            content="换一换游戏方案",
            payload={"selected_plan_id": event.get("selected_plan_id")},
        )
        return
    if event_type == "confirm":
        _append_event_message(
            db,
            session_id=session_id,
            event_type="confirm",
            content="确认当前游戏方案",
            payload={"selected_plan_id": event.get("selected_plan_id")},
        )


def _event_from_initial_message(
    initial_message: Optional[str], assets: list[UploadedAsset]
) -> dict[str, Any] | None:
    if initial_message and initial_message.strip():
        return {"type": "chat", "message": initial_message.strip()}
    if assets:
        return {
            "type": "upload_assets",
            "uploaded_assets": [_asset_usage(asset) for asset in assets],
        }
    return None


def _empty_graph_result(*, material_usage: dict[str, Any]) -> dict[str, Any]:
    assistant_response = _empty_assistant_response()
    assistant_response["message"] = WELCOME_MESSAGE
    return {
        "conversation_status": "collecting",
        "user_requirements": _empty_user_requirements(),
        "game_plan": _empty_game_plan(),
        "material_usage": material_usage,
        "assistant_response": assistant_response,
        "handoff_to_generation": False,
    }


def _state_for_graph(
    *,
    create_session: Optional[CreateSession],
    user_event: dict[str, Any],
    material_usage: Optional[dict[str, Any]] = None,
    conversation_history: Optional[list[dict[str, Any]]] = None,
) -> dict[str, Any]:
    return {
        "user_requirements": (
            create_session.user_requirements if create_session else _empty_user_requirements()
        ),
        "game_plan": create_session.game_plan if create_session else _empty_game_plan(),
        "material_usage": (
            material_usage
            if material_usage is not None
            else (create_session.material_usage if create_session else {"assets": []})
        ),
        "assistant_response": (
            create_session.assistant_response
            if create_session
            else _empty_assistant_response()
        ),
        "handoff_to_generation": False,
        "conversation_status": (
            create_session.status if create_session else "collecting"
        ),
        "user_event": user_event,
        "conversation_history": conversation_history or [],
    }


def _conversation_history_from_messages(
    messages: list[CreateSessionMessage],
) -> list[dict[str, str]]:
    history: list[dict[str, str]] = []
    for message in messages:
        content = str(message.content or "").strip()
        if not content:
            continue
        history.append({"role": message.role, "content": content})
    return history


def _apply_graph_result(
    create_session: CreateSession, result: dict[str, Any]
) -> bool:
    create_session.status = result["conversation_status"]
    create_session.user_requirements = result["user_requirements"]
    create_session.game_plan = result["game_plan"]
    create_session.material_usage = result["material_usage"]
    create_session.assistant_response = result["assistant_response"]
    handoff = bool(result.get("handoff_to_generation", False))
    if handoff and create_session.status == "confirmed":
        create_session.confirmed_at = _now()
    return handoff


@router.post("", status_code=201)
async def create_session(
    payload: CreateSessionRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, Any]:
    assets = await _load_assets(db, asset_ids=payload.asset_ids, user_id=user.user_id)
    material_usage = {"assets": [_asset_usage(asset) for asset in assets]}
    initial_event = _event_from_initial_message(payload.initial_message, assets)
    if initial_event is None:
        graph_state = None
        graph_result = _empty_graph_result(material_usage=material_usage)
    else:
        graph_state = _state_for_graph(
            create_session=None,
            user_event=initial_event,
            material_usage=material_usage,
        )
        graph_result = await _run_graph_or_raise_http(graph_state)
    now = _now()
    create_session = CreateSession(
        user_id=user.user_id,
        status=graph_result["conversation_status"],
        user_requirements=graph_result["user_requirements"],
        game_plan=graph_result["game_plan"],
        material_usage=graph_result["material_usage"],
        assistant_response=graph_result["assistant_response"],
        created_at=now,
        updated_at=now,
    )
    db.add(create_session)
    await db.flush()
    for asset in assets:
        asset.session_id = create_session.id
    if graph_state is not None:
        _append_event_input_message(
            db, session_id=create_session.id, event=graph_state["user_event"]
        )
    _append_assistant_message(
        db,
        session_id=create_session.id,
        assistant_response=graph_result["assistant_response"],
    )
    await db.commit()
    await db.refresh(create_session)
    messages = await _load_messages(db, session_id=create_session.id)
    return _serialize_session(create_session, messages=messages)


@router.get("/{session_id}")
async def get_create_session(
    session_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, Any]:
    create_session = await _get_owned_session(
        db, session_id=session_id, user_id=user.user_id
    )
    messages = await _load_messages(db, session_id=create_session.id)
    return _serialize_session(create_session, messages=messages)


@router.post("/{session_id}/events")
async def handle_create_session_event(
    session_id: uuid.UUID,
    payload: CreateSessionEventRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, Any]:
    create_session = await _get_owned_session(
        db, session_id=session_id, user_id=user.user_id
    )
    if payload.type not in ALLOWED_EVENT_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported event type")

    if payload.type == "chat" and not payload.message:
        raise HTTPException(status_code=400, detail="Chat message is required")

    event: dict[str, Any] = {"type": payload.type}
    if payload.message is not None:
        event["message"] = payload.message
    if payload.selected_plan_id is not None:
        event["selected_plan_id"] = payload.selected_plan_id

    if payload.type == "upload_assets":
        asset_ids = [asset.asset_id for asset in payload.uploaded_assets]
        assets = await _load_assets(db, asset_ids=asset_ids, user_id=user.user_id)
        hint_by_id = {
            asset.asset_id: asset.user_hint for asset in payload.uploaded_assets
        }
        event["uploaded_assets"] = [
            _asset_usage(asset, user_hint=hint_by_id.get(str(asset.id)))
            for asset in assets
        ]
        event["replace_existing_assets"] = payload.replace_existing_assets
        for asset in assets:
            asset.session_id = create_session.id

    previous_messages = await _load_messages(db, session_id=create_session.id)
    graph_result = await _run_graph_or_raise_http(
        _state_for_graph(
            create_session=create_session,
            user_event=event,
            conversation_history=_conversation_history_from_messages(previous_messages),
        )
    )
    handoff_to_generation = _apply_graph_result(create_session, graph_result)
    _append_event_input_message(db, session_id=create_session.id, event=event)
    _append_assistant_message(
        db,
        session_id=create_session.id,
        assistant_response=graph_result["assistant_response"],
    )

    create_session.updated_at = _now()
    await db.commit()
    await db.refresh(create_session)
    messages = await _load_messages(db, session_id=create_session.id)
    return _serialize_session(
        create_session,
        messages=messages,
        handoff_to_generation=handoff_to_generation,
    )
