from __future__ import annotations

import re
import uuid
from inspect import signature
from datetime import datetime, timezone
from typing import Annotated, Any, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.agent_runner import (
    AgentLogEvent,
    AgentRunFailure,
    AgentRunInput,
    AgentRunSuccess,
    UploadedAssetPayload,
    get_agent_runner,
)
from app.auth import get_current_user
from app.db import get_session
from app.models import AgentLog, CreateSession, Game, GenerationJob, UploadedAsset, User


router = APIRouter(prefix="/api/jobs", tags=["jobs"])
SENSITIVE_PATTERN = re.compile(r"(token|secret|password|code)", re.IGNORECASE)


class CreateJobRequest(BaseModel):
    session_id: uuid.UUID
    prompt: Optional[str] = Field(default=None, min_length=1)


class CreateRevisionRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


def _serialize_job(job: GenerationJob) -> dict[str, Any]:
    title = (
        (job.game_plan or {}).get("title")
        or (job.confirmation or {}).get("title")
        or "Untitled Job"
    )
    return {
        "job_id": str(job.id),
        "session_id": str(job.create_session_id) if job.create_session_id else None,
        "parent_job_id": str(job.parent_job_id) if job.parent_job_id else None,
        "title": title,
        "status": job.status,
        "created_at": job.created_at.isoformat(),
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "finished_at": job.finished_at.isoformat() if job.finished_at else None,
        "game_id": str(job.game_id) if job.game_id else None,
        "result_summary": job.result_summary,
        "error_message": _sanitize_log_message(job.error_message) if job.error_message else None,
        "validation_report": job.validation_report,
        "artifact_prefix": job.artifact_prefix,
        "manifest_url": job.manifest_url,
        "confirmation": job.confirmation,
        "user_requirements": job.user_requirements,
        "game_plan": job.game_plan,
        "material_usage": job.material_usage,
        "prompt": job.prompt,
    }


def _confirmation_from_game_plan(game_plan: dict[str, Any]) -> dict[str, Any]:
    return {
        "plan_id": game_plan.get("plan_id"),
        "title": game_plan.get("title") or "Untitled Game",
        "introduction": game_plan.get("introduction") or "",
        "tags": game_plan.get("tags") or [],
    }


def _sanitize_log_message(message: str) -> str:
    if "X-Amz-Signature=" in message:
        message = message.split("?", 1)[0]
    return SENSITIVE_PATTERN.sub("[redacted]", message)


def _sanitize_error_message(error: Exception) -> str:
    message = str(error).strip() or error.__class__.__name__
    return _sanitize_log_message(message)


async def _get_owned_job(
    db: AsyncSession, *, job_id: uuid.UUID, user_id: uuid.UUID
) -> GenerationJob:
    job = await db.get(GenerationJob, job_id)
    if job is None or job.user_id != user_id:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


async def _append_agent_logs(
    db: AsyncSession, *, job_id: uuid.UUID, logs: list[AgentLogEvent]
) -> None:
    for log in logs:
        db.add(
            AgentLog(
                job_id=job_id,
                step=log.step,
                level=log.level,
                message=log.message,
                created_at=log.created_at,
            )
        )


async def _assets_for_material_usage(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    session_id: uuid.UUID | None,
    material_usage: dict[str, Any],
) -> list[UploadedAsset]:
    material_assets = (material_usage or {}).get("assets") or []
    asset_ids = [
        str(asset.get("asset_id"))
        for asset in material_assets
        if isinstance(asset, dict) and asset.get("asset_id")
    ]
    if len(asset_ids) > 5:
        raise HTTPException(status_code=400, detail="Asset limit exceeded")

    try:
        asset_uuids = [uuid.UUID(asset_id) for asset_id in asset_ids]
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid asset id") from exc

    if not asset_uuids:
        return []

    assets = (
        await db.execute(select(UploadedAsset).where(UploadedAsset.id.in_(asset_uuids)))
    ).scalars().all()
    if len(assets) != len(asset_uuids):
        raise HTTPException(status_code=403, detail="Asset does not belong to user")
    if any(asset.user_id != user_id for asset in assets):
        raise HTTPException(status_code=403, detail="Asset does not belong to user")
    if session_id and any(asset.session_id != session_id for asset in assets):
        raise HTTPException(status_code=403, detail="Asset does not belong to session")
    return list(assets)


