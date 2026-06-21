from __future__ import annotations

import asyncio
import uuid
from pathlib import Path
from typing import Any, Dict, List

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.agent_runner import (
    AgentLogEvent,
    AgentRunFailure,
    AgentRunInput,
    AgentRunResult,
    AgentRunSuccess,
    FakeAgentRunner,
    LangGraphGenerationRunner,
    reset_agent_runner,
    set_agent_runner,
)
from app.db import get_session as app_get_session
from app import jobs as jobs_module
from app.main import app
from app.models import AgentLog, Base, CreateSession, Game, GenerationJob, UploadedAsset, User


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
def client(session_factory):
    async def override_get_session():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[app_get_session] = override_get_session
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
        reset_agent_runner()


def register_and_login(client: TestClient, email: str = "owner@example.com") -> None:
    response = client.post(
        "/api/auth/register",
        json={"email": email, "password": "password123"},
    )
    assert response.status_code == 201


def create_asset(
    client: TestClient,
    *,
    filename: str = "asset.png",
    mime_type: str = "image/png",
    size_bytes: int = 1024,
) -> str:
    presign = client.post(
        "/api/uploads/presign",
        json={
            "filename": filename,
            "mime_type": mime_type,
            "size_bytes": size_bytes,
        },
    )
    body = presign.json()
    complete = client.post(
        "/api/uploads/complete",
        json={
            "upload_id": body["upload_id"],
            "object_key": body["object_key"],
            "filename": filename,
            "mime_type": mime_type,
            "size_bytes": size_bytes,
        },
    )
    return complete.json()["asset_id"]


def create_confirmed_session(
    client: TestClient,
    session_factory,
    *,
    initial_message: str = "build a dungeon crawler",
    asset_ids: list[str] | None = None,
) -> str:
    create_session_id = uuid.uuid4()

    async def seed_session() -> None:
        async with session_factory() as session:
            owner = (
                await session.execute(select(User).where(User.email == "owner@example.com"))
            ).scalar_one()
            create_session = CreateSession(
                id=create_session_id,
                user_id=owner.user_id,
                status="confirmed",
                user_requirements={
                    "intent_summary": initial_message,
                    "must_have": ["dungeon", "crawler"],
                    "constraints": [],
                },
                game_plan={
                    "plan_id": "runner-plan",
                    "title": "Dungeon Crawl",
                    "introduction": "Explore rooms",
                    "tags": ["dungeon"],
                    "gameplay": "move and fight",
                    "controls": "WASD",
                },
                material_usage={
                    "assets": [
                        {
                            "asset_id": asset_id,
                            "filename": "asset.png",
                            "mime_type": "image/png",
                            "size_bytes": 1024,
                            "object_key": "uploads/test/asset.png",
                            "user_hint": "uploaded sprite",
                        }
                        for asset_id in (asset_ids or [])
                    ]
                },
                assistant_response={
                    "message": "方案已确认。",
                    "suggestions": [],
                    "card": {
                        "plan_id": "runner-plan",
                        "title": "Dungeon Crawl",
                        "introduction": "Explore rooms",
                        "tags": ["dungeon"],
                    },
                    "actions": ["generate"],
                },
            )
            session.add(create_session)
            for asset_id in asset_ids or []:
                asset = await session.get(UploadedAsset, uuid.UUID(asset_id))
                asset.session_id = create_session_id
            await session.commit()

    asyncio.run(seed_session())
    return str(create_session_id)


class CapturingRunner(FakeAgentRunner):
    def __init__(self, result: AgentRunResult) -> None:
        super().__init__(result=result)
        self.calls: List[Dict[str, Any]] = []

    async def run(self, payload):
        self.calls.append(
            {
                "job_id": str(payload.job_id),
                "user_id": str(payload.user_id),
                "session_id": str(payload.session_id) if payload.session_id else None,
                "prompt": payload.prompt,
                "confirmation": payload.confirmation,
                "user_requirements": payload.user_requirements,
                "game_plan": payload.game_plan,
                "material_usage": payload.material_usage,
                "uploaded_assets": [
                    {
                        "asset_id": str(asset.asset_id),
                        "filename": asset.filename,
                        "mime_type": asset.mime_type,
                        "size_bytes": asset.size_bytes,
                        "object_key": asset.object_key,
                        "local_path": asset.local_path,
                    }
                    for asset in payload.uploaded_assets
                ],
            }
        )
        return await super().run(payload)


