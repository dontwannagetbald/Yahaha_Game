import pytest
from urllib.error import HTTPError

from agent.providers.openai_compatible import (
    parse_chat_completion_response,
    parse_json_object_content,
    parse_responses_api_response,
)
from agent.providers import (
    LLMMessage,
    MockLLMProvider,
    OpenAICompatibleLLMProvider,
    ProviderConfig,
    ProviderConfigurationError,
    provider_from_config,
    ProviderError,
)


def test_mock_provider_returns_configured_json_response() -> None:
    provider = MockLLMProvider(
        response={
            "game_plan_patch": {"title": "星星小猫"},
            "suggestions": ["方向键移动"],
        }
    )

    response = provider.complete_json(
        messages=[LLMMessage(role="user", content="做一个小猫游戏")],
        response_schema={"type": "object"},
    )

    assert response["game_plan_patch"]["title"] == "星星小猫"
    assert response["suggestions"] == ["方向键移动"]


def test_provider_from_config_uses_mock_without_api_key() -> None:
    config = ProviderConfig(provider="mock")

    provider = provider_from_config(config)

    assert isinstance(provider, MockLLMProvider)


def test_openai_provider_requires_api_key_base_url_and_model() -> None:
    config = ProviderConfig(provider="openai-compatible")

    with pytest.raises(ProviderConfigurationError):
        OpenAICompatibleLLMProvider(config)


def test_provider_config_loads_dotenv_from_working_tree(
    tmp_path, monkeypatch
) -> None:
    project = tmp_path / "project"
    agents = project / "lan_agents"
    agents.mkdir(parents=True)
    (project / ".env").write_text(
        "\n".join(
            [
                "LLM_PROVIDER=openai-compatible",
                "OPENAI_COMPATIBLE_API_KEY=test-key",
                "OPENAI_COMPATIBLE_BASE_URL=https://llm.example/v1",
                "OPENAI_COMPATIBLE_MODEL=test-model",
            ]
        )
    )
    monkeypatch.chdir(agents)
    for name in [
        "LLM_PROVIDER",
        "OPENAI_COMPATIBLE_API_KEY",
        "OPENAI_COMPATIBLE_BASE_URL",
        "OPENAI_COMPATIBLE_MODEL",
    ]:
        monkeypatch.delenv(name, raising=False)

    config = ProviderConfig.from_env()

    assert config.provider == "openai-compatible"
    assert config.api_key == "test-key"
    assert config.base_url == "https://llm.example/v1"
    assert config.model == "test-model"


def test_parse_json_object_content_accepts_fenced_json() -> None:
    content = '```json\n{"ok": true, "stage": "generation_provider_smoke"}\n```'

    result = parse_json_object_content(content)

    assert result["ok"] is True
    assert result["stage"] == "generation_provider_smoke"


def test_parse_json_object_content_extracts_object_from_prefixed_text() -> None:
    content = 'Here is the JSON:\n{"ok": true, "summary": "ready"}'

    result = parse_json_object_content(content)

    assert result == {"ok": True, "summary": "ready"}


def test_parse_json_object_content_can_emit_debug_preview(monkeypatch) -> None:
    monkeypatch.setenv("LLM_DEBUG_INVALID_JSON_PREVIEW", "true")

    with pytest.raises(ProviderError, match="preview: not-json-response"):
        parse_json_object_content("not-json-response")


def test_parse_chat_completion_response_can_emit_debug_preview(monkeypatch) -> None:
    monkeypatch.setenv("LLM_DEBUG_INVALID_JSON_PREVIEW", "true")
    raw = '{"error":{"message":"model overloaded"}}'

    with pytest.raises(ProviderError, match="raw preview:"):
        parse_chat_completion_response(raw)


def test_openai_provider_uses_responses_api_for_reference_attachments(
    tmp_path, monkeypatch
) -> None:
    reference_file = tmp_path / "rules.md"
    reference_file.write_text("Rules: collect 10 stars before time runs out.")
    calls = []

    class FakeResponse:
        def __init__(self, body: str) -> None:
            self._body = body

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self, *_args):
            return self._body.encode("utf-8")

        def close(self):
            return None

    def fake_urlopen(http_request, timeout):
        calls.append(
            {
                "url": http_request.full_url,
                "method": http_request.get_method(),
                "data": http_request.data,
            }
        )
        if http_request.full_url.endswith("/files") and http_request.get_method() == "POST":
            return FakeResponse('{"id":"file-reference-123"}')
        if http_request.full_url.endswith("/responses"):
            return FakeResponse(
                '{"output":[{"content":[{"type":"output_text","text":"{\\"ok\\":true,\\"used\\":[\\"file-reference-123\\"]}"}]}]}'
            )
        if http_request.full_url.endswith("/files/file-reference-123") and (
            http_request.get_method() == "DELETE"
        ):
            return FakeResponse('{"deleted":true}')
        raise AssertionError(f"unexpected request {http_request.full_url}")

    monkeypatch.setattr("agent.providers.openai_compatible.request.urlopen", fake_urlopen)
    provider = OpenAICompatibleLLMProvider(
        ProviderConfig(
            provider="openai-compatible",
            api_key="test-key",
            base_url="https://api.openai.test/v1",
            model="gpt-test",
        )
    )

    result = provider.complete_json_with_attachments(
        messages=[LLMMessage(role="user", content="Build contracts")],
        response_schema={"type": "object"},
        attachments=[
            {
                "asset_id": "asset-rules-file",
                "filename": "rules.md",
                "mime_type": "text/markdown",
                "local_path": str(reference_file),
                "user_hint": "玩法说明",
            }
        ],
    )

    assert result == {"ok": True, "used": ["file-reference-123"]}
    assert [call["method"] for call in calls] == ["POST", "POST", "DELETE"]
    responses_payload = calls[1]["data"].decode("utf-8")
    assert '"type": "input_file"' in responses_payload
    assert '"file_id": "file-reference-123"' in responses_payload


