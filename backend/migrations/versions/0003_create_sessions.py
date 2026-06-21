"""add create sessions

Revision ID: 0003_create_sessions
Revises: 0002_business_tables
Create Date: 2026-06-20 00:00:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "0003_create_sessions"
down_revision: Union[str, None] = "0002_business_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "create_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("user_requirements", sa.JSON(), nullable=False),
        sa.Column("game_plan", sa.JSON(), nullable=False),
        sa.Column("material_usage", sa.JSON(), nullable=False),
        sa.Column("assistant_response", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('collecting', 'ready_to_confirm', 'confirmed', 'error')",
            name="ck_create_sessions_status",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_create_sessions_user_id", "create_sessions", ["user_id"])
    op.create_index("ix_create_sessions_status", "create_sessions", ["status"])
    op.create_index("ix_create_sessions_created_at", "create_sessions", ["created_at"])
    op.create_index("ix_create_sessions_updated_at", "create_sessions", ["updated_at"])
    op.add_column(
        "generation_jobs",
        sa.Column("create_session_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "generation_jobs",
        sa.Column("parent_job_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "generation_jobs",
        sa.Column("revision_intent", sa.Text(), nullable=True),
    )
    op.add_column(
        "generation_jobs",
        sa.Column("user_requirements", sa.JSON(), nullable=False, server_default="{}"),
    )
    op.add_column(
        "generation_jobs",
        sa.Column("game_plan", sa.JSON(), nullable=False, server_default="{}"),
    )
    op.add_column(
        "generation_jobs",
        sa.Column("material_usage", sa.JSON(), nullable=False, server_default="{}"),
    )
    op.create_foreign_key(
        "fk_generation_jobs_create_session_id_create_sessions",
        "generation_jobs",
        "create_sessions",
        ["create_session_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_generation_jobs_parent_job_id_generation_jobs",
        "generation_jobs",
        "generation_jobs",
        ["parent_job_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_generation_jobs_create_session_id",
        "generation_jobs",
        ["create_session_id"],
    )
    op.create_index(
        "ix_generation_jobs_parent_job_id",
        "generation_jobs",
        ["parent_job_id"],
    )
    op.create_table(
        "create_session_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "role IN ('user', 'assistant', 'system')",
            name="ck_create_session_messages_role",
        ),
        sa.ForeignKeyConstraint(
            ["session_id"], ["create_sessions.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_create_session_messages_session_id",
        "create_session_messages",
        ["session_id"],
    )
    op.create_index(
        "ix_create_session_messages_created_at",
        "create_session_messages",
        ["created_at"],
    )
    op.add_column(
        "uploaded_assets",
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_uploaded_assets_session_id_create_sessions",
        "uploaded_assets",
        "create_sessions",
        ["session_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_uploaded_assets_session_id", "uploaded_assets", ["session_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_uploaded_assets_session_id", table_name="uploaded_assets")
    op.drop_constraint(
        "fk_uploaded_assets_session_id_create_sessions",
        "uploaded_assets",
        type_="foreignkey",
    )
    op.drop_column("uploaded_assets", "session_id")
    op.drop_index(
        "ix_create_session_messages_created_at",
        table_name="create_session_messages",
    )
    op.drop_index(
        "ix_create_session_messages_session_id",
        table_name="create_session_messages",
    )
    op.drop_table("create_session_messages")
    op.drop_index("ix_create_sessions_updated_at", table_name="create_sessions")
    op.drop_index("ix_create_sessions_created_at", table_name="create_sessions")
    op.drop_index("ix_create_sessions_status", table_name="create_sessions")
    op.drop_index("ix_create_sessions_user_id", table_name="create_sessions")
    op.drop_index(
        "ix_generation_jobs_parent_job_id", table_name="generation_jobs"
    )
    op.drop_index(
        "ix_generation_jobs_create_session_id", table_name="generation_jobs"
    )
    op.drop_constraint(
        "fk_generation_jobs_parent_job_id_generation_jobs",
        "generation_jobs",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_generation_jobs_create_session_id_create_sessions",
        "generation_jobs",
        type_="foreignkey",
    )
    op.drop_column("generation_jobs", "material_usage")
    op.drop_column("generation_jobs", "game_plan")
    op.drop_column("generation_jobs", "user_requirements")
    op.drop_column("generation_jobs", "revision_intent")
    op.drop_column("generation_jobs", "parent_job_id")
    op.drop_column("generation_jobs", "create_session_id")
    op.drop_table("create_sessions")
