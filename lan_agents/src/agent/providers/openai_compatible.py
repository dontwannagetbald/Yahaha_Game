"""OpenAI-compatible JSON provider implemented with the stdlib HTTP client."""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Any
from urllib import error, request

from agent.providers.base import (
    LLMMessage,
    ProviderConfig,
    ProviderConfigurationError,
    ProviderError,
)


class OpenAICompatibleLLMProvider:
    """Call an OpenAI-compatible chat completions endpoint."""

    def __init__(self, config: ProviderConfig) -> None:
        missing = []
        if not config.api_key:
            missing.append("OPENAI_COMPATIBLE_API_KEY")
        if not config.base_url:
            missing.append("OPENAI_COMPATIBLE_BASE_URL")
        if not config.model:
            missing.append("OPENAI_COMPATIBLE_MODEL")
        if missing:
            raise ProviderConfigurationError(
                f"Missing LLM provider configuration: {', '.join(missing)}"
            )
        self._config = config

    def complete_json(
        self,
        *,
        messages: list[LLMMessage],
        response_schema: dict[str, Any],
        temperature: float = 0.2,
        max_tokens: int = 1200,
    ) -> dict[str, Any]:
        """Return a JSON object from `/chat/completions`."""
        payload = {
            "model": self._config.model,
            "messages": [
                {"role": message.role, "content": message.content}
                for message in messages
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
        }
        endpoint = self._chat_completions_url(self._config.base_url)
        try:
            raw = self._post_json(endpoint, payload, "LLM provider HTTP error")
        except ProviderError as exc:
            if not _requests_max_completion_tokens(str(exc)):
                raise
            retry_payload = dict(payload)
            retry_payload["max_completion_tokens"] = retry_payload.pop("max_tokens")
            raw = self._post_json(endpoint, retry_payload, "LLM provider HTTP error")
        except OSError as exc:
            raise ProviderError("LLM provider request failed") from exc

        result = parse_chat_completion_response(raw)
        if not isinstance(result, dict):
            raise ProviderError("LLM provider JSON response must be an object")
        return result

    def complete_json_with_attachments(
        self,
        *,
        messages: list[LLMMessage],
        response_schema: dict[str, Any],
        attachments: list[dict[str, Any]],
        temperature: float = 0.2,
        max_tokens: int = 1200,
    ) -> dict[str, Any]:
        """Return a JSON object using temporary file references via Responses API."""
        if not attachments:
            return self.complete_json(
                messages=messages,
                response_schema=response_schema,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        uploaded_file_ids: list[str] = []
        try:
            for attachment in attachments:
                uploaded_file_ids.append(self._upload_reference_attachment(attachment))
            payload = {
                "model": self._config.model,
                "input": _responses_input_from_messages(messages, uploaded_file_ids),
                "temperature": temperature,
                "max_output_tokens": max_tokens,
                "text": {"format": {"type": "json_object"}},
            }
            http_request = request.Request(
                self._responses_url(self._config.base_url),
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {self._config.api_key}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            try:
                with request.urlopen(  # nosec B310 - endpoint is configured server-side.
                    http_request, timeout=self._config.timeout_seconds
                ) as response:
                    raw = response.read().decode("utf-8")
            except error.HTTPError as exc:
                detail = exc.read(500).decode("utf-8", "replace").strip()
                suffix = f": {_safe_preview(detail)}" if detail else ""
                raise ProviderError(
                    f"LLM provider Responses API HTTP error: {exc.code}{suffix}"
                ) from exc
            except OSError as exc:
                raise ProviderError("LLM provider Responses API request failed") from exc
            return parse_responses_api_response(raw)
        finally:
            for file_id in uploaded_file_ids:
                self._delete_uploaded_file(file_id)

    def _post_json(self, endpoint: str, payload: dict[str, Any], error_prefix: str) -> str:
        http_request = request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self._config.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with request.urlopen(  # nosec B310 - endpoint is configured server-side.
                http_request, timeout=self._config.timeout_seconds
            ) as response:
                return response.read().decode("utf-8")
        except error.HTTPError as exc:
            detail = exc.read(500).decode("utf-8", "replace").strip()
            suffix = f": {_safe_preview(detail)}" if detail else ""
            raise ProviderError(f"{error_prefix}: {exc.code}{suffix}") from exc

    def _upload_reference_attachment(self, attachment: dict[str, Any]) -> str:
        local_path = str(attachment.get("local_path") or "").strip()
        if not local_path:
            raise ProviderError("Reference attachment local_path is required")
        path = Path(local_path)
        if not path.is_file():
            raise ProviderError("Reference attachment file is not readable")
        filename = str(attachment.get("filename") or path.name).strip() or path.name
        content_type = str(attachment.get("mime_type") or "application/octet-stream").strip()
        boundary = f"----yahaha-{uuid.uuid4().hex}"
        body = _multipart_form_data(
            boundary=boundary,
            fields={"purpose": "user_data"},
            files=[
                {
                    "field": "file",
                    "filename": filename,
                    "content_type": content_type,
                    "data": path.read_bytes(),
                }
            ],
        )
        http_request = request.Request(
            self._files_url(self._config.base_url),
            data=body,
            headers={
                "Authorization": f"Bearer {self._config.api_key}",
                "Content-Type": f"multipart/form-data; boundary={boundary}",
            },
            method="POST",
        )
        try:
            with request.urlopen(  # nosec B310 - endpoint is configured server-side.
                http_request, timeout=self._config.timeout_seconds
            ) as response:
                raw = response.read().decode("utf-8")
        except error.HTTPError as exc:
            detail = exc.read(500).decode("utf-8", "replace").strip()
            suffix = f": {_safe_preview(detail)}" if detail else ""
            raise ProviderError(f"LLM provider file upload HTTP error: {exc.code}{suffix}") from exc
        except OSError as exc:
            raise ProviderError("LLM provider file upload failed") from exc
        try:
            file_id = _extract_uploaded_file_id(json.loads(raw))
        except (TypeError, json.JSONDecodeError) as exc:
            raise ProviderError(
                f"LLM provider file upload returned invalid JSON: {_safe_preview(raw)}"
            ) from exc
        if not isinstance(file_id, str) or not file_id.strip():
            raise ProviderError(
                f"LLM provider file upload returned empty file id: {_safe_preview(raw)}"
            )
        return file_id.strip()

    def _delete_uploaded_file(self, file_id: str) -> None:
        http_request = request.Request(
            f"{self._files_url(self._config.base_url)}/{file_id}",
            headers={"Authorization": f"Bearer {self._config.api_key}"},
            method="DELETE",
        )
        try:
            with request.urlopen(  # nosec B310 - endpoint is configured server-side.
                http_request, timeout=self._config.timeout_seconds
            ):
                return
        except Exception:
            return

    @staticmethod
    def _chat_completions_url(base_url: str) -> str:
        trimmed = base_url.rstrip("/")
        if trimmed.endswith("/chat/completions"):
            return trimmed
        return f"{trimmed}/chat/completions"

    @staticmethod
    def _responses_url(base_url: str) -> str:
        trimmed = base_url.rstrip("/")
        if trimmed.endswith("/responses"):
            return trimmed
        if trimmed.endswith("/chat/completions"):
            trimmed = trimmed[: -len("/chat/completions")]
        return f"{trimmed}/responses"

    @staticmethod
    def _files_url(base_url: str) -> str:
        trimmed = base_url.rstrip("/")
        for suffix in ("/chat/completions", "/responses"):
            if trimmed.endswith(suffix):
                trimmed = trimmed[: -len(suffix)]
        return f"{trimmed}/files"


def parse_chat_completion_response(raw: str) -> dict[str, Any]:
    """Parse an OpenAI-compatible chat completion envelope into a JSON object."""
    try:
        data = json.loads(raw)
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        if os.getenv("LLM_DEBUG_INVALID_JSON_PREVIEW", "").lower() == "true":
            raise ProviderError(
                f"LLM provider returned invalid JSON raw preview: {_safe_preview(raw)}"
            ) from exc
        raise ProviderError("LLM provider returned invalid JSON") from exc
    if not isinstance(content, str):
        raise ProviderError("LLM provider JSON content must be a string")
    return parse_json_object_content(content)


def _extract_uploaded_file_id(data: Any) -> str:
    if not isinstance(data, dict):
        return ""
    for key in ("id", "file_id"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    nested = data.get("data")
    if isinstance(nested, dict):
        for key in ("id", "file_id"):
            value = nested.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return ""


def parse_responses_api_response(raw: str) -> dict[str, Any]:
    """Parse an OpenAI Responses API envelope into a JSON object."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ProviderError("LLM provider returned invalid Responses API JSON") from exc
    output_text = data.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return parse_json_object_content(output_text)
    output = data.get("output")
    if isinstance(output, list):
        for item in output:
            if not isinstance(item, dict):
                continue
            content = item.get("content")
            if not isinstance(content, list):
                continue
            for part in content:
                if not isinstance(part, dict):
                    continue
                if part.get("type") in {"output_text", "text"} and isinstance(
                    part.get("text"), str
                ):
                    return parse_json_object_content(part["text"])
    if os.getenv("LLM_DEBUG_INVALID_JSON_PREVIEW", "").lower() == "true":
        raise ProviderError(
            f"LLM provider returned invalid Responses API preview: {_safe_preview(raw)}"
        )
    raise ProviderError("LLM provider returned invalid Responses API output")


def _responses_input_from_messages(
    messages: list[LLMMessage], file_ids: list[str]
) -> list[dict[str, Any]]:
    result = [
        {
            "role": message.role,
            "content": [{"type": "input_text", "text": message.content}],
        }
        for message in messages
    ]
    if file_ids:
        result.append(
            {
                "role": "user",
                "content": [
                    {"type": "input_file", "file_id": file_id}
                    for file_id in file_ids
                ],
            }
        )
    return result


def _multipart_form_data(
    *,
    boundary: str,
    fields: dict[str, str],
    files: list[dict[str, Any]],
) -> bytes:
    chunks: list[bytes] = []
    for key, value in fields.items():
        chunks.extend(
            [
                f"--{boundary}\r\n".encode("utf-8"),
                f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode("utf-8"),
                str(value).encode("utf-8"),
                b"\r\n",
            ]
        )
    for file_item in files:
        chunks.extend(
            [
                f"--{boundary}\r\n".encode("utf-8"),
                (
                    'Content-Disposition: form-data; '
                    f'name="{file_item["field"]}"; filename="{file_item["filename"]}"\r\n'
                ).encode("utf-8"),
                f'Content-Type: {file_item["content_type"]}\r\n\r\n'.encode("utf-8"),
                file_item["data"],
                b"\r\n",
            ]
        )
    chunks.append(f"--{boundary}--\r\n".encode("utf-8"))
    return b"".join(chunks)


def parse_json_object_content(content: str) -> dict[str, Any]:
    """Parse a JSON object from strict JSON, fenced JSON, or prefixed text."""
    stripped = content.strip()
    if stripped.startswith("```"):
        stripped = _strip_markdown_fence(stripped)
    try:
        result = json.loads(stripped)
    except json.JSONDecodeError:
        result = _extract_first_json_object(stripped)
    if not isinstance(result, dict):
        raise ProviderError("LLM provider JSON response must be an object")
    return result


def _strip_markdown_fence(content: str) -> str:
    lines = content.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


def _extract_first_json_object(content: str) -> dict[str, Any]:
    decoder = json.JSONDecoder()
    for index, char in enumerate(content):
        if char != "{":
            continue
        try:
            result, _ = decoder.raw_decode(content[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(result, dict):
            return result
    if os.getenv("LLM_DEBUG_INVALID_JSON_PREVIEW", "").lower() == "true":
        raise ProviderError(
            f"LLM provider returned invalid JSON preview: {_safe_preview(content)}"
        )
    raise ProviderError("LLM provider returned invalid JSON")


def _safe_preview(content: str) -> str:
    return " ".join(content.strip().split())[:160]


def _requests_max_completion_tokens(message: str) -> bool:
    normalized = message.lower()
    return (
        "max_completion_tokens" in normalized
        and "max_tokens" in normalized
        and "unsupported parameter" in normalized
    )