def _runner_input_for_job(
    *,
    job: GenerationJob,
    uploaded_assets: list[UploadedAsset],
) -> AgentRunInput:
    game_plan = job.game_plan or {}
    return AgentRunInput(
        job_id=job.id,
        user_id=job.user_id,
        session_id=job.create_session_id,
        prompt=job.prompt,
        confirmation=job.confirmation or _confirmation_from_game_plan(game_plan),
        user_requirements=job.user_requirements or {},
        game_plan=game_plan,
        material_usage=job.material_usage or {"assets": []},
        uploaded_assets=[
            UploadedAssetPayload(
                asset_id=asset.id,
                filename=asset.filename,
                mime_type=asset.mime_type,
                size_bytes=asset.size_bytes,
                object_key=asset.object_key,
                purpose=asset.purpose,
            )
            for asset in uploaded_assets
        ],
        )


async def _append_agent_log(
    db: AsyncSession, *, job_id: uuid.UUID, log: AgentLogEvent
) -> None:
    db.add(
        AgentLog(
            job_id=job_id,
            step=log.step,
            level=log.level,
            message=_sanitize_log_message(log.message),
            created_at=log.created_at,
        )
    )
    await db.commit()


def _runner_accepts_emit_log(runner: Any) -> bool:
    try:
        return "emit_log" in signature(runner.run).parameters
    except (TypeError, ValueError):
        return False


async def _run_job_in_background(
    *,
    session_factory,
    job_id: uuid.UUID,
    runner_input: AgentRunInput,
) -> None:
    runner = get_agent_runner()
    async with session_factory() as session:
        job = await session.get(GenerationJob, job_id)
        if job is None:
            return

        job.status = "running"
        job.started_at = datetime.now(timezone.utc)
        await session.commit()

        async def emit_log(log: AgentLogEvent) -> None:
            await _append_agent_log(session, job_id=job_id, log=log)

        try:
            if _runner_accepts_emit_log(runner):
                result = await runner.run(runner_input, emit_log=emit_log)
            else:
                result = await runner.run(runner_input)
        except Exception as exc:
            error_message = _sanitize_error_message(exc)
            failed_job = await session.get(GenerationJob, job_id)
            if failed_job is None:
                return

            failed_job.status = "failed"
            failed_job.finished_at = datetime.now(timezone.utc)
            failed_job.error_message = error_message
            session.add(
                AgentLog(
                    job_id=job_id,
                    step="agent_runner",
                    level="error",
                    message=error_message,
                    created_at=datetime.now(timezone.utc),
                )
            )
            await session.commit()
            return

        refreshed_job = await session.get(GenerationJob, job_id)
        if refreshed_job is None:
            return

        await _append_agent_logs(
            session,
            job_id=job_id,
            logs=list(result.logs),
        )

        if isinstance(result, AgentRunSuccess):
            game = Game(
                owner_id=refreshed_job.user_id,
                title=result.title,
                description=result.description,
                cover_url=result.cover_url,
                tags=result.tags,
                status="draft",
                manifest_url=result.manifest_url,
                artifact_base_url=result.artifact_base_url,
            )
            session.add(game)
            await session.flush()

            refreshed_job.status = "succeeded"
            refreshed_job.finished_at = datetime.now(timezone.utc)
            refreshed_job.game_id = game.id
            refreshed_job.artifact_prefix = result.artifact_prefix
            refreshed_job.manifest_url = result.manifest_url
            refreshed_job.result_summary = result.result_summary
            refreshed_job.error_message = None
            refreshed_job.validation_report = None
        elif isinstance(result, AgentRunFailure):
            refreshed_job.status = "failed"
            refreshed_job.finished_at = datetime.now(timezone.utc)
            refreshed_job.error_message = result.error_message
            refreshed_job.validation_report = result.validation_report
        else:
            refreshed_job.status = "failed"
            refreshed_job.finished_at = datetime.now(timezone.utc)
            refreshed_job.error_message = "Unsupported agent runner result"
            refreshed_job.validation_report = None

        await session.commit()


