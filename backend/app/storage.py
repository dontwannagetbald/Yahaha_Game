from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import PurePosixPath
from urllib.parse import quote

import boto3
from botocore.client import Config
from botocore.exceptions import BotoCoreError

from app.config import Settings


class StorageConfigurationError(RuntimeError):
    pass


class StorageUnavailableError(RuntimeError):
    pass


@dataclass(frozen=True)
class PresignedUrlResult:
    url: str
    expires_in: int


class ObjectStorageService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.bucket = settings.minio_bucket
        self._s3_client = boto3.client(
            "s3",
            endpoint_url=settings.minio_endpoint,
            aws_access_key_id=settings.minio_access_key,
            aws_secret_access_key=settings.minio_secret_key,
            region_name=settings.minio_region,
            use_ssl=settings.minio_use_ssl,
            config=Config(signature_version="s3v4"),
        )

    def build_upload_object_key(self, *, user_id, upload_id, filename: str) -> str:
        safe_filename = self._sanitize_filename(filename)
        return f"uploads/{user_id}/{upload_id}/{safe_filename}"

    def build_draft_object_key(
        self, *, user_id, job_id, version: str, relative_path: str
    ) -> str:
        safe_relative_path = self._sanitize_relative_path(relative_path)
        return f"drafts/{user_id}/{job_id}/{version}/{safe_relative_path}"

    def build_published_object_key(
        self, *, game_id, version: str, relative_path: str
    ) -> str:
        safe_relative_path = self._sanitize_relative_path(relative_path)
        return f"published/{game_id}/{version}/{safe_relative_path}"

    def build_presigned_upload_url(
        self, object_key: str, *, expires_in: int = 900
    ) -> PresignedUrlResult:
        url = self._generate_presigned_url(
            "put_object",
            object_key=object_key,
            expires_in=expires_in,
        )
        return PresignedUrlResult(url=url, expires_in=expires_in)

    def build_presigned_read_url(
        self, object_key: str, *, expires_in: int = 900
    ) -> PresignedUrlResult:
        url = self._generate_presigned_url(
            "get_object",
            object_key=object_key,
            expires_in=expires_in,
        )
        return PresignedUrlResult(url=url, expires_in=expires_in)

    def build_public_read_url(self, object_key: str) -> str:
        if not object_key.startswith("published/"):
            raise StorageConfigurationError(
                "Public URL is only allowed for published/* object keys"
            )

        quoted_key = quote(object_key, safe="/-_.~")
        return f"{self.settings.minio_public_endpoint}/{self.bucket}/{quoted_key}"

    def _sanitize_filename(self, filename: str) -> str:
        name = PurePosixPath(filename).name.strip()
        raw_stem, raw_dot, raw_suffix = name.rpartition(".")
        base_name = raw_stem if raw_dot else raw_suffix
        suffix = f".{raw_suffix}" if raw_dot else ""

        safe_base = re.sub(r"[^a-zA-Z0-9._-]+", "-", base_name)
        safe_base = re.sub(r"-{2,}", "-", safe_base).strip(".-").lower()
        safe_suffix = (
            re.sub(r"[^a-zA-Z0-9]+", "", raw_suffix).lower() if raw_dot else ""
        )

        if not safe_base:
            raise StorageConfigurationError("Filename is empty after sanitization")
        if safe_suffix:
            return f"{safe_base}.{safe_suffix}"
        return safe_base

    def _sanitize_relative_path(self, relative_path: str) -> str:
        parts: list[str] = []
        for part in PurePosixPath(relative_path).parts:
            if part in {"", ".", ".."}:
                continue
            clean = re.sub(r"[^a-zA-Z0-9._-]+", "-", part).strip(".-")
            if clean:
                parts.append(clean)
        if not parts:
            raise StorageConfigurationError("Relative path is empty after sanitization")
        return "/".join(parts)

    def _generate_presigned_url(
        self, operation_name: str, *, object_key: str, expires_in: int
    ) -> str:
        try:
            return self._s3_client.generate_presigned_url(
                operation_name,
                Params={"Bucket": self.bucket, "Key": object_key},
                ExpiresIn=expires_in,
            )
        except BotoCoreError as exc:
            raise StorageUnavailableError(
                "Object storage is unavailable"
            ) from exc
