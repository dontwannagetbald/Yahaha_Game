import base64
import json
from pathlib import Path

import pytest

from agent.generation_graph.asset_agent.tools.image_model import (
    ImageGenerationConfig,
    OpenAIImageGenerationClient,
    parse_image_generation_response,
)
from agent.providers import ProviderError


PNG_BYTES = b"\x89PNG\r\n\x1a\nfake"


class FakeHTTPResponse:
    def __init__(self, payload: dict) -> None:
        self._raw = json.dumps(payload).encode("utf-8")

    def __enter__(self) -> "FakeHTTPResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def read(self) -> bytes:
        return self._raw


def test_parse_image_generation_response_decodes_b64_json() -> None:
    raw = json.dumps(
        {"data": [{"b64_json": base64.b64encode(PNG_BYTES).decode("ascii")}]}
    )

    assert parse_image_generation_response(raw) == PNG_BYTES


def test_parse_image_generation_response_includes_safe_preview_on_invalid_json() -> None:
    raw = json.dumps({"code": 99, "msg": "model does not support image generation"})

    with pytest.raises(ProviderError, match="model does not support image generation"):
        parse_image_generation_response(raw)


def test_parse_image_generation_response_explains_url_only_response() -> None:
    raw = json.dumps({"data": [{"url": "https://example.com/generated.png"}]})

    with pytest.raises(ProviderError, match="URL instead of b64_json"):
        parse_image_generation_response(raw)


def test_openai_image_generation_client_posts_fixed_size_payload(tmp_path: Path) -> None:
    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        captured["headers"] = dict(request.header_items())
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        return FakeHTTPResponse(
            {"data": [{"b64_json": base64.b64encode(PNG_BYTES).decode("ascii")}]}
        )

    client = OpenAIImageGenerationClient(
        ImageGenerationConfig(
            provider="openai-compatible",
            api_key="test-key",
            base_url="https://api.openai.com/v1",
            model="gpt-image-2",
            timeout_seconds=12,
        ),
        urlopen=fake_urlopen,
    )
    output_path = tmp_path / "generated.png"

    client.generate_png(prompt="draw a cat", size="1280x720", output_path=output_path)

    assert captured["url"] == "https://api.openai.com/v1/images/generations"
    assert captured["timeout"] == 12
    assert captured["headers"]["Authorization"] == "Bearer test-key"
    assert captured["payload"]["model"] == "gpt-image-2"
    assert captured["payload"]["prompt"] == "draw a cat"
    assert captured["payload"]["size"] == "1280x720"
    assert captured["payload"]["output_format"] == "png"
    assert "response_format" not in captured["payload"]
    assert output_path.read_bytes() == PNG_BYTES


def test_openai_image_generation_client_posts_image_edit_payload(tmp_path: Path) -> None:
    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        captured["headers"] = dict(request.header_items())
        captured["body"] = request.data
        return FakeHTTPResponse(
            {"data": [{"b64_json": base64.b64encode(PNG_BYTES).decode("ascii")}]}
        )

    client = OpenAIImageGenerationClient(
        ImageGenerationConfig(
            provider="openai-compatible",
            api_key="test-key",
            base_url="https://api.openai.com/v1",
            model="gpt-image-2",
            timeout_seconds=12,
        ),
        urlopen=fake_urlopen,
    )
    input_path = tmp_path / "reference.png"
    input_path.write_bytes(b"reference-png")
    output_path = tmp_path / "edited.png"

    client.edit_png(
        prompt="turn this into a game sprite",
        size="1024x1024",
        input_path=input_path,
        output_path=output_path,
    )

    body = captured["body"]
    assert captured["url"] == "https://api.openai.com/v1/images/edits"
    assert captured["timeout"] == 12
    assert captured["headers"]["Authorization"] == "Bearer test-key"
    assert "multipart/form-data" in captured["headers"]["Content-type"]
    assert b'name="model"' in body
    assert b"gpt-image-2" in body
    assert b'name="prompt"' in body
    assert b"turn this into a game sprite" in body
    assert b'name="size"' in body
    assert b"1024x1024" in body
    assert b'name="image"; filename="reference.png"' in body
    assert b"reference-png" in body
    assert output_path.read_bytes() == PNG_BYTES


def test_openai_image_generation_client_reports_timeout_with_hint(tmp_path: Path) -> None:
    def fake_urlopen(request, timeout):
        raise TimeoutError("The read operation timed out")

    client = OpenAIImageGenerationClient(
        ImageGenerationConfig(
            provider="openai-compatible",
            api_key="test-key",
            base_url="https://api.openai.com/v1",
            model="gpt-image-2",
            timeout_seconds=12,
        ),
        urlopen=fake_urlopen,
    )

    with pytest.raises(ProviderError, match="timed out|OPENAI_IMAGE_TIMEOUT_SECONDS"):
        client.generate_png(
            prompt="draw a cat",
            size="1280x720",
            output_path=tmp_path / "generated.png",
        )