class RaisingRunner(FakeAgentRunner):
    async def run(self, payload):
        raise RuntimeError(
            "Image provider returned invalid JSON: "
            "{\"error\":{\"message\":\"The model 'gpt-5.5' does not exist.\","
            "\"type\":\"image_generation_user_error\",\"param\":\"model\","
            "\"code\":\"invalid_value\"},\"token\":\"secret-value\"}"
        )


class StreamingRunner(FakeAgentRunner):
    async def run(self, payload, emit_log=None):
        if emit_log is not None:
            await emit_log(
                AgentLogEvent(
                    step="orchestrator",
                    level="info",
                    message="orchestrator started",
                )
            )
            await emit_log(
                AgentLogEvent(
                    step="orchestrator",
                    level="info",
                    message="orchestrator completed",
                )
            )
        return success_result()


class FakeGenerationGraph:
    async def astream_events(self, state, version):
        assert version == "v2"
        assert state["job_context"]["job_id"]
        assert state["game_plan"]["title"] == "Dungeon Crawl"
        yield {
            "event": "on_chain_start",
            "name": "Generation Graph",
            "metadata": {},
        }
        yield {
            "event": "on_chain_start",
            "name": "orchestrator",
            "metadata": {"langgraph_node": "orchestrator"},
        }
        yield {
            "event": "on_chain_end",
            "name": "orchestrator",
            "metadata": {"langgraph_node": "orchestrator"},
            "data": {"output": {"development_brief": {"title": "Dungeon Crawl"}}},
        }
        yield {
            "event": "on_chain_start",
            "name": "coding_agent",
            "metadata": {"langgraph_node": "coding_agent"},
        }
        yield {
            "event": "on_chain_end",
            "name": "coding_agent",
            "metadata": {"langgraph_node": "coding_agent"},
            "data": {"output": {"generation_status": "code_drafted"}},
        }
        yield {
            "event": "on_chain_end",
            "name": "Generation Graph",
            "metadata": {},
            "data": {
                "output": {
                    "status": "succeeded",
                    "generation_status": "succeeded",
                    "artifact_workspace": "output/drafts/test-user/test-job/v1",
                    "artifact_result": {
                        "workspace": "output/drafts/test-user/test-job/v1",
                        "manifest_path": "output/drafts/test-user/test-job/v1/manifest.json",
                        "cover_path": "assets/cover.png",
                    },
                    "draft_game_meta": {
                        "title": "Dungeon Crawl",
                        "description": "Explore rooms",
                        "tags": ["dungeon"],
                        "cover_path": "assets/cover.png",
                        "manifest_path": "manifest.json",
                    },
                }
            },
        }


class FailingGenerationGraph:
    async def astream_events(self, state, version):
        yield {
            "event": "on_chain_start",
            "name": "asset_agent",
            "metadata": {"langgraph_node": "asset_agent"},
        }
        raise RuntimeError("image provider exploded")


class FinalStateFailureGraph:
    async def astream_events(self, state, version):
        yield {
            "event": "on_chain_end",
            "name": "Generation Graph",
            "metadata": {},
            "data": {
                "output": {
                    "status": "failed",
                    "generation_status": "failed",
                    "failed_step": "validator_agent",
                    "error_message": (
                        "最终验收失败：runtime_check_failed - Runtime check did not pass: "
                        "game_ready signal missing; render signal missing.。"
                    ),
                    "retry_hint": "请重新生成游戏，或调整素材后再试。",
                    "validation_report": {
                        "valid": False,
                        "issues": [
                            {
                                "kind": "runtime_check_failed",
                                "message": (
                                    "Runtime check did not pass: game_ready signal "
                                    "missing; render signal missing."
                                ),
                                "runtime_details": [
                                    "game_ready signal missing",
                                    "render signal missing",
                                ],
                            }
                        ],
                        "checked_files": ["manifest.json", "index.html"],
                    },
                    "agent_logs": [
                        {
                            "step": "validator_agent",
                            "level": "error",
                            "message": (
                                "最终验收失败：runtime_check_failed - Runtime check did not pass: "
                                "game_ready signal missing; render signal missing.。"
                            ),
                        }
                    ],
                }
            },
        }