def test_openai_provider_accepts_wrapped_file_upload_response(
    tmp_path, monkeypatch
) -> None:
    reference_file = tmp_path / "rules.md"
    reference_file.write_text("Rules: collect 10 stars before time runs out.")
    calls = []

    class FakeResponse:
        def __init__(self, body: str) -> None:
            self._body = body

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self, *_args):
            return self._body.encode("utf-8")

        def close(self):
            return None

    def fake_urlopen(http_request, timeout):
        calls.append({"url": http_request.full_url, "method": http_request.get_method()})
        if http_request.full_url.endswith("/files") and http_request.get_method() == "POST":
            return FakeResponse('{"code":0,"msg":"success","data":{"id":"file-wrapped-123"}}')
        if http_request.full_url.endswith("/responses"):
            return FakeResponse('{"output_text":"{\\"ok\\":true}"}')
        if http_request.full_url.endswith("/files/file-wrapped-123") and (
            http_request.get_method() == "DELETE"
        ):
            return FakeResponse('{"deleted":true}')
        raise AssertionError(f"unexpected request {http_request.full_url}")

    monkeypatch.setattr("agent.providers.openai_compatible.request.urlopen", fake_urlopen)
    provider = OpenAICompatibleLLMProvider(
        ProviderConfig(
            provider="openai-compatible",
            api_key="test-key",
            base_url="https://api.openai.test/v1",
            model="gpt-test",
        )
    )

    result = provider.complete_json_with_attachments(
        messages=[LLMMessage(role="user", content="Build contracts")],
        response_schema={"type": "object"},
        attachments=[
            {
                "asset_id": "asset-rules-file",
                "filename": "rules.md",
                "mime_type": "text/markdown",
                "local_path": str(reference_file),
                "user_hint": "玩法说明",
            }
        ],
    )

    assert result == {"ok": True}
    assert [call["method"] for call in calls] == ["POST", "POST", "DELETE"]


def test_openai_provider_file_upload_without_id_reports_response_preview(
    tmp_path, monkeypatch
) -> None:
    reference_file = tmp_path / "rules.md"
    reference_file.write_text("Rules: collect 10 stars before time runs out.")

    class FakeResponse:
        def __init__(self, body: str) -> None:
            self._body = body

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self, *_args):
            return self._body.encode("utf-8")

        def close(self):
            return None

    def fake_urlopen(http_request, timeout):
        if http_request.full_url.endswith("/files") and http_request.get_method() == "POST":
            return FakeResponse('{"code":0,"msg":"success","data":{}}')
        raise AssertionError(f"unexpected request {http_request.full_url}")

    monkeypatch.setattr("agent.providers.openai_compatible.request.urlopen", fake_urlopen)
    provider = OpenAICompatibleLLMProvider(
        ProviderConfig(
            provider="openai-compatible",
            api_key="test-key",
            base_url="https://api.openai.test/v1",
            model="gpt-test",
        )
    )

    with pytest.raises(ProviderError, match="empty file id.*code.*success"):
        provider.complete_json_with_attachments(
            messages=[LLMMessage(role="user", content="Build contracts")],
            response_schema={"type": "object"},
            attachments=[
                {
                    "asset_id": "asset-rules-file",
                    "filename": "rules.md",
                    "mime_type": "text/markdown",
                    "local_path": str(reference_file),
                    "user_hint": "玩法说明",
                }
            ],
        )


def test_openai_provider_retries_chat_completion_with_max_completion_tokens(
    monkeypatch,
) -> None:
    calls = []

    class FakeResponse:
        def __init__(self, body: str) -> None:
            self._body = body

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self, *_args):
            return self._body.encode("utf-8")

        def close(self):
            return None

    def fake_urlopen(http_request, timeout):
        payload = http_request.data.decode("utf-8")
        calls.append(payload)
        if len(calls) == 1:
            raise HTTPError(
                http_request.full_url,
                400,
                "Bad Request",
                hdrs=None,
                fp=FakeResponse(
                    '{"error":{"message":"Unsupported parameter: max_tokens is not supported with this model. Use max_completion_tokens instead."}}'
                ),
            )
        return FakeResponse(
            '{"choices":[{"message":{"content":"{\\"ok\\":true,\\"retry\\":\\"max_completion_tokens\\"}"}}]}'
        )

    monkeypatch.setattr("agent.providers.openai_compatible.request.urlopen", fake_urlopen)
    provider = OpenAICompatibleLLMProvider(
        ProviderConfig(
            provider="openai-compatible",
            api_key="test-key",
            base_url="https://api.openai.test/v1",
            model="gpt-test",
        )
    )

    result = provider.complete_json(
        messages=[LLMMessage(role="user", content="Build contracts")],
        response_schema={"type": "object"},
        max_tokens=777,
    )

    assert result == {"ok": True, "retry": "max_completion_tokens"}
    first_payload = calls[0]
    second_payload = calls[1]
    assert '"max_tokens": 777' in first_payload
    assert '"max_completion_tokens": 777' in second_payload
    assert '"max_tokens"' not in second_payload


def test_parse_responses_api_response_reads_output_text() -> None:
    raw = (
        '{"output":[{"content":[{"type":"output_text",'
        '"text":"{\\"ok\\":true,\\"stage\\":\\"responses\\"}"}]}]}'
    )

    result = parse_responses_api_response(raw)

    assert result == {"ok": True, "stage": "responses"}
