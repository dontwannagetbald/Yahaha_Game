from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path
import uuid

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app import jobs as jobs_module
from app.db import get_session as app_get_session
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


def login(client: TestClient, email: str):
    response = client.post(
        "/api/auth/register",
        json={"email": email, "password": "password123"},
    )
    assert response.status_code == 201


def create_asset(client: TestClient) -> str:
    presign = client.post(
        "/api/uploads/presign",
        json={"filename": "asset.png", "mime_type": "image/png", "size_bytes": 1024},
    )
    body = presign.json()
    complete = client.post(
        "/api/uploads/complete",
        json={
            "upload_id": body["upload_id"],
            "object_key": body["object_key"],
            "filename": "asset.png",
            "mime_type": "image/png",
            "size_bytes": 1024,
        },
    )
    return complete.json()["asset_id"]


def create_confirmed_session(
    client: TestClient,
    session_factory,
    *,
    initial_message: str = "做一个猫咪跑酷游戏",
    asset_ids: list[str] | None = None,
    status: str = "confirmed",
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
                status=status,
                user_requirements={
                    "intent_summary": initial_message,
                    "must_have": ["跑酷", "收集"],
                    "constraints": [],
                },
                game_plan={
                    "plan_id": "test-plan",
                    "title": "猫咪跑酷",
                    "introduction": "收集鱼干并躲避障碍。",
                    "tags": ["runner"],
                    "gameplay": "跑酷收集",
                    "controls": "方向键移动",
                },
                material_usage={
                    "assets": [
                        {
                            "asset_id": asset_id,
                            "filename": "asset.png",
                            "mime_type": "image/png",
                            "size_bytes": 1024,
                            "object_key": "uploads/test/asset.png",
                            "user_hint": "",
                        }
                        for asset_id in (asset_ids or [])
                    ]
                },
                assistant_response={
                    "message": "方案已确认。",
                    "suggestions": [],
                    "card": {
                        "plan_id": "test-plan",
                        "title": "猫咪跑酷",
                        "introduction": "收集鱼干并躲避障碍。",
                        "tags": ["runner"],
                    },
                    "actions": ["generate"],
                },
                confirmed_at=datetime.now(timezone.utc) if status == "confirmed" else None,
            )
            session.add(create_session)
            for asset_id in asset_ids or []:
                asset = await session.get(UploadedAsset, uuid.UUID(asset_id))
                asset.session_id = create_session_id
            await session.commit()

    asyncio.run(seed_session())
    return str(create_session_id)


def test_recover_interrupted_jobs_marks_pending_and_running_failed(session_factory):
    async def exercise() -> None:
        async with session_factory() as session:
            owner = User(email="owner@example.com", password_hash="hash")
            session.add(owner)
            await session.flush()
            running_job = GenerationJob(
                user_id=owner.user_id,
                prompt="running prompt",
                confirmation={"title": "Running"},
                status="running",
                started_at=datetime.now(timezone.utc) - timedelta(minutes=5),
                created_at=datetime.now(timezone.utc) - timedelta(minutes=6),
            )
            pending_job = GenerationJob(
                user_id=owner.user_id,
                prompt="pending prompt",
                confirmation={"title": "Pending"},
                status="pending",
                created_at=datetime.now(timezone.utc) - timedelta(minutes=4),
            )
            succeeded_job = GenerationJob(
                user_id=owner.user_id,
                prompt="succeeded prompt",
                confirmation={"title": "Succeeded"},
                status="succeeded",
                created_at=datetime.now(timezone.utc),
                finished_at=datetime.now(timezone.utc),
            )
            session.add_all([running_job, pending_job, succeeded_job])
            await session.commit()

            recovered = await jobs_module.recover_interrupted_jobs(session_factory)

            assert recovered == 2
            await session.refresh(running_job)
            await session.refresh(pending_job)
            await session.refresh(succeeded_job)
            assert running_job.status == "failed"
            assert pending_job.status == "failed"
            assert succeeded_job.status == "succeeded"
            assert running_job.finished_at is not None
            assert pending_job.finished_at is not None
            assert "服务重启" in str(running_job.error_message)
            assert "服务重启" in str(pending_job.error_message)
            logs = (await session.execute(select(AgentLog))).scalars().all()
            assert {log.job_id for log in logs} == {running_job.id, pending_job.id}
            assert all(log.step == "agent_runner" for log in logs)

    asyncio.run(exercise())