def success_result() -> AgentRunSuccess:
    return AgentRunSuccess(
        title="Mock Dungeon",
        description="A deterministic dungeon game",
        tags=["dungeon", "mock"],
        cover_url="https://example.com/mock-cover.png",
        artifact_prefix="drafts/user-id/job-id/v1",
        manifest_url="https://draft.local/drafts/user-id/job-id/v1/manifest.json",
        artifact_base_url="https://draft.local/drafts/user-id/job-id/v1/",
        result_summary="Mock generation completed",
        logs=[
            AgentLogEvent(step="start", level="info", message="Generation started"),
            AgentLogEvent(step="build", level="info", message="Bundle generated"),
        ],
    )


class StubPresignedReadResult:
    def __init__(self, url: str, expires_in: int = 900) -> None:
        self.url = url
        self.expires_in = expires_in


class RecordingStorageService:
    def __init__(self) -> None:
        self.objects: dict[str, tuple[bytes, str]] = {}

    def build_upload_object_key(self, *, user_id, upload_id, filename: str) -> str:
        return f"uploads/{user_id}/{upload_id}/{filename}"

    def build_presigned_upload_url(self, object_key: str, *, expires_in: int = 900):
        return StubPresignedReadResult(
            f"http://localhost:9000/yahaha-game/{object_key}?X-Amz-Signature=test",
            expires_in,
        )

    def build_draft_object_key(self, *, user_id, job_id, version: str, relative_path: str) -> str:
        return f"drafts/{user_id}/{job_id}/{version}/{relative_path}"

    def build_presigned_read_url(self, object_key: str, *, expires_in: int = 900):
        return StubPresignedReadResult(
            f"http://localhost:9000/yahaha-game/{object_key}?X-Amz-Signature=test",
            expires_in,
        )

    def put_object(self, object_key: str, *, body: bytes, content_type: str) -> None:
        self.objects[object_key] = (body, content_type)

    def get_object(self, object_key: str):
        body, content_type = self.objects[object_key]
        return body, content_type


def local_bundle_result(workspace: Path) -> AgentRunSuccess:
    (workspace / "assets").mkdir(parents=True)
    (workspace / "manifest.json").write_text(
        '{"entry":"index.html","styles":["style.css"],"scripts":["game.js"],"assets":["assets/cover.png"],"cover":"assets/cover.png","runtime":"html5-iframe"}',
        encoding="utf-8",
    )
    (workspace / "index.html").write_text("<!doctype html><html></html>", encoding="utf-8")
    (workspace / "style.css").write_text("body { margin: 0; }", encoding="utf-8")
    (workspace / "game.js").write_text("window.parent.postMessage({type:'game_ready'}, '*');", encoding="utf-8")
    (workspace / "assets" / "cover.png").write_bytes(b"fake-png")
    return AgentRunSuccess(
        title="Local Bundle",
        description="A generated local bundle",
        tags=["local"],
        cover_url=str(workspace / "assets" / "cover.png"),
        artifact_prefix=str(workspace),
        manifest_url=str(workspace / "manifest.json"),
        artifact_base_url=f"{workspace}/",
        result_summary="Generation completed",
        logs=[AgentLogEvent(step="finish", level="info", message="Bundle generated")],
    )


def failure_result() -> AgentRunFailure:
    return AgentRunFailure(
        error_message="Mock provider failed",
        retry_hint="Retry later",
        failed_step="build",
        validation_report={
            "valid": False,
            "issues": [{"kind": "runtime_check_failed"}],
        },
        logs=[
            AgentLogEvent(step="start", level="info", message="Generation started"),
            AgentLogEvent(step="build", level="error", message="Bundle failed"),
        ],
    )


