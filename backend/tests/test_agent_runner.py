from __future__ import annotations

import asyncio
import uuid
from typing import Any, Dict, List

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.agent_runner import (
    AgentLogEvent,
    AgentRunFailure,
    AgentRunResult,
    AgentRunSuccess,
    FakeAgentRunner,
    reset_agent_runner,
    set_agent_runner,
)
from app.db import get_session as app_get_session
from app.main import app
from app.models import AgentLog, Base, Game, GenerationJob, UploadedAsset


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


class CapturingRunner(FakeAgentRunner):
    def __init__(self, result: AgentRunResult) -> None:
        super().__init__(result=result)
        self.calls: List[Dict[str, Any]] = []

    async def run(self, payload):
        self.calls.append(
            {
                "job_id": str(payload.job_id),
                "user_id": str(payload.user_id),
                "prompt": payload.prompt,
                "confirmation": payload.confirmation,
                "uploaded_assets": [
                    {
                        "asset_id": str(asset.asset_id),
                        "filename": asset.filename,
                        "mime_type": asset.mime_type,
                        "size_bytes": asset.size_bytes,
                        "object_key": asset.object_key,
                    }
                    for asset in payload.uploaded_assets
                ],
            }
        )
        return await super().run(payload)


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


def failure_result() -> AgentRunFailure:
    return AgentRunFailure(
        error_message="Mock provider failed",
        retry_hint="Retry later",
        failed_step="build",
        logs=[
            AgentLogEvent(step="start", level="info", message="Generation started"),
            AgentLogEvent(step="build", level="error", message="Bundle failed"),
        ],
    )


def test_runner_input_contains_job_user_prompt_confirmation_and_assets(
    client: TestClient,
):
    runner = CapturingRunner(result=success_result())
    set_agent_runner(runner)
    register_and_login(client)
    asset_id = create_asset(client)

    response = client.post(
        "/api/jobs",
        json={
            "prompt": "build a dungeon crawler",
            "asset_ids": [asset_id],
            "confirmation": {
                "title": "Dungeon Crawl",
                "short_description": "Explore rooms",
                "game_type": "roguelike",
                "core_gameplay": "move and fight",
                "win_lose_condition": "beat the boss",
                "controls": "WASD",
                "assets_used": "uploaded sprite",
                "tags": ["dungeon"],
                "cover_suggestion": "torch hallway",
            },
        },
    )

    assert response.status_code == 201
    assert len(runner.calls) == 1
    call = runner.calls[0]
    assert call["job_id"] == response.json()["job_id"]
    assert call["prompt"] == "build a dungeon crawler"
    assert call["confirmation"]["title"] == "Dungeon Crawl"
    assert len(call["uploaded_assets"]) == 1
    assert call["uploaded_assets"][0]["asset_id"] == asset_id
    assert "X-Amz-Signature" not in str(call["uploaded_assets"])


def test_background_status_flow_handles_success_and_failure(client: TestClient, session_factory):
    register_and_login(client)

    success_runner = CapturingRunner(result=success_result())
    set_agent_runner(success_runner)
    success_response = client.post(
        "/api/jobs",
        json={
            "prompt": "make success",
            "asset_ids": [],
            "confirmation": {"title": "Success Title"},
        },
    )
    success_job_id = success_response.json()["job_id"]

    failure_runner = CapturingRunner(result=failure_result())
    set_agent_runner(failure_runner)
    failure_response = client.post(
        "/api/jobs",
        json={
            "prompt": "make failure",
            "asset_ids": [],
            "confirmation": {"title": "Failure Title"},
        },
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

    asyncio.run(inspect())


def test_success_creates_draft_game_and_links_job(client: TestClient, session_factory):
    runner = CapturingRunner(result=success_result())
    set_agent_runner(runner)
    register_and_login(client)

    response = client.post(
        "/api/jobs",
        json={
            "prompt": "build draft game",
            "asset_ids": [],
            "confirmation": {
                "title": "Dungeon Crawl",
                "short_description": "Explore rooms",
                "tags": ["dungeon", "mock"],
                "cover_suggestion": "torch hallway",
            },
        },
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
