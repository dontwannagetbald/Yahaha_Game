from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from sqlalchemy import CheckConstraint, UniqueConstraint

from app.models import Base


REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = REPO_ROOT / "backend"


def table(name: str):
    return Base.metadata.tables[name]


def column_names(table_name: str) -> set[str]:
    return set(table(table_name).columns.keys())


def index_names(table_name: str) -> set[str]:
    return {index.name for index in table(table_name).indexes}


def unique_constraint_names(table_name: str) -> set[str]:
    return {
        constraint.name
        for constraint in table(table_name).constraints
        if isinstance(constraint, UniqueConstraint)
    }


def check_constraint_sql(table_name: str, constraint_name: str) -> str:
    for constraint in table(table_name).constraints:
        if isinstance(constraint, CheckConstraint) and constraint.name == constraint_name:
            return str(constraint.sqltext)
    raise AssertionError(f"Missing check constraint {constraint_name}")


def test_games_table_has_required_columns_and_indexes():
    assert "games" in Base.metadata.tables
    assert {
        "id",
        "owner_id",
        "title",
        "description",
        "cover_url",
        "tags",
        "status",
        "manifest_url",
        "artifact_base_url",
        "play_count",
        "like_count",
        "published_at",
        "created_at",
        "updated_at",
    }.issubset(column_names("games"))
    assert {
        "ix_games_owner_id",
        "ix_games_status",
        "ix_games_published_at",
        "ix_games_created_at",
    }.issubset(index_names("games"))
    assert table("games").c.owner_id.foreign_keys
    assert table("games").c.status.default.arg == "draft"


def test_game_likes_table_has_required_unique_constraint():
    assert "game_likes" in Base.metadata.tables
    assert {"id", "game_id", "user_id", "created_at"}.issubset(
        column_names("game_likes")
    )
    assert "uq_game_likes_game_user" in unique_constraint_names("game_likes")
    assert table("game_likes").c.game_id.foreign_keys
    assert table("game_likes").c.user_id.foreign_keys


def test_generation_jobs_table_has_required_columns_and_indexes():
    assert "generation_jobs" in Base.metadata.tables
    assert {
        "id",
        "user_id",
        "prompt",
        "confirmation",
        "create_session_id",
        "parent_job_id",
        "revision_intent",
        "user_requirements",
        "game_plan",
        "material_usage",
        "validation_report",
        "status",
        "game_id",
        "artifact_prefix",
        "manifest_url",
        "result_summary",
        "error_message",
        "created_at",
        "started_at",
        "finished_at",
    }.issubset(column_names("generation_jobs"))
    assert {
        "ix_generation_jobs_user_id",
        "ix_generation_jobs_status",
        "ix_generation_jobs_created_at",
        "ix_generation_jobs_create_session_id",
        "ix_generation_jobs_parent_job_id",
    }.issubset(index_names("generation_jobs"))
    assert table("generation_jobs").c.user_id.foreign_keys
    assert table("generation_jobs").c.create_session_id.nullable is True
    assert table("generation_jobs").c.create_session_id.foreign_keys
    create_session_fk = next(iter(table("generation_jobs").c.create_session_id.foreign_keys))
    assert create_session_fk.target_fullname == "create_sessions.id"
    assert table("generation_jobs").c.parent_job_id.nullable is True
    assert table("generation_jobs").c.parent_job_id.foreign_keys
    parent_job_fk = next(iter(table("generation_jobs").c.parent_job_id.foreign_keys))
    assert parent_job_fk.target_fullname == "generation_jobs.id"
    assert table("generation_jobs").c.game_id.nullable is True
    assert table("generation_jobs").c.status.default.arg == "pending"


def test_uploaded_assets_table_allows_unbound_job():
    assert "uploaded_assets" in Base.metadata.tables
    assert {
        "id",
        "user_id",
        "job_id",
        "filename",
        "mime_type",
        "size_bytes",
        "object_key",
        "purpose",
        "created_at",
    }.issubset(column_names("uploaded_assets"))
    assert table("uploaded_assets").c.job_id.nullable is True
    assert table("uploaded_assets").c.user_id.foreign_keys
    assert table("uploaded_assets").c.job_id.foreign_keys
    assert {
        "ix_uploaded_assets_user_id",
        "ix_uploaded_assets_job_id",
        "ix_uploaded_assets_created_at",
    }.issubset(index_names("uploaded_assets"))