def runner_payload() -> AgentRunInput:
    return AgentRunInput(
        job_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        session_id=uuid.uuid4(),
        prompt="build a dungeon crawler",
        confirmation={"title": "Dungeon Crawl"},
        user_requirements={"intent_summary": "build a dungeon crawler"},
        game_plan={
            "title": "Dungeon Crawl",
            "introduction": "Explore rooms",
            "tags": ["dungeon"],
        },
        material_usage={"assets": []},
        uploaded_assets=[],
    )


@pytest.mark.asyncio
async def test_langgraph_runner_emits_node_start_and_end_logs():
    logs: list[AgentLogEvent] = []
    runner = LangGraphGenerationRunner(graph=FakeGenerationGraph())

    result = await runner.run(runner_payload(), emit_log=logs.append)

    assert isinstance(result, AgentRunSuccess)
    assert result.title == "Dungeon Crawl"
    assert result.manifest_url.endswith("/manifest.json")
    assert [
        (log.step, log.level, log.message)
        for log in logs
    ] == [
        ("orchestrator", "info", "orchestrator started"),
        ("orchestrator", "info", "orchestrator completed"),
        ("coding_agent", "info", "coding_agent started"),
        ("coding_agent", "info", "coding_agent completed"),
    ]


@pytest.mark.asyncio
async def test_langgraph_runner_emits_node_error_log_before_reraising():
    logs: list[AgentLogEvent] = []
    runner = LangGraphGenerationRunner(graph=FailingGenerationGraph())

    with pytest.raises(RuntimeError, match="image provider exploded"):
        await runner.run(runner_payload(), emit_log=logs.append)

    assert [(log.step, log.level) for log in logs] == [
        ("asset_agent", "info"),
        ("asset_agent", "error"),
    ]
    assert logs[-1].message == "asset_agent failed: image provider exploded"


@pytest.mark.asyncio
async def test_langgraph_runner_preserves_validation_report_on_failure():
    runner = LangGraphGenerationRunner(graph=FinalStateFailureGraph())

    result = await runner.run(runner_payload())

    assert isinstance(result, AgentRunFailure)
    assert "game_ready signal missing" in result.error_message
    assert result.failed_step == "validator_agent"
    assert result.validation_report["issues"][0]["kind"] == "runtime_check_failed"
    assert result.validation_report["issues"][0]["runtime_details"] == [
        "game_ready signal missing",
        "render signal missing",
    ]
    assert result.logs[-1].step == "validator_agent"
    assert "game_ready signal missing" in result.logs[-1].message


def test_runner_input_contains_session_snapshots_and_assets(
    client: TestClient, session_factory
):
    storage = RecordingStorageService()
    app.dependency_overrides[jobs_module.get_storage_service] = lambda: storage
    runner = CapturingRunner(result=success_result())
    set_agent_runner(runner)
    register_and_login(client)
    asset_id = create_asset(client)
    asset_object_key = ""
    async def read_asset_key() -> None:
        nonlocal asset_object_key
        async with session_factory() as session:
            asset = await session.get(UploadedAsset, uuid.UUID(asset_id))
            assert asset is not None
            asset_object_key = asset.object_key

    asyncio.run(read_asset_key())
    storage.objects[asset_object_key] = (b"uploaded-player-png", "image/png")
    session_id = create_confirmed_session(
        client,
        session_factory,
        initial_message="build a dungeon crawler",
        asset_ids=[asset_id],
    )

    response = client.post(
        "/api/jobs",
        json={"session_id": session_id},
    )

    assert response.status_code == 201
    assert len(runner.calls) == 1
    call = runner.calls[0]
    assert call["job_id"] == response.json()["job_id"]
    assert call["session_id"] == session_id
    assert call["prompt"] == "build a dungeon crawler"
    assert call["confirmation"]["title"] == "Dungeon Crawl"
    assert call["user_requirements"]["intent_summary"] == "build a dungeon crawler"
    assert call["game_plan"]["title"] == "Dungeon Crawl"
    assert call["material_usage"]["assets"][0]["asset_id"] == asset_id
    assert len(call["uploaded_assets"]) == 1
    assert call["uploaded_assets"][0]["asset_id"] == asset_id
    uploaded_local_path = Path(call["uploaded_assets"][0]["local_path"])
    assert uploaded_local_path.is_file()
    assert uploaded_local_path.read_bytes() == b"uploaded-player-png"
    assert "X-Amz-Signature" not in str(call["uploaded_assets"])


