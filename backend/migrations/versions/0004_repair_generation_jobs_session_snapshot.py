"""repair generation job session snapshot columns

Revision ID: 0004_repair_job_snapshots
Revises: 0003_create_sessions
Create Date: 2026-06-21 17:05:00
"""

from typing import Sequence, Union

from alembic import op


revision: str = "0004_repair_job_snapshots"
down_revision: Union[str, None] = "0003_create_sessions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 0003 was expanded during local development after some databases had already
    # been stamped at that revision. Keep this migration idempotent so both old
    # and fresh dev databases converge to the model shape.
    op.execute(
        """
        ALTER TABLE generation_jobs
        ADD COLUMN IF NOT EXISTS create_session_id UUID
        """
    )
    op.execute(
        """
        ALTER TABLE generation_jobs
        ADD COLUMN IF NOT EXISTS parent_job_id UUID
        """
    )
    op.execute(
        """
        ALTER TABLE generation_jobs
        ADD COLUMN IF NOT EXISTS revision_intent TEXT
        """
    )
    op.execute(
        """
        ALTER TABLE generation_jobs
        ADD COLUMN IF NOT EXISTS user_requirements JSON NOT NULL DEFAULT '{}'
        """
    )
    op.execute(
        """
        ALTER TABLE generation_jobs
        ADD COLUMN IF NOT EXISTS game_plan JSON NOT NULL DEFAULT '{}'
        """
    )
    op.execute(
        """
        ALTER TABLE generation_jobs
        ADD COLUMN IF NOT EXISTS material_usage JSON NOT NULL DEFAULT '{}'
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'fk_generation_jobs_create_session_id_create_sessions'
            ) THEN
                ALTER TABLE generation_jobs
                ADD CONSTRAINT fk_generation_jobs_create_session_id_create_sessions
                FOREIGN KEY (create_session_id)
                REFERENCES create_sessions (id)
                ON DELETE SET NULL;
            END IF;
        END
        $$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'fk_generation_jobs_parent_job_id_generation_jobs'
            ) THEN
                ALTER TABLE generation_jobs
                ADD CONSTRAINT fk_generation_jobs_parent_job_id_generation_jobs
                FOREIGN KEY (parent_job_id)
                REFERENCES generation_jobs (id)
                ON DELETE SET NULL;
            END IF;
        END
        $$;
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_generation_jobs_create_session_id
        ON generation_jobs (create_session_id)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_generation_jobs_parent_job_id
        ON generation_jobs (parent_job_id)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_generation_jobs_parent_job_id")
    op.execute("DROP INDEX IF EXISTS ix_generation_jobs_create_session_id")
    op.execute(
        """
        ALTER TABLE generation_jobs
        DROP CONSTRAINT IF EXISTS fk_generation_jobs_parent_job_id_generation_jobs
        """
    )
    op.execute(
        """
        ALTER TABLE generation_jobs
        DROP CONSTRAINT IF EXISTS fk_generation_jobs_create_session_id_create_sessions
        """
    )
    op.execute("ALTER TABLE generation_jobs DROP COLUMN IF EXISTS material_usage")
    op.execute("ALTER TABLE generation_jobs DROP COLUMN IF EXISTS game_plan")
    op.execute("ALTER TABLE generation_jobs DROP COLUMN IF EXISTS user_requirements")
    op.execute("ALTER TABLE generation_jobs DROP COLUMN IF EXISTS revision_intent")
    op.execute("ALTER TABLE generation_jobs DROP COLUMN IF EXISTS parent_job_id")
    op.execute("ALTER TABLE generation_jobs DROP COLUMN IF EXISTS create_session_id")