def test_uploaded_assets_session_binding_column_allows_create_session_binding():
    assert "uploaded_assets" in Base.metadata.tables
    assert "session_id" in column_names("uploaded_assets")
    assert table("uploaded_assets").c.session_id.nullable is True
    assert table("uploaded_assets").c.session_id.foreign_keys
    session_id_fk = next(iter(table("uploaded_assets").c.session_id.foreign_keys))
    assert session_id_fk.target_fullname == "create_sessions.id"
    assert "ix_uploaded_assets_session_id" in index_names("uploaded_assets")


def test_create_sessions_table_has_required_columns_constraints_and_indexes():
    assert "create_sessions" in Base.metadata.tables
    assert {
        "id",
        "user_id",
        "status",
        "user_requirements",
        "game_plan",
        "material_usage",
        "assistant_response",
        "created_at",
        "updated_at",
        "confirmed_at",
    }.issubset(column_names("create_sessions"))
    assert {
        "ix_create_sessions_user_id",
        "ix_create_sessions_status",
        "ix_create_sessions_created_at",
        "ix_create_sessions_updated_at",
    }.issubset(index_names("create_sessions"))
    assert table("create_sessions").c.user_id.foreign_keys
    user_id_fk = next(iter(table("create_sessions").c.user_id.foreign_keys))
    assert user_id_fk.target_fullname == "users.user_id"
    assert table("create_sessions").c.status.default.arg == "collecting"
    assert table("create_sessions").c.confirmed_at.nullable is True
    status_check = check_constraint_sql(
        "create_sessions", "ck_create_sessions_status"
    )
    for status in ("collecting", "ready_to_confirm", "confirmed", "error"):
        assert status in status_check


def test_create_session_messages_table_has_required_shape():
    assert "create_session_messages" in Base.metadata.tables
    assert {
        "id",
        "session_id",
        "role",
        "content",
        "payload",
        "created_at",
    }.issubset(column_names("create_session_messages"))
    assert table("create_session_messages").c.session_id.foreign_keys
    session_id_fk = next(
        iter(table("create_session_messages").c.session_id.foreign_keys)
    )
    assert session_id_fk.target_fullname == "create_sessions.id"
    role_check = check_constraint_sql(
        "create_session_messages", "ck_create_session_messages_role"
    )
    for role in ("user", "assistant", "system"):
        assert role in role_check
    assert {
        "ix_create_session_messages_session_id",
        "ix_create_session_messages_created_at",
    }.issubset(index_names("create_session_messages"))


def test_agent_logs_and_play_events_tables_have_required_shape():
    assert "agent_logs" in Base.metadata.tables
    assert {"id", "job_id", "step", "level", "message", "created_at"}.issubset(
        column_names("agent_logs")
    )
    assert table("agent_logs").c.job_id.foreign_keys
    assert "ix_agent_logs_job_id" in index_names("agent_logs")

    assert "play_events" in Base.metadata.tables
    assert {
        "id",
        "game_id",
        "user_id",
        "event_type",
        "metadata",
        "created_at",
    }.issubset(column_names("play_events"))
    assert table("play_events").c.user_id.nullable is True
    assert table("play_events").c.game_id.foreign_keys
    assert table("play_events").c.user_id.foreign_keys
    assert {
        "ix_play_events_game_id",
        "ix_play_events_user_id",
        "ix_play_events_created_at",
    }.issubset(index_names("play_events"))


@pytest.mark.parametrize(
    "table_name",
    [
        "games",
        "game_likes",
        "generation_jobs",
        "create_sessions",
        "create_session_messages",
        "uploaded_assets",
        "agent_logs",
        "play_events",
    ],
)
def test_alembic_upgrade_sql_creates_business_tables(table_name: str):
    result = subprocess.run(
        ["../.venv/bin/alembic", "upgrade", "head", "--sql"],
        cwd=BACKEND_DIR,
        check=True,
        text=True,
        capture_output=True,
    )

    assert f"CREATE TABLE {table_name}" in result.stdout


def test_alembic_upgrade_sql_repairs_generation_jobs_session_snapshot_columns():
    result = subprocess.run(
        ["../.venv/bin/alembic", "upgrade", "head", "--sql"],
        cwd=BACKEND_DIR,
        check=True,
        text=True,
        capture_output=True,
    )

    assert "0004_repair_job_snapshots" in result.stdout
    assert "ADD COLUMN create_session_id" in result.stdout
    assert "ADD COLUMN parent_job_id" in result.stdout
    assert "ADD COLUMN revision_intent" in result.stdout
    assert "ADD COLUMN user_requirements" in result.stdout
    assert "ADD COLUMN game_plan" in result.stdout
    assert "ADD COLUMN material_usage" in result.stdout
    assert "ix_generation_jobs_create_session_id" in result.stdout
    assert "ix_generation_jobs_parent_job_id" in result.stdout
