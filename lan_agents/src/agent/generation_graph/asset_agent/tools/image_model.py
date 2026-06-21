"""Image generation client boundary for Asset Agent."""

from __future__ import annotations

import base64
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Protocol
from urllib import error, request

from agent.providers.base import (
    ProviderConfig,
    ProviderConfigurationError,
    ProviderError,
)


class ImageGenerationClient(Protocol):
    """Minimal image generation interface used by Asset Agent."""

    def generate_png(self, *, prompt: str, size: str, output_path: Path) -> None:
        """Generate a PNG image at the requested path."""

    def edit_png(
        self,
        *,
        prompt: str,
        size: str,
        input_path: Path,
        output_path: Path,
    ) -> None:
        """Refine a reference image into a PNG at the requested path."""


@dataclass(frozen=True)
class ImageGenerationConfig:
    """Environment-backed image generation configuration."""

    provider: str = "mock"
    api_key: str = ""
    base_url: str = ""
    model: str = "gpt-image-2"
    timeout_seconds: float = 180.0
    quality: str = "auto"
    background_size: str = "1280x720"
    player_source_size: str = "1024x1024"

    @classmethod
    def from_env(cls) -> "ImageGenerationConfig":
        """Build image generation config from environment and local `.env`."""
        common = ProviderConfig.from_env()
        dotenv_values = _load_nearest_dotenv()
        timeout = _env_value(
            "OPENAI_IMAGE_TIMEOUT_SECONDS",
            dotenv_values,
            str(common.timeout_seconds or 180.0),
        )
        try:
            timeout_seconds = float(timeout)
        except ValueError:
            timeout_seconds = 180.0
        return cls(
            provider=_env_value("ASSET_IMAGE_PROVIDER", dotenv_values, "mock") or "mock",
            api_key=_env_value(
                "OPENAI_IMAGE_API_KEY",
                dotenv_values,
                common.api_key,
            ),
            base_url=_env_value(
                "OPENAI_IMAGE_BASE_URL",
                dotenv_values,
                common.base_url or "https://api.openai.com/v1",
            ),
            model=_env_value("OPENAI_IMAGE_MODEL", dotenv_values, "gpt-image-2")
            or "gpt-image-2",
            timeout_seconds=timeout_seconds,
            quality=_env_value("OPENAI_IMAGE_QUALITY", dotenv_values, "auto") or "auto",
            background_size=_env_value(
                "OPENAI_IMAGE_BACKGROUND_SIZE",
                dotenv_values,
                "1280x720",
            )
            or "1280x720",
            player_source_size=_env_value(
                "OPENAI_IMAGE_PLAYER_SOURCE_SIZE",
                dotenv_values,
                "1024x1024",
            )
            or "1024x1024",
        )


