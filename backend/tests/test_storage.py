from __future__ import annotations

import uuid

import pytest
from botocore.exceptions import BotoCoreError

from app.config import Settings


def build_settings() -> Settings:
    return Settings(
        database_url="postgresql+asyncpg://user:pass@db:5432/app",
        minio_endpoint="http://minio:9000",
        minio_public_endpoint="http://localhost:9000",
        minio_access_key="change-me-local",
        minio_secret_key="change-me-local",
        minio_bucket="yahaha-game",
        minio_region="us-east-1",
        minio_use_ssl=False,
    )


def test_object_key_builders_use_single_bucket_boundary():
    from app.storage import ObjectStorageService

    service = ObjectStorageService(build_settings())

    user_id = uuid.UUID("11111111-1111-1111-1111-111111111111")
    upload_id = uuid.UUID("22222222-2222-2222-2222-222222222222")
    job_id = uuid.UUID("33333333-3333-3333-3333-333333333333")
    game_id = uuid.UUID("44444444-4444-4444-4444-444444444444")

    upload_key = service.build_upload_object_key(
        user_id=user_id,
        upload_id=upload_id,
        filename="cover final.png",
    )
    draft_key = service.build_draft_object_key(
        user_id=user_id,
        job_id=job_id,
        version="v1",
        relative_path="build/manifest.json",
    )
    published_key = service.build_published_object_key(
        game_id=game_id,
        version="v3",
        relative_path="bundle/index.js",
    )

    assert service.bucket == "yahaha-game"
    assert upload_key == (
        "uploads/11111111-1111-1111-1111-111111111111/"
        "22222222-2222-2222-2222-222222222222/cover-final.png"
    )
    assert draft_key == (
        "drafts/11111111-1111-1111-1111-111111111111/"
        "33333333-3333-3333-3333-333333333333/v1/build/manifest.json"
    )
    assert published_key == (
        "published/44444444-4444-4444-4444-444444444444/v3/bundle/index.js"
    )


def test_object_key_builders_strip_path_traversal_segments():
    from app.storage import ObjectStorageService

    service = ObjectStorageService(build_settings())

    user_id = uuid.UUID("11111111-1111-1111-1111-111111111111")
    upload_id = uuid.UUID("22222222-2222-2222-2222-222222222222")

    object_key = service.build_upload_object_key(
        user_id=user_id,
        upload_id=upload_id,
        filename="../nested//..//my poster?.png",
    )

    assert ".." not in object_key
    assert object_key.endswith("/my-poster.png")


def test_private_prefixes_return_presigned_urls_without_full_signature_assertions():
    from app.storage import ObjectStorageService

    service = ObjectStorageService(build_settings())

    draft_result = service.build_presigned_read_url("drafts/user/job/v1/manifest.json")
    upload_result = service.build_presigned_upload_url("uploads/user/upload/file.png")

    assert draft_result.expires_in == 900
    assert upload_result.expires_in == 900
    assert draft_result.url.startswith("http://minio:9000/yahaha-game/")
    assert upload_result.url.startswith("http://minio:9000/yahaha-game/")
    assert "X-Amz-Signature=" in draft_result.url
    assert "X-Amz-Signature=" in upload_result.url


def test_published_prefix_returns_public_url():
    from app.storage import ObjectStorageService

    service = ObjectStorageService(build_settings())

    public_url = service.build_public_read_url(
        "published/game-id/v2/manifest.json"
    )

    assert public_url == "http://localhost:9000/yahaha-game/published/game-id/v2/manifest.json"


def test_public_url_rejects_non_published_prefix():
    from app.storage import ObjectStorageService, StorageConfigurationError

    service = ObjectStorageService(build_settings())

    with pytest.raises(StorageConfigurationError):
        service.build_public_read_url("uploads/user/upload/file.png")


def test_presigned_url_wraps_storage_client_failures(monkeypatch):
    from app.storage import (
        ObjectStorageService,
        StorageUnavailableError,
    )

    service = ObjectStorageService(build_settings())

    def broken_generate_presigned_url(*args, **kwargs):
        raise BotoCoreError()

    monkeypatch.setattr(
        service._s3_client,
        "generate_presigned_url",
        broken_generate_presigned_url,
    )

    with pytest.raises(StorageUnavailableError):
        service.build_presigned_read_url("uploads/user/upload/file.png")
