"""add generation job validation report

Revision ID: 0005_job_validation_report
Revises: 0004_repair_job_snapshots
Create Date: 2026-06-21 18:10:00
"""

from typing import Sequence, Union

from alembic import op


revision: str = "0005_job_validation_report"
down_revision: Union[str, None] = "0004_repair_job_snapshots"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE generation_jobs
        ADD COLUMN IF NOT EXISTS validation_report JSON
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE generation_jobs DROP COLUMN IF EXISTS validation_report")
