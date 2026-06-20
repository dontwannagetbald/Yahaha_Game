from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Annotated, Any

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
from app.models import AgentLog, Game, GenerationJob, UploadedAsset, User


router = APIRouter(prefix="/api/jobs", tags=["jobs"])
SENSITIVE_PATTERN = re.compile(r"(token|secret|password|code)", re.IGNORECASE)


class CreateJobRequest(BaseModel):
    prompt: str = Field(min_length=1)
    asset_ids: list[str] = Field(default_factory=list)
    confirmation: dict[str, Any]


def _serialize_job(job: GenerationJob) -> dict[str, Any]:
    return {
        "job_id": str(job.id),
        "title": (job.confirmation or {}).get("title") or "Untitled Job",
        "status": job.status,
        "created_at": job.created_at.isoformat(),
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "finished_at": job.finished_at.isoformat() if job.finished_at else None,
        "game_id": str(job.game_id) if job.game_id else None,
        "result_summary": job.result_summary,
        "error_message": job.error_message,
        "artifact_prefix": job.artifact_prefix,
        "manifest_url": job.manifest_url,
        "confirmation": job.confirmation,
        "prompt": job.prompt,
    }


def _sanitize_log_message(message: str) -> str:
    if "X-Amz-Signature=" in message:
        message = message.split("?", 1)[0]
    return SENSITIVE_PATTERN.sub("[redacted]", message)


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

        result = await runner.run(runner_input)

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
        elif isinstance(result, AgentRunFailure):
            refreshed_job.status = "failed"
            refreshed_job.finished_at = datetime.now(timezone.utc)
            refreshed_job.error_message = result.error_message
        else:
            refreshed_job.status = "failed"
            refreshed_job.finished_at = datetime.now(timezone.utc)
            refreshed_job.error_message = "Unsupported agent runner result"

        await session.commit()


@router.post("", status_code=201)
async def create_job(
    payload: CreateJobRequest,
    background_tasks: BackgroundTasks,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, Any]:
    if len(payload.asset_ids) > 5:
        raise HTTPException(status_code=400, detail="Asset limit exceeded")

    asset_uuids = [uuid.UUID(asset_id) for asset_id in payload.asset_ids]
    assets: list[UploadedAsset] = []
    if asset_uuids:
        assets = (
            await db.execute(select(UploadedAsset).where(UploadedAsset.id.in_(asset_uuids)))
        ).scalars().all()
        if len(assets) != len(asset_uuids):
            raise HTTPException(status_code=403, detail="Asset does not belong to user")
        if any(asset.user_id != user.user_id for asset in assets):
            raise HTTPException(status_code=403, detail="Asset does not belong to user")

    job = GenerationJob(
        user_id=user.user_id,
        prompt=payload.prompt,
        confirmation=payload.confirmation,
        status="pending",
        created_at=datetime.now(timezone.utc),
    )
    db.add(job)
    await db.flush()
    for asset in assets:
        asset.job_id = job.id

    runner_input = AgentRunInput(
        job_id=job.id,
        user_id=user.user_id,
        prompt=payload.prompt,
        confirmation=payload.confirmation,
        uploaded_assets=[
            UploadedAssetPayload(
                asset_id=asset.id,
                filename=asset.filename,
                mime_type=asset.mime_type,
                size_bytes=asset.size_bytes,
                object_key=asset.object_key,
                purpose=asset.purpose,
            )
            for asset in assets
        ],
    )

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
        "status": job.status,
        "created_at": job.created_at.isoformat(),
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