def test_background_status_flow_handles_success_and_failure(client: TestClient, session_factory):
    register_and_login(client)

    success_runner = CapturingRunner(result=success_result())
    set_agent_runner(success_runner)
    success_session_id = create_confirmed_session(
        client,
        session_factory,
        initial_message="make success",
    )
    success_response = client.post(
        "/api/jobs",
        json={"session_id": success_session_id},
    )
    success_job_id = success_response.json()["job_id"]

    failure_runner = CapturingRunner(result=failure_result())
    set_agent_runner(failure_runner)
    failure_session_id = create_confirmed_session(
        client,
        session_factory,
        initial_message="make failure",
    )
    failure_response = client.post(
        "/api/jobs",
        json={"session_id": failure_session_id},
    )
    failure_job_id = failure_response.json()["job_id"]

    async def inspect():
        async with session_factory() as session:
            success_job = await session.get(GenerationJob, uuid.UUID(success_job_id))
            failure_job = await session.get(GenerationJob, uuid.UUID(failure_job_id))
            assert success_job.status == "succeeded"
            assert success_job.started_at is not None
            assert success_job.finished_at is not None
            assert failure_job.status == "failed"
            assert failure_job.started_at is not None
            assert failure_job.finished_at is not None
            assert failure_job.error_message == "Mock provider failed"
            assert failure_job.validation_report["issues"][0]["kind"] == (
                "runtime_check_failed"
            )

            success_logs = (
                await session.execute(
                    select(AgentLog)
                    .where(AgentLog.job_id == success_job.id)
                    .order_by(AgentLog.created_at.asc())
                )
            ).scalars().all()
            failure_logs = (
                await session.execute(
                    select(AgentLog)
                    .where(AgentLog.job_id == failure_job.id)
                    .order_by(AgentLog.created_at.asc())
                )
            ).scalars().all()
            assert [log.step for log in success_logs][:2] == ["start", "build"]
            assert failure_logs[-1].level == "error"

    detail = client.get(f"/api/jobs/{failure_job_id}")
    assert detail.status_code == 200
    assert detail.json()["validation_report"]["valid"] is False
    assert detail.json()["validation_report"]["issues"][0]["kind"] == (
        "runtime_check_failed"
    )

    asyncio.run(inspect())


def test_background_status_flow_persists_provider_exceptions(
    client: TestClient, session_factory
):
    set_agent_runner(RaisingRunner())
    register_and_login(client)
    session_id = create_confirmed_session(
        client,
        session_factory,
        initial_message="make provider exception",
    )

    response = client.post(
        "/api/jobs",
        json={"session_id": session_id},
    )
    job_id = response.json()["job_id"]

    assert response.status_code == 201

    async def inspect():
        async with session_factory() as session:
            job = await session.get(GenerationJob, uuid.UUID(job_id))
            assert job.status == "failed"
            assert job.started_at is not None
            assert job.finished_at is not None
            assert "Image provider returned invalid JSON" in job.error_message
            assert "The model 'gpt-5.5' does not exist." in job.error_message
            assert "secret-value" not in job.error_message

            logs = (
                await session.execute(
                    select(AgentLog)
                    .where(AgentLog.job_id == job.id)
                    .order_by(AgentLog.created_at.asc())
                )
            ).scalars().all()
            assert logs[-1].step == "agent_runner"
            assert logs[-1].level == "error"
            assert "The model 'gpt-5.5' does not exist." in logs[-1].message
            assert "secret-value" not in logs[-1].message

    asyncio.run(inspect())


