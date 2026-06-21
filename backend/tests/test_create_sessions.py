from __future__ import annotations

import asyncio
import uuid

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db import get_session as app_get_session
from app.main import app
from app.models import (
    Base,
    CreateSession,
    CreateSessionMessage,
    GenerationJob,
    UploadedAsset,
)


class FakeConversationGraph:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def ainvoke(self, state: dict) -> dict:
        self.calls.append(state)
        user_event = state.get("user_event", {})
        event_type = user_event.get("type")
        is_confirm = event_type == "confirm"
        is_regenerate = event_type == "regenerate"
        plan_id = (
            f"plan-from-fake-graph-{len(self.calls)}"
            if event_type == "regenerate"
            else "plan-from-fake-graph"
        )
        material_usage = state.get("material_usage") or {"assets": []}
        if event_type == "upload_assets":
            material_usage = {"assets": user_event.get("uploaded_assets") or []}
        game_plan = {
            "plan_id": plan_id,
            "title": "真实图方案 Remix" if is_regenerate else "真实图方案",
            "introduction": (
                "来自 fake graph 的另一版介绍"
                if is_regenerate
                else "来自 fake graph 的介绍"
            ),
            "tags": ["casual"],
            "gameplay": user_event.get("message") or "图负责更新玩法",
            "core_loop": ["对话", "确认"],
            "style": "亲和温暖",
            "characters": ["设计助手"],
            "win_condition": "用户确认方案",
            "lose_condition": "用户继续修改",
            "controls": "点击建议或继续输入",
        }
        if event_type == "upload_assets":
            game_plan = state.get("game_plan") or game_plan
        return {
            **state,
            "conversation_status": "confirmed" if is_confirm else "ready_to_confirm",
            "user_requirements": {
                "intent_summary": user_event.get("message")
                or "fake graph understood user intent",
                "must_have": ["真实图调用"],
                "constraints": [],
            },
            "game_plan": game_plan,
            "material_usage": material_usage,
            "assistant_response": {
                "message": "fake graph 已确认方案" if is_confirm else "来自 fake graph 的亲和回复",
                "suggestions": ["更轻松", "更可爱"],
                "card": {
                    "plan_id": plan_id,
                    "title": "真实图方案 Remix" if is_regenerate else "真实图方案",
                    "introduction": (
                        "来自 fake graph 的另一版介绍"
                        if is_regenerate
                        else "来自 fake graph 的介绍"
                    ),
                    "tags": ["casual"],
                },
                "actions": ["generate"] if is_confirm else ["generate", "regenerate"],
            },
            "handoff_to_generation": is_confirm,
        }


class FailingConversationGraph:
    async def ainvoke(self, state: dict) -> dict:
        raise RuntimeError("模型没有返回可点击建议，请重试。")


class DetailedFailingConversationGraph:
    async def ainvoke(self, state: dict) -> dict:
        error = RuntimeError("模型没有返回可点击建议，请重试。")
        error.details = {
            "reason": "provider_exception",
            "missing_fields": ["title"],
            "provider_error": "empty suggestions",
        }
        raise error


class SilentUploadConversationGraph(FakeConversationGraph):
    async def ainvoke(self, state: dict) -> dict:
        result = await super().ainvoke(state)
        if state.get("user_event", {}).get("type") == "upload_assets":
            result["conversation_status"] = state.get("conversation_status", "collecting")
            result["assistant_response"] = {
                "message": "",
                "suggestions": [],
                "card": None,
                "actions": [],
            }
        return result


@pytest_asyncio.fixture()
async def session_factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        yield factory
    finally:
        await engine.dispose()


@pytest.fixture()
def client(session_factory, monkeypatch: pytest.MonkeyPatch):
    import app.conversation_runner as runner_module

    monkeypatch.setattr(
        runner_module, "get_conversation_graph", lambda: FakeConversationGraph()
    )

    async def override_get_session():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[app_get_session] = override_get_session
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def login(client: TestClient, email: str) -> None:
    response = client.post(
        "/api/auth/register",
        json={"email": email, "password": "password123"},
    )
    assert response.status_code == 201


