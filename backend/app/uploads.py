from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.db import get_session
from app.models import UploadedAsset, User
from app.schemas import (
    UploadCompleteRequest,
    UploadCompleteResponse,
    UploadPresignRequest,
    UploadPresignResponse,
)
from app.storage import ObjectStorageService
from app.config import settings


router = APIRouter(prefix="/api/uploads", tags=["uploads"])

MAX_UPLOAD_SIZE_BYTES = 20 * 1024 * 1024


def get_storage_service() -> ObjectStorageService:
    return ObjectStorageService(settings)


@router.post("/presign", response_model=UploadPresignResponse)
async def presign_upload(
    payload: UploadPresignRequest,
    user: Annotated[User, Depends(get_current_user)],
    storage: Annotated[ObjectStorageService, Depends(get_storage_service)],
) -> UploadPresignResponse:
    if payload.size_bytes > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds 20MB limit")

    upload_id = uuid.uuid4()
    object_key = storage.build_upload_object_key(
        user_id=user.user_id,
        upload_id=upload_id,
        filename=payload.filename,
    )
    presigned = storage.build_presigned_upload_url(object_key)
    return UploadPresignResponse(
        upload_id=str(upload_id),
        object_key=object_key,
        upload_url=presigned.url,
        expires_in=presigned.expires_in,
    )


@router.post("/complete", response_model=UploadCompleteResponse)
async def complete_upload(
    payload: UploadCompleteRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> UploadCompleteResponse:
    expected_prefix = f"uploads/{user.user_id}/"
    if not payload.object_key.startswith(expected_prefix):
        raise HTTPException(status_code=403, detail="Upload does not belong to user")

    asset = UploadedAsset(
        user_id=user.user_id,
        job_id=None,
        filename=payload.filename,
        mime_type=payload.mime_type,
        size_bytes=payload.size_bytes,
        object_key=payload.object_key,
        purpose=None,
    )
    db.add(asset)
    await db.flush()
    await db.commit()

    return UploadCompleteResponse(
        asset_id=str(asset.id),
        filename=asset.filename,
        mime_type=asset.mime_type,
        size_bytes=asset.size_bytes,
    )