class OpenAIImageGenerationClient:
    """Call an OpenAI-compatible `/images/generations` endpoint."""

    def __init__(
        self,
        config: ImageGenerationConfig,
        urlopen: Callable[..., Any] | None = None,
    ) -> None:
        missing = []
        if not config.api_key:
            missing.append("OPENAI_IMAGE_API_KEY or OPENAI_COMPATIBLE_API_KEY")
        if not config.base_url:
            missing.append("OPENAI_IMAGE_BASE_URL or OPENAI_COMPATIBLE_BASE_URL")
        if not config.model:
            missing.append("OPENAI_IMAGE_MODEL")
        if missing:
            raise ProviderConfigurationError(
                f"Missing image provider configuration: {', '.join(missing)}"
            )
        self._config = config
        self._urlopen = urlopen or request.urlopen

    def generate_png(self, *, prompt: str, size: str, output_path: Path) -> None:
        """Generate a PNG via `/images/generations` and write it to disk."""
        payload = {
            "model": self._config.model,
            "prompt": prompt,
            "size": size,
            "quality": self._config.quality,
            "output_format": "png",
        }
        http_request = request.Request(
            _images_generations_url(self._config.base_url),
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self._config.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with self._urlopen(  # nosec B310 - endpoint is configured server-side.
                http_request, timeout=self._config.timeout_seconds
            ) as response:
                raw = response.read().decode("utf-8")
        except error.HTTPError as exc:
            detail = exc.read(500).decode("utf-8", "replace").strip()
            suffix = f": {_safe_preview(detail)}" if detail else ""
            raise ProviderError(f"Image provider HTTP error: {exc.code}{suffix}") from exc
        except TimeoutError as exc:
            raise ProviderError(
                "Image provider request timed out after "
                f"{self._config.timeout_seconds:g}s; increase "
                "OPENAI_IMAGE_TIMEOUT_SECONDS for slow image generation providers"
            ) from exc
        except OSError as exc:
            raise ProviderError("Image provider request failed") from exc
        png_bytes = parse_image_generation_response(raw)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(png_bytes)

    def edit_png(
        self,
        *,
        prompt: str,
        size: str,
        input_path: Path,
        output_path: Path,
    ) -> None:
        """Generate a refined PNG via `/images/edits` and write it to disk."""
        if not input_path.is_file():
            raise ProviderError(f"Image edit input is not readable: {input_path}")
        boundary = f"----yahaha-image-{os.urandom(16).hex()}"
        body = _multipart_form_data(
            boundary=boundary,
            fields={
                "model": self._config.model,
                "prompt": prompt,
                "size": size,
                "quality": self._config.quality,
                "output_format": "png",
            },
            files=[
                {
                    "field": "image",
                    "filename": input_path.name,
                    "content_type": _content_type_for_image(input_path),
                    "data": input_path.read_bytes(),
                }
            ],
        )
        http_request = request.Request(
            _images_edits_url(self._config.base_url),
            data=body,
            headers={
                "Authorization": f"Bearer {self._config.api_key}",
                "Content-Type": f"multipart/form-data; boundary={boundary}",
            },
            method="POST",
        )
        try:
            with self._urlopen(  # nosec B310 - endpoint is configured server-side.
                http_request, timeout=self._config.timeout_seconds
            ) as response:
                raw = response.read().decode("utf-8")
        except error.HTTPError as exc:
            detail = exc.read(500).decode("utf-8", "replace").strip()
            suffix = f": {_safe_preview(detail)}" if detail else ""
            raise ProviderError(
                f"Image edit provider HTTP error: {exc.code}{suffix}"
            ) from exc
        except TimeoutError as exc:
            raise ProviderError(
                "Image edit provider request timed out after "
                f"{self._config.timeout_seconds:g}s; increase "
                "OPENAI_IMAGE_TIMEOUT_SECONDS for slow image edit providers"
            ) from exc
        except OSError as exc:
            raise ProviderError("Image edit provider request failed") from exc
        png_bytes = parse_image_generation_response(raw)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(png_bytes)


def image_client_from_env() -> ImageGenerationClient | None:
    """Return the configured image client, or None for deterministic local mode."""
    config = ImageGenerationConfig.from_env()
    provider = config.provider.lower()
    if provider == "mock":
        return None
    if provider in {"openai", "openai-compatible", "openai_compatible"}:
        return OpenAIImageGenerationClient(config)
    raise ProviderConfigurationError(f"Unsupported image provider: {config.provider}")


def parse_image_generation_response(raw: str) -> bytes:
    """Extract PNG bytes from an OpenAI image generation response."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ProviderError(
            f"Image provider returned invalid JSON: {_safe_preview(raw)}"
        ) from exc
    try:
        first_item = data["data"][0]
        encoded = first_item["b64_json"]
    except (KeyError, IndexError, TypeError) as exc:
        if _has_url_image_output(data):
            raise ProviderError(
                "Image provider returned an image URL instead of b64_json; "
                "this client currently requires base64 image data"
            ) from exc
        raise ProviderError(
            f"Image provider returned invalid JSON: {_safe_preview(raw)}"
        ) from exc
    if not isinstance(encoded, str) or not encoded.strip():
        raise ProviderError("Image provider returned empty image data")
    try:
        return base64.b64decode(encoded, validate=True)
    except ValueError as exc:
        raise ProviderError("Image provider returned invalid base64 image data") from exc


def _images_generations_url(base_url: str) -> str:
    trimmed = base_url.rstrip("/")
    if trimmed.endswith("/images/generations"):
        return trimmed
    for suffix in ("/chat/completions", "/responses"):
        if trimmed.endswith(suffix):
            trimmed = trimmed[: -len(suffix)]
    return f"{trimmed}/images/generations"


def _images_edits_url(base_url: str) -> str:
    trimmed = base_url.rstrip("/")
    if trimmed.endswith("/images/edits"):
        return trimmed
    for suffix in ("/chat/completions", "/responses", "/images/generations"):
        if trimmed.endswith(suffix):
            trimmed = trimmed[: -len(suffix)]
    return f"{trimmed}/images/edits"


def _multipart_form_data(
    *,
    boundary: str,
    fields: dict[str, str],
    files: list[dict[str, Any]],
) -> bytes:
    body = bytearray()
    for name, value in fields.items():
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8")
        )
        body.extend(str(value).encode("utf-8"))
        body.extend(b"\r\n")
    for file_item in files:
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(
            (
                'Content-Disposition: form-data; '
                f'name="{file_item["field"]}"; filename="{file_item["filename"]}"\r\n'
            ).encode("utf-8")
        )
        body.extend(
            f'Content-Type: {file_item["content_type"]}\r\n\r\n'.encode("utf-8")
        )
        body.extend(file_item["data"])
        body.extend(b"\r\n")
    body.extend(f"--{boundary}--\r\n".encode("utf-8"))
    return bytes(body)


def _content_type_for_image(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if suffix == ".webp":
        return "image/webp"
    return "image/png"


def _env_value(name: str, dotenv_values: dict[str, str], default: str) -> str:
    value = os.getenv(name)
    if value is None:
        value = dotenv_values.get(name, default)
    return value.strip()


def _load_nearest_dotenv() -> dict[str, str]:
    values: dict[str, str] = {}
    for directory in [Path.cwd(), *Path.cwd().parents]:
        env_path = directory / ".env"
        if not env_path.exists():
            continue
        for line in env_path.read_text().splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            values.setdefault(key.strip(), value.strip().strip('"').strip("'"))
    return values


def _safe_preview(content: str) -> str:
    return " ".join(content.strip().split())[:160]


def _has_url_image_output(data: Any) -> bool:
    if not isinstance(data, dict):
        return False
    items = data.get("data")
    if not isinstance(items, list) or not items:
        return False
    first_item = items[0]
    return isinstance(first_item, dict) and isinstance(first_item.get("url"), str)
