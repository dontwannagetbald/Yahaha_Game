from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.db import get_session
from app.models import AgentLog, GenerationJob, UploadedAsset, User


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


@router.post("", status_code=201)
async def create_job(
    payload: CreateJobRequest,
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
    await db.commit()
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