def test_background_status_flow_persists_streamed_runner_logs(
    client: TestClient, session_factory
):
    set_agent_runner(StreamingRunner())
    register_and_login(client)
    session_id = create_confirmed_session(
        client,
        session_factory,
        initial_message="make streaming logs",
    )

    response = client.post(
        "/api/jobs",
        json={"session_id": session_id},
    )
    job_id = response.json()["job_id"]

    assert response.status_code == 201

    async def inspect():
        async with session_factory() as session:
            job = await session.get(GenerationJob, uuid.UUID(job_id))
            assert job.status == "succeeded"

            logs = (
                await session.execute(
                    select(AgentLog)
                    .where(AgentLog.job_id == job.id)
                    .order_by(AgentLog.created_at.asc())
                )
            ).scalars().all()
            messages = [log.message for log in logs]
            assert "orchestrator started" in messages
            assert "orchestrator completed" in messages
            assert messages.index("orchestrator started") < messages.index(
                "orchestrator completed"
            )

    asyncio.run(inspect())


def test_success_creates_draft_game_and_links_job(client: TestClient, session_factory):
    runner = CapturingRunner(result=success_result())
    set_agent_runner(runner)
    register_and_login(client)
    session_id = create_confirmed_session(
        client,
        session_factory,
        initial_message="build draft game",
    )

    response = client.post(
        "/api/jobs",
        json={"session_id": session_id},
    )

    job_id = response.json()["job_id"]

    async def inspect():
        async with session_factory() as session:
            job = await session.get(GenerationJob, uuid.UUID(job_id))
            assert job.status == "succeeded"
            assert job.game_id is not None
            assert job.artifact_prefix == "drafts/user-id/job-id/v1"
            assert job.manifest_url == "https://draft.local/drafts/user-id/job-id/v1/manifest.json"

            game = await session.get(Game, job.game_id)
            assert game is not None
            assert game.status == "draft"
            assert game.title == "Mock Dungeon"
            assert game.description == "A deterministic dungeon game"
            assert game.tags == ["dungeon", "mock"]
            assert game.cover_url == "https://example.com/mock-cover.png"
            assert game.manifest_url == job.manifest_url
            assert game.artifact_base_url == "https://draft.local/drafts/user-id/job-id/v1/"

    asyncio.run(inspect())


def test_success_uploads_local_bundle_to_draft_storage(
    client: TestClient, session_factory, tmp_path: Path
):
    storage = RecordingStorageService()
    app.dependency_overrides[jobs_module.get_storage_service] = lambda: storage
    runner = CapturingRunner(result=local_bundle_result(tmp_path / "bundle"))
    set_agent_runner(runner)
    register_and_login(client)
    session_id = create_confirmed_session(
        client,
        session_factory,
        initial_message="build stored draft game",
    )

    response = client.post(
        "/api/jobs",
        json={"session_id": session_id},
    )

    job_id = response.json()["job_id"]

    async def inspect():
        async with session_factory() as session:
            job = await session.get(GenerationJob, uuid.UUID(job_id))
            assert job.status == "succeeded"
            assert job.artifact_prefix == f"drafts/{job.user_id}/{job.id}/v1"
            assert job.manifest_url.startswith("http://localhost:9000/yahaha-game/drafts/")
            assert "/app/output/" not in job.manifest_url

            game = await session.get(Game, job.game_id)
            assert game is not None
            assert game.manifest_url == f"/api/jobs/{job.id}/artifacts/manifest.json"
            assert game.artifact_base_url == f"/api/jobs/{job.id}/artifacts/"
            assert game.cover_url == f"/api/jobs/{job.id}/artifacts/assets/cover.png"

    asyncio.run(inspect())

    assert f"drafts/{runner.calls[0]['user_id']}/{job_id}/v1/manifest.json" in storage.objects
    assert f"drafts/{runner.calls[0]['user_id']}/{job_id}/v1/index.html" in storage.objects

    artifact = client.get(f"/api/jobs/{job_id}/artifacts/index.html")

    assert artifact.status_code == 200
    assert "<!doctype html>" in artifact.text