@router.post("", status_code=201)
async def create_job(
    payload: CreateJobRequest,
    background_tasks: BackgroundTasks,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, Any]:
    create_session = await db.get(CreateSession, payload.session_id)
    if create_session is None or create_session.user_id != user.user_id:
        raise HTTPException(status_code=404, detail="Create session not found")
    if create_session.status != "confirmed":
        raise HTTPException(status_code=400, detail="Create session is not confirmed")

    user_requirements = create_session.user_requirements or {}
    game_plan = create_session.game_plan or {}
    material_usage = create_session.material_usage or {"assets": []}
    assets = await _assets_for_material_usage(
        db,
        user_id=user.user_id,
        session_id=create_session.id,
        material_usage=material_usage,
    )
    prompt = (
        payload.prompt
        or user_requirements.get("intent_summary")
        or game_plan.get("title")
        or "Generate game from confirmed create session"
    )
    confirmation = _confirmation_from_game_plan(game_plan)

    job = GenerationJob(
        user_id=user.user_id,
        prompt=prompt,
        confirmation=confirmation,
        create_session_id=create_session.id,
        user_requirements=user_requirements,
        game_plan=game_plan,
        material_usage=material_usage,
        status="pending",
        created_at=datetime.now(timezone.utc),
    )
    db.add(job)
    await db.flush()
    for asset in assets:
        asset.job_id = job.id

    runner_input = _runner_input_for_job(job=job, uploaded_assets=assets)

    session_factory = async_sessionmaker(db.bind, expire_on_commit=False)
    await db.commit()
    background_tasks.add_task(
        _run_job_in_background,
        session_factory=session_factory,
        job_id=job.id,
        runner_input=runner_input,
    )
    return {
        "job_id": str(job.id),
        "session_id": str(create_session.id),
        "status": job.status,
        "created_at": job.created_at.isoformat(),
    }


@router.post("/{job_id}/revisions", status_code=201)
async def create_revision_job(
    job_id: uuid.UUID,
    payload: CreateRevisionRequest,
    background_tasks: BackgroundTasks,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, Any]:
    source_job = await _get_owned_job(db, job_id=job_id, user_id=user.user_id)
    if source_job.status in {"pending", "running"}:
        raise HTTPException(status_code=409, detail="Job is still generating")

    if source_job.status not in {"succeeded", "failed"}:
        raise HTTPException(status_code=409, detail="Job cannot be revised")

    revision_intent = payload.message.strip()
    user_requirements = dict(source_job.user_requirements or {})
    game_plan = dict(source_job.game_plan or {})
    material_usage = dict(source_job.material_usage or {"assets": []})
    assets = await _assets_for_material_usage(
        db,
        user_id=user.user_id,
        session_id=source_job.create_session_id,
        material_usage=material_usage,
    )
    prompt = f"{source_job.prompt}\n\nRevision: {revision_intent}"
    confirmation = source_job.confirmation or _confirmation_from_game_plan(game_plan)

    revision_job = GenerationJob(
        user_id=user.user_id,
        prompt=prompt,
        confirmation=confirmation,
        create_session_id=source_job.create_session_id,
        parent_job_id=source_job.id,
        revision_intent=revision_intent,
        user_requirements=user_requirements,
        game_plan=game_plan,
        material_usage=material_usage,
        status="pending",
        created_at=datetime.now(timezone.utc),
    )
    db.add(revision_job)
    await db.flush()

    runner_input = _runner_input_for_job(job=revision_job, uploaded_assets=assets)
    session_factory = async_sessionmaker(db.bind, expire_on_commit=False)
    await db.commit()
    background_tasks.add_task(
        _run_job_in_background,
        session_factory=session_factory,
        job_id=revision_job.id,
        runner_input=runner_input,
    )
    return {
        "job_id": str(revision_job.id),
        "session_id": str(revision_job.create_session_id)
        if revision_job.create_session_id
        else None,
        "parent_job_id": str(source_job.id),
        "status": revision_job.status,
        "created_at": revision_job.created_at.isoformat(),
    }


@router.get("")
async def list_jobs(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, Any]:
    jobs = (
        await db.execute(
            select(GenerationJob)
            .where(GenerationJob.user_id == user.user_id)
            .order_by(GenerationJob.created_at.desc())
        )
    ).scalars().all()
    return {"jobs": [_serialize_job(job) for job in jobs]}


@router.get("/{job_id}")
async def get_job(
    job_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, Any]:
    job = await _get_owned_job(db, job_id=job_id, user_id=user.user_id)
    return _serialize_job(job)


@router.get("/{job_id}/logs")
async def get_job_logs(
    job_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, Any]:
    job = await _get_owned_job(db, job_id=job_id, user_id=user.user_id)
    logs = (
        await db.execute(
            select(AgentLog)
            .where(AgentLog.job_id == job.id)
            .order_by(AgentLog.created_at.asc())
        )
    ).scalars().all()
    return {
        "logs": [
            {
                "step": log.step,
                "level": log.level,
                "message": _sanitize_log_message(log.message),
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ]
    }