def create_asset(client: TestClient, filename: str = "asset.png") -> str:
    presign = client.post(
        "/api/uploads/presign",
        json={"filename": filename, "mime_type": "image/png", "size_bytes": 1024},
    )
    assert presign.status_code == 200
    body = presign.json()
    complete = client.post(
        "/api/uploads/complete",
        json={
            "upload_id": body["upload_id"],
            "object_key": body["object_key"],
            "filename": filename,
            "mime_type": "image/png",
            "size_bytes": 1024,
        },
    )
    assert complete.status_code == 200
    return complete.json()["asset_id"]


def assert_card_is_projection(card: dict, game_plan: dict) -> None:
    assert set(card.keys()) == {"plan_id", "title", "introduction", "tags"}
    assert card["plan_id"] == game_plan["plan_id"]
    assert card["title"] == game_plan["title"]
    assert card["introduction"] == game_plan["introduction"]
    assert card["tags"] == game_plan["tags"]


def assert_messages_are_ordered(messages: list[dict]) -> None:
    assert messages == sorted(messages, key=lambda item: item["created_at"])


def test_create_session_requires_login(client: TestClient):
    response = client.post("/api/create-sessions", json={})

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"


def test_create_session_uses_configured_conversation_graph(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
):
    import app.conversation_runner as runner_module

    fake_graph = FakeConversationGraph()
    monkeypatch.setattr(runner_module, "get_conversation_graph", lambda: fake_graph)
    login(client, "creator@example.com")

    response = client.post(
        "/api/create-sessions",
        json={"initial_message": "请真实设计一个轻松猫咪游戏"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["assistant_response"]["message"] == "来自 fake graph 的亲和回复"
    assert body["game_plan"]["plan_id"] == "plan-from-fake-graph"
    assert fake_graph.calls[0]["user_event"] == {
        "type": "chat",
        "message": "请真实设计一个轻松猫咪游戏",
    }
    assert fake_graph.calls[0]["user_requirements"]["intent_summary"] == ""


def test_empty_create_session_starts_blank_conversation_without_invalid_event(
    client: TestClient, session_factory
):
    login(client, "blank@example.com")

    response = client.post("/api/create-sessions", json={})

    assert response.status_code == 201
    body = response.json()
    assert body["conversation_status"] == "collecting"
    assert body["assistant_response"]["message"] == "您好呀，今天想要尝试做个什么样的游戏呢✨🧙‍♀️？"
    assert body["assistant_response"]["suggestions"] == []
    assert [message["role"] for message in body["messages"]] == ["assistant"]
    assert body["messages"][0]["content"] == "您好呀，今天想要尝试做个什么样的游戏呢✨🧙‍♀️？"
    assert body["messages"][0]["payload"]["event_type"] == "assistant_response"

    async def inspect() -> None:
        async with session_factory() as session:
            create_session = (
                await session.execute(select(CreateSession))
            ).scalar_one()
            messages = (
                await session.execute(select(CreateSessionMessage))
            ).scalars().all()
            assert create_session.status == "collecting"
            assert [message.role for message in messages] == ["assistant"]
            assert messages[0].content == "您好呀，今天想要尝试做个什么样的游戏呢✨🧙‍♀️？"

    asyncio.run(inspect())


def test_chat_event_uses_configured_conversation_graph(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
):
    import app.conversation_runner as runner_module

    fake_graph = FakeConversationGraph()
    monkeypatch.setattr(runner_module, "get_conversation_graph", lambda: fake_graph)
    login(client, "creator@example.com")
    created = client.post(
        "/api/create-sessions",
        json={"initial_message": "先做一个初版"},
    )
    session_id = created.json()["session_id"]

    response = client.post(
        f"/api/create-sessions/{session_id}/events",
        json={"type": "chat", "message": "再加入星星收集"},
    )

    assert response.status_code == 200
    assert response.json()["assistant_response"]["message"] == "来自 fake graph 的亲和回复"
    assert fake_graph.calls[-1]["user_event"] == {
        "type": "chat",
        "message": "再加入星星收集",
    }
    assert fake_graph.calls[-1]["game_plan"]["plan_id"] == "plan-from-fake-graph"
    assert [item["role"] for item in fake_graph.calls[-1]["conversation_history"]] == [
        "user",
        "assistant",
    ]
    assert fake_graph.calls[-1]["conversation_history"][0]["content"] == "先做一个初版"
    assert fake_graph.calls[-1]["conversation_history"][1]["content"] == "来自 fake graph 的亲和回复"


def test_chat_event_returns_json_error_when_conversation_graph_fails(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
):
    import app.conversation_runner as runner_module

    fake_graph = FakeConversationGraph()
    monkeypatch.setattr(runner_module, "get_conversation_graph", lambda: fake_graph)
    login(client, "graph-error@example.com")
    created = client.post(
        "/api/create-sessions",
        json={"initial_message": "先做一个初版"},
    )
    session_id = created.json()["session_id"]
    monkeypatch.setattr(
        runner_module, "get_conversation_graph", lambda: FailingConversationGraph()
    )

    response = client.post(
        f"/api/create-sessions/{session_id}/events",
        json={"type": "chat", "message": "继续"},
    )

    assert response.status_code == 502
    assert response.json()["error"]["message"] == "模型没有返回可点击建议，请重试。"


def test_create_session_event_surfaces_structured_provider_error_details(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
):
    import app.conversation_runner as runner_module

    fake_graph = FakeConversationGraph()
    monkeypatch.setattr(runner_module, "get_conversation_graph", lambda: fake_graph)
    login(client, "graph-error-detail@example.com")
    created = client.post(
        "/api/create-sessions",
        json={"initial_message": "先做一个初版"},
    )
    session_id = created.json()["session_id"]
    monkeypatch.setattr(
        runner_module, "get_conversation_graph", lambda: DetailedFailingConversationGraph()
    )

    response = client.post(
        f"/api/create-sessions/{session_id}/events",
        json={"type": "chat", "message": "继续"},
    )

    body = response.json()
    assert response.status_code == 502
    assert body["error"]["message"] == "模型没有返回可点击建议，请重试。"
    assert body["error"]["retry_hint"] == "请稍后重试。"
    assert body["error"]["details"] == {
        "reason": "provider_exception",
        "missing_fields": ["title"],
        "provider_error": "empty suggestions",
    }


def test_create_session_initial_message_and_asset_binding(
    client: TestClient, session_factory
):
    login(client, "creator@example.com")
    asset_id = create_asset(client)

    response = client.post(
        "/api/create-sessions",
        json={
            "initial_message": "做一个霓虹猫躲避激光的街机游戏",
            "asset_ids": [asset_id],
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["session_id"]
    assert body["conversation_status"] in {"collecting", "ready_to_confirm"}
    assert body["user_requirements"]["intent_summary"]
    assert "message" in body["assistant_response"]
    assert body["material_usage"]["assets"][0]["asset_id"] == asset_id
    assert isinstance(body["assistant_response"]["suggestions"], list)
    assert all(isinstance(item, str) for item in body["assistant_response"]["suggestions"])
    if body["assistant_response"]["card"]:
        assert_card_is_projection(body["assistant_response"]["card"], body["game_plan"])

    async def inspect() -> None:
        async with session_factory() as session:
            create_session = (
                await session.execute(select(CreateSession))
            ).scalar_one()
            asset = await session.get(UploadedAsset, uuid.UUID(asset_id))
            assert create_session.status in {"collecting", "ready_to_confirm"}
            assert asset.session_id == create_session.id
            assert asset.job_id is None

    asyncio.run(inspect())


def test_create_session_with_initial_message_writes_session_messages(
    client: TestClient, session_factory
):
    login(client, "creator@example.com")

    response = client.post(
        "/api/create-sessions",
        json={"initial_message": "做一个月球兔子跑酷"},
    )

    assert response.status_code == 201
    body = response.json()
    assert "messages" in body
    assert [message["role"] for message in body["messages"]] == ["user", "assistant"]
    assert body["messages"][0]["content"] == "做一个月球兔子跑酷"
    assert body["messages"][0]["payload"]["event_type"] == "chat"
    assert body["messages"][1]["content"] == body["assistant_response"]["message"]
    assert body["messages"][1]["payload"]["suggestions"] == body["assistant_response"]["suggestions"]
    assert body["messages"][1]["payload"]["card"] == body["assistant_response"]["card"]
    assert_messages_are_ordered(body["messages"])

    async def inspect() -> None:
        async with session_factory() as session:
            messages = (
                await session.execute(
                    select(CreateSessionMessage).order_by(CreateSessionMessage.created_at)
                )
            ).scalars().all()
            assert [message.role for message in messages] == ["user", "assistant"]
            assert messages[0].content == "做一个月球兔子跑酷"

    asyncio.run(inspect())


def test_create_session_rejects_cross_user_assets(client: TestClient):
    login(client, "owner@example.com")
    asset_id = create_asset(client)
    client.post("/api/auth/logout")
    login(client, "other@example.com")

    response = client.post(
        "/api/create-sessions",
        json={"initial_message": "偷素材", "asset_ids": [asset_id]},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "forbidden"


def test_event_permissions_and_validation(client: TestClient):
    login(client, "owner@example.com")
    created = client.post(
        "/api/create-sessions", json={"initial_message": "做一个太空跑酷"}
    )
    session_id = created.json()["session_id"]

    invalid = client.post(
        f"/api/create-sessions/{session_id}/events",
        json={"type": "unknown"},
    )
    missing_message = client.post(
        f"/api/create-sessions/{session_id}/events",
        json={"type": "chat"},
    )
    client.post("/api/auth/logout")
    login(client, "viewer@example.com")
    forbidden = client.post(
        f"/api/create-sessions/{session_id}/events",
        json={"type": "regenerate"},
    )

    assert invalid.status_code == 400
    assert missing_message.status_code in {400, 422}
    assert forbidden.status_code in {403, 404}
    assert "X-Amz-Signature" not in str(invalid.json())


def test_chat_event_updates_state_and_returns_short_contextual_suggestions(
    client: TestClient,
):
    login(client, "creator@example.com")
    created = client.post(
        "/api/create-sessions",
        json={"initial_message": "做一个猫咪冒险游戏"},
    )
    session_id = created.json()["session_id"]

    response = client.post(
        f"/api/create-sessions/{session_id}/events",
        json={"type": "chat", "message": "加入收集鱼干和躲避狗狗"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["conversation_status"] in {"collecting", "ready_to_confirm"}
    assert "鱼干" in str(body["user_requirements"]) or "鱼干" in str(body["game_plan"])
    assert body["material_usage"] == {"assets": []}
    assert isinstance(body["assistant_response"]["suggestions"], list)
    assert all(isinstance(item, str) for item in body["assistant_response"]["suggestions"])
    if body["assistant_response"]["card"]:
        assert_card_is_projection(body["assistant_response"]["card"], body["game_plan"])


def test_chat_event_appends_session_messages(client: TestClient):
    login(client, "creator@example.com")
    created = client.post(
        "/api/create-sessions",
        json={"initial_message": "做一个猫咪冒险游戏"},
    )
    session_id = created.json()["session_id"]

    response = client.post(
        f"/api/create-sessions/{session_id}/events",
        json={"type": "chat", "message": "加入收集鱼干和躲避狗狗"},
    )

    assert response.status_code == 200
    body = response.json()
    assert [message["role"] for message in body["messages"]] == [
        "user",
        "assistant",
        "user",
        "assistant",
    ]
    assert body["messages"][-2]["content"] == "加入收集鱼干和躲避狗狗"
    assert body["messages"][-2]["payload"]["event_type"] == "chat"
    assert body["messages"][-1]["content"] == body["assistant_response"]["message"]
    assert body["messages"][-1]["payload"]["event_type"] == "assistant_response"
    assert_messages_are_ordered(body["messages"])


def test_upload_assets_event_only_updates_material_usage_assets(
    client: TestClient, session_factory
):
    login(client, "creator@example.com")
    asset_id = create_asset(client, "cat.png")
    created = client.post(
        "/api/create-sessions",
        json={"initial_message": "做一个猫咪平台跳跃"},
    )
    session_id = created.json()["session_id"]
    before_plan = created.json()["game_plan"]

    response = client.post(
        f"/api/create-sessions/{session_id}/events",
        json={
            "type": "upload_assets",
            "uploaded_assets": [
                {
                    "asset_id": asset_id,
                    "filename": "cat.png",
                    "mime_type": "image/png",
                    "size_bytes": 1024,
                    "object_key": "uploads/hidden/X-Amz-Signature=secret",
                    "user_hint": "当主角参考",
                }
            ],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["game_plan"] == before_plan
    assert set(body["material_usage"].keys()) == {"assets"}
    assert body["material_usage"]["assets"][0]["asset_id"] == asset_id
    assert "X-Amz-Signature" not in str(body)

    async def inspect() -> None:
        async with session_factory() as session:
            assert (await session.execute(select(GenerationJob))).scalars().all() == []
            asset = await session.get(UploadedAsset, uuid.UUID(asset_id))
            assert str(asset.session_id) == session_id

    asyncio.run(inspect())


def test_upload_assets_event_does_not_append_empty_assistant_message(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
):
    import app.conversation_runner as runner_module

    fake_graph = SilentUploadConversationGraph()
    monkeypatch.setattr(runner_module, "get_conversation_graph", lambda: fake_graph)
    login(client, "silent-upload@example.com")
    asset_id = create_asset(client, "screenshot.png")
    created = client.post("/api/create-sessions", json={})
    session_id = created.json()["session_id"]

    response = client.post(
        f"/api/create-sessions/{session_id}/events",
        json={
            "type": "upload_assets",
            "uploaded_assets": [
                {"asset_id": asset_id, "filename": "screenshot.png", "user_hint": "参考画面"}
            ],
        },
    )

    assert response.status_code == 200
    messages = response.json()["messages"]
    assert [message["payload"]["event_type"] for message in messages] == [
        "assistant_response",
        "upload_assets",
    ]
    assert messages[-1]["role"] == "system"
    assert messages[-1]["content"] == "上传素材：screenshot.png"


def test_non_chat_events_append_reviewable_session_messages(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
):
    import app.conversation_runner as runner_module

    fake_graph = FakeConversationGraph()
    monkeypatch.setattr(runner_module, "get_conversation_graph", lambda: fake_graph)
    login(client, "creator@example.com")
    asset_id = create_asset(client, "cat.png")
    created = client.post(
        "/api/create-sessions",
        json={"initial_message": "做一个猫咪平台跳跃"},
    )
    session_id = created.json()["session_id"]

    upload = client.post(
        f"/api/create-sessions/{session_id}/events",
        json={
            "type": "upload_assets",
            "uploaded_assets": [
                {"asset_id": asset_id, "filename": "cat.png", "user_hint": "当主角"}
            ],
        },
    )
    regenerate = client.post(
        f"/api/create-sessions/{session_id}/events",
        json={"type": "regenerate", "selected_plan_id": created.json()["game_plan"]["plan_id"]},
    )
    confirm = client.post(
        f"/api/create-sessions/{session_id}/events",
        json={"type": "confirm", "selected_plan_id": regenerate.json()["game_plan"]["plan_id"]},
    )

    assert upload.status_code == 200
    assert regenerate.status_code == 200
    assert confirm.status_code == 200
    messages = confirm.json()["messages"]
    event_types = [message["payload"].get("event_type") for message in messages]
    assert "upload_assets" in event_types
    assert "regenerate" in event_types
    assert "confirm" in event_types
    assert event_types[-1] == "assistant_response"
    assert_messages_are_ordered(messages)


def test_regenerate_preserves_requirements_and_material_usage(client: TestClient):
    login(client, "creator@example.com")
    asset_id = create_asset(client, "robot.png")
    created = client.post(
        "/api/create-sessions",
        json={
            "initial_message": "做一个机器人生存游戏",
            "asset_ids": [asset_id],
        },
    )
    before = created.json()

    response = client.post(
        f"/api/create-sessions/{before['session_id']}/events",
        json={"type": "regenerate", "selected_plan_id": before["game_plan"]["plan_id"]},
    )

    assert response.status_code == 200
    after = response.json()
    assert after["game_plan"]["plan_id"] != before["game_plan"]["plan_id"]
    assert after["game_plan"]["title"] != before["game_plan"]["title"]
    assert after["game_plan"]["introduction"] != before["game_plan"]["introduction"]
    assert after["user_requirements"]["must_have"] == before["user_requirements"]["must_have"]
    assert after["user_requirements"]["constraints"] == before["user_requirements"]["constraints"]
    assert after["material_usage"]["assets"] == before["material_usage"]["assets"]
    assert_card_is_projection(after["assistant_response"]["card"], after["game_plan"])


def test_confirm_marks_session_without_creating_generation_job(
    client: TestClient, session_factory, monkeypatch: pytest.MonkeyPatch
):
    import app.conversation_runner as runner_module

    fake_graph = FakeConversationGraph()
    monkeypatch.setattr(runner_module, "get_conversation_graph", lambda: fake_graph)
    login(client, "creator@example.com")
    asset_id = create_asset(client)
    created = client.post(
        "/api/create-sessions",
        json={
            "initial_message": "做一个动作街机游戏",
            "asset_ids": [asset_id],
        },
    )
    session_id = created.json()["session_id"]

    response = client.post(
        f"/api/create-sessions/{session_id}/events",
        json={"type": "confirm", "selected_plan_id": created.json()["game_plan"]["plan_id"]},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["conversation_status"] == "confirmed"
    assert body["handoff_to_generation"] is True

    async def inspect() -> None:
        async with session_factory() as session:
            create_session = await session.get(CreateSession, uuid.UUID(session_id))
            jobs = (await session.execute(select(GenerationJob))).scalars().all()
            assert create_session.status == "confirmed"
            assert create_session.confirmed_at is not None
            assert jobs == []

    asyncio.run(inspect())


def test_get_session_restores_owner_state_and_hides_from_non_owner(client: TestClient):
    login(client, "creator@example.com")
    created = client.post(
        "/api/create-sessions", json={"initial_message": "做一个解谜游戏"}
    )
    session_id = created.json()["session_id"]

    restored = client.get(f"/api/create-sessions/{session_id}")
    client.post("/api/auth/logout")
    login(client, "viewer@example.com")
    forbidden = client.get(f"/api/create-sessions/{session_id}")

    assert restored.status_code == 200
    assert restored.json()["session_id"] == session_id
    assert restored.json()["user_requirements"] == created.json()["user_requirements"]
    assert restored.json()["game_plan"] == created.json()["game_plan"]
    assert restored.json()["material_usage"] == created.json()["material_usage"]
    assert restored.json()["assistant_response"] == created.json()["assistant_response"]
    assert restored.json()["messages"] == created.json()["messages"]
    assert forbidden.status_code in {403, 404}
