from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from sqlalchemy import UniqueConstraint

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
    }.issubset(index_names("generation_jobs"))
    assert table("generation_jobs").c.user_id.foreign_keys
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