def test_create_requires_login(client: TestClient):
    response = client.post(
        "/api/jobs",
        json={"prompt": "make game", "asset_ids": [], "confirmation": {"title": "x"}},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"


def test_create_job_from_confirmed_session_snapshots_plan_and_assets(
    client: TestClient, session_factory
):
    login(client, "owner@example.com")
    asset_id = create_asset(client)
    session_id = create_confirmed_session(
        client,
        session_factory,
        initial_message="做一个猫咪跑酷游戏",
        asset_ids=[asset_id],
    )

    created = client.post("/api/jobs", json={"session_id": session_id})

    assert created.status_code == 201
    body = created.json()
    assert body["job_id"]
    assert body["session_id"] == session_id
    assert body["status"] == "pending"

    async def inspect() -> None:
        async with session_factory() as session:
            job = (
                await session.execute(select(GenerationJob))
            ).scalar_one()
            asset = await session.get(UploadedAsset, uuid.UUID(asset_id))
            create_session = await session.get(CreateSession, uuid.UUID(session_id))
            assert job.create_session_id == create_session.id
            assert job.prompt == create_session.user_requirements["intent_summary"]
            assert job.user_requirements == create_session.user_requirements
            assert job.game_plan == create_session.game_plan
            assert job.material_usage == create_session.material_usage
            assert asset.session_id == create_session.id
            assert asset.job_id == job.id

    asyncio.run(inspect())


def test_job_detail_exposes_browser_accessible_artifact_urls(
    client: TestClient, session_factory, tmp_path: Path
):
    login(client, "owner@example.com")
    workspace = tmp_path / "artifact"
    workspace.mkdir()
    (workspace / "manifest.json").write_text(
        '{"entry":"index.html","runtime":"html5-iframe"}',
        encoding="utf-8",
    )
    (workspace / "index.html").write_text("<!doctype html><html></html>", encoding="utf-8")
    job_id = uuid.uuid4()

    async def seed_job() -> None:
        async with session_factory() as session:
            owner = (
                await session.execute(select(User).where(User.email == "owner@example.com"))
            ).scalar_one()
            game = Game(
                owner_id=owner.user_id,
                title="预览测试游戏",
                description="draft",
                cover_url="https://example.com/cover.png",
                tags=["casual"],
                status="draft",
            )
            session.add(game)
            await session.flush()
            job = GenerationJob(
                id=job_id,
                user_id=owner.user_id,
                prompt="预览测试",
                status="succeeded",
                user_requirements={},
                game_plan={"title": "预览测试"},
                material_usage={"assets": []},
                game_id=game.id,
                artifact_prefix=str(workspace),
                manifest_url=str(workspace / "manifest.json"),
            )
            session.add(job)
            await session.commit()

    asyncio.run(seed_job())

    detail = client.get(f"/api/jobs/{job_id}")

    assert detail.status_code == 200
    body = detail.json()
    assert body["manifest_url"] == f"/api/jobs/{job_id}/artifacts/manifest.json"
    assert body["artifact_base_url"] == f"/api/jobs/{job_id}/artifacts/"
    assert body["artifact_prefix"] == str(workspace)
    assert body["cover_url"] == "https://example.com/cover.png"

    artifact = client.get(f"/api/jobs/{job_id}/artifacts/index.html")

    assert artifact.status_code == 200
    assert "<!doctype html>" in artifact.text


def test_missing_legacy_local_artifact_returns_404_without_storage_lookup(
    client: TestClient, session_factory, tmp_path: Path
):
    class ExplodingStorage:
        def get_object(self, object_key: str):
            raise AssertionError(f"unexpected storage lookup: {object_key}")

    app.dependency_overrides[jobs_module.get_storage_service] = lambda: ExplodingStorage()
    login(client, "owner@example.com")
    missing_workspace = tmp_path / "missing-artifact"
    job_id = uuid.uuid4()

    async def seed_job() -> None:
        async with session_factory() as session:
            owner = (
                await session.execute(select(User).where(User.email == "owner@example.com"))
            ).scalar_one()
            job = GenerationJob(
                id=job_id,
                user_id=owner.user_id,
                prompt="旧本地路径测试",
                status="succeeded",
                user_requirements={},
                game_plan={"title": "旧本地路径测试"},
                material_usage={"assets": []},
                artifact_prefix=str(missing_workspace),
                manifest_url=str(missing_workspace / "manifest.json"),
            )
            session.add(job)
            await session.commit()

    asyncio.run(seed_job())

    response = client.get(f"/api/jobs/{job_id}/artifacts/index.html")

    assert response.status_code == 404


def test_create_job_requires_owned_confirmed_session_and_allows_rerun(
    client: TestClient, session_factory
):
    login(client, "owner@example.com")
    unconfirmed_session_id = create_confirmed_session(
        client,
        session_factory,
        initial_message="还没确认的游戏",
        status="ready_to_confirm",
    )

    not_confirmed = client.post(
        "/api/jobs",
        json={"session_id": unconfirmed_session_id},
    )
    assert not_confirmed.status_code == 400

    confirmed_session_id = create_confirmed_session(client, session_factory)
    first = client.post("/api/jobs", json={"session_id": confirmed_session_id})
    rerun = client.post("/api/jobs", json={"session_id": confirmed_session_id})
    assert first.status_code == 201
    assert rerun.status_code == 201
    assert rerun.json()["job_id"] != first.json()["job_id"]

    async def inspect() -> None:
        async with session_factory() as session:
            jobs = (
                await session.execute(
                    select(GenerationJob).order_by(GenerationJob.created_at.asc())
                )
            ).scalars().all()
            assert len(jobs) == 2
            assert all(str(job.create_session_id) == confirmed_session_id for job in jobs)

    asyncio.run(inspect())

    client.post("/api/auth/logout")
    login(client, "other@example.com")
    forbidden = client.post("/api/jobs", json={"session_id": confirmed_session_id})
    assert forbidden.status_code in {403, 404}


def test_create_rejects_session_asset_limit(client: TestClient, session_factory):
    login(client, "owner@example.com")
    asset_id = create_asset(client)
    session_id = create_confirmed_session(
        client,
        session_factory,
        asset_ids=[asset_id] * 6,
    )

    too_many = client.post(
        "/api/jobs",
        json={"session_id": session_id},
    )
    assert too_many.status_code == 400


def test_list_detail_and_logs_permissions(client: TestClient, session_factory):
    login(client, "owner@example.com")
    first_session_id = create_confirmed_session(
        client,
        session_factory,
        initial_message="first",
    )
    second_session_id = create_confirmed_session(
        client,
        session_factory,
        initial_message="second",
    )
    first = client.post("/api/jobs", json={"session_id": first_session_id})
    second = client.post("/api/jobs", json={"session_id": second_session_id})
    first_id = first.json()["job_id"]
    second_id = second.json()["job_id"]

    async def seed_logs():
        async with session_factory() as session:
            job = await session.get(GenerationJob, uuid.UUID(second_id))
            session.add_all(
                [
                    AgentLog(
                        job_id=job.id,
                        step="start",
                        level="info",
                        message="token=secret hidden",
                        created_at=datetime.now(timezone.utc) - timedelta(seconds=1),
                    ),
                    AgentLog(
                        job_id=job.id,
                        step="done",
                        level="info",
                        message="ok",
                        created_at=datetime.now(timezone.utc),
                    ),
                ]
            )
            await session.commit()

    asyncio.run(seed_logs())

    listed = client.get("/api/jobs")
    detail = client.get(f"/api/jobs/{second_id}")
    logs = client.get(f"/api/jobs/{second_id}/logs")

    assert listed.status_code == 200
    assert [job["job_id"] for job in listed.json()["jobs"]] == [second_id, first_id]
    assert [job["session_id"] for job in listed.json()["jobs"]] == [
        second_session_id,
        first_session_id,
    ]
    assert detail.status_code == 200
    assert detail.json()["job_id"] == second_id
    assert detail.json()["session_id"] == second_session_id
    assert detail.json()["parent_job_id"] is None
    assert logs.status_code == 200
    returned_steps = [log["step"] for log in logs.json()["logs"]]
    assert "start" in returned_steps
    assert returned_steps[-1] == "done"
    assert "secret" not in str(logs.json())

    other_client = TestClient(app)
    try:
        app.dependency_overrides[app_get_session] = app.dependency_overrides[
            app_get_session
        ]
        login(other_client, "viewer@example.com")
        assert other_client.get(f"/api/jobs/{second_id}").status_code == 404
        assert other_client.get(f"/api/jobs/{second_id}/logs").status_code == 404
    finally:
        other_client.close()


def test_delete_job_removes_only_owned_task_history(
    client: TestClient, session_factory
):
    login(client, "owner@example.com")
    session_id = create_confirmed_session(client, session_factory)
    created = client.post("/api/jobs", json={"session_id": session_id})
    job_id = created.json()["job_id"]

    async def seed_logs() -> None:
        async with session_factory() as session:
            job = await session.get(GenerationJob, uuid.UUID(job_id))
            session.add(
                AgentLog(
                    job_id=job.id,
                    step="orchestrator",
                    level="info",
                    message="任务已进入编排。",
                    created_at=datetime.now(timezone.utc),
                )
            )
            await session.commit()

    asyncio.run(seed_logs())

    deleted = client.delete(f"/api/jobs/{job_id}")

    assert deleted.status_code == 204
    assert client.get(f"/api/jobs/{job_id}").status_code == 404
    assert client.get("/api/jobs").json()["jobs"] == []

    async def inspect() -> None:
        async with session_factory() as session:
            job = await session.get(GenerationJob, uuid.UUID(job_id))
            create_session = await session.get(CreateSession, uuid.UUID(session_id))
            logs = (
                await session.execute(
                    select(AgentLog).where(AgentLog.job_id == uuid.UUID(job_id))
                )
            ).scalars().all()
            assert job is None
            assert create_session is not None
            assert logs == []

    asyncio.run(inspect())


def test_delete_job_hides_non_owner_task_history(client: TestClient, session_factory):
    login(client, "owner@example.com")
    session_id = create_confirmed_session(client, session_factory)
    created = client.post("/api/jobs", json={"session_id": session_id})
    job_id = created.json()["job_id"]

    client.post("/api/auth/logout")
    login(client, "viewer@example.com")

    deleted = client.delete(f"/api/jobs/{job_id}")

    assert deleted.status_code == 404


def test_delete_job_rejects_pending_or_running_task_history(
    client: TestClient, session_factory
):
    login(client, "owner@example.com")
    session_id = create_confirmed_session(client, session_factory)
    pending_job_id = uuid.uuid4()
    running_job_id = uuid.uuid4()

    async def seed_jobs() -> None:
        async with session_factory() as session:
            owner = (
                await session.execute(select(User).where(User.email == "owner@example.com"))
            ).scalar_one()
            create_session = await session.get(CreateSession, uuid.UUID(session_id))
            for job_id, status in [
                (pending_job_id, "pending"),
                (running_job_id, "running"),
            ]:
                session.add(
                    GenerationJob(
                        id=job_id,
                        user_id=owner.user_id,
                        prompt="做一个猫咪跑酷游戏",
                        confirmation={"title": "猫咪跑酷"},
                        create_session_id=create_session.id,
                        user_requirements=create_session.user_requirements,
                        game_plan=create_session.game_plan,
                        material_usage=create_session.material_usage,
                        status=status,
                        created_at=datetime.now(timezone.utc),
                    )
                )
            await session.commit()

    asyncio.run(seed_jobs())

    pending_delete = client.delete(f"/api/jobs/{pending_job_id}")
    running_delete = client.delete(f"/api/jobs/{running_job_id}")

    assert pending_delete.status_code == 409
    assert running_delete.status_code == 409


def test_revision_job_rejects_pending_or_running_source_job(
    client: TestClient, session_factory
):
    login(client, "owner@example.com")
    session_id = create_confirmed_session(client, session_factory)
    pending_job_id = uuid.uuid4()
    running_job_id = uuid.uuid4()

    async def seed_jobs() -> None:
        async with session_factory() as session:
            owner = (
                await session.execute(select(User).where(User.email == "owner@example.com"))
            ).scalar_one()
            create_session = await session.get(CreateSession, uuid.UUID(session_id))
            for job_id, status in [
                (pending_job_id, "pending"),
                (running_job_id, "running"),
            ]:
                session.add(
                    GenerationJob(
                        id=job_id,
                        user_id=owner.user_id,
                        prompt="做一个猫咪跑酷游戏",
                        confirmation={"title": "猫咪跑酷"},
                        create_session_id=create_session.id,
                        user_requirements=create_session.user_requirements,
                        game_plan=create_session.game_plan,
                        material_usage=create_session.material_usage,
                        status=status,
                        created_at=datetime.now(timezone.utc),
                    )
                )
            await session.commit()

    asyncio.run(seed_jobs())

    pending_revision = client.post(
        f"/api/jobs/{pending_job_id}/revisions",
        json={"message": "把障碍物速度降低一点"},
    )
    running_revision = client.post(
        f"/api/jobs/{running_job_id}/revisions",
        json={"message": "把障碍物速度降低一点"},
    )

    assert pending_revision.status_code == 409
    assert running_revision.status_code == 409


def test_revision_job_copies_snapshots_without_overwriting_source(
    client: TestClient, session_factory
):
    login(client, "owner@example.com")
    session_id = create_confirmed_session(client, session_factory)
    created = client.post("/api/jobs", json={"session_id": session_id})
    source_job_id = created.json()["job_id"]
    source_game_id = uuid.uuid4()

    async def mark_succeeded() -> None:
        async with session_factory() as session:
            job = await session.get(GenerationJob, uuid.UUID(source_job_id))
            game = Game(
                id=source_game_id,
                owner_id=job.user_id,
                title="猫咪跑酷旧版",
                description="旧版 draft",
                cover_url="http://localhost:9000/yahaha-game/drafts/old/cover.png",
                tags=["runner"],
                status="draft",
                manifest_url="http://localhost:9000/yahaha-game/drafts/old/manifest.json",
                artifact_base_url="http://localhost:9000/yahaha-game/drafts/old/",
            )
            session.add(game)
            await session.flush()
            job.status = "succeeded"
            job.game_id = game.id
            job.artifact_prefix = "drafts/old"
            job.manifest_url = game.manifest_url
            await session.commit()

    asyncio.run(mark_succeeded())

    revision = client.post(
        f"/api/jobs/{source_job_id}/revisions",
        json={"message": "把难度降低一点，增加回血道具"},
    )

    assert revision.status_code == 201
    body = revision.json()
    assert body["job_id"] != source_job_id
    assert body["session_id"] == session_id
    assert body["parent_job_id"] == source_job_id
    assert body["status"] == "pending"

    async def inspect() -> None:
        async with session_factory() as session:
            source = await session.get(GenerationJob, uuid.UUID(source_job_id))
            source_game = await session.get(Game, source_game_id)
            child = await session.get(GenerationJob, uuid.UUID(body["job_id"]))
            assert source.status == "succeeded"
            assert source.game_id == source_game_id
            assert source_game.title == "猫咪跑酷旧版"
            assert child.parent_job_id == source.id
            assert child.create_session_id == source.create_session_id
            assert child.revision_intent == "把难度降低一点，增加回血道具"
            assert child.user_requirements == source.user_requirements
            assert child.game_plan == source.game_plan
            assert child.material_usage == source.material_usage

    asyncio.run(inspect())
