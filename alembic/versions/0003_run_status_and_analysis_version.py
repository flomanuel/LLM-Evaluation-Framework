"""test_run status/status_error, analysis_run.version

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-05

"""
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, Sequence[str], None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "evaluation"


def upgrade() -> None:
    """Add run lifecycle status columns to test_run and a version column to analysis_run."""
    op.add_column(
        "test_run",
        sa.Column("status", sa.Text(), nullable=False, server_default="pending"),
        schema=SCHEMA,
    )
    op.add_column(
        "test_run",
        sa.Column("status_error", sa.Text(), nullable=True),
        schema=SCHEMA,
    )
    op.add_column(
        "analysis_run",
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        schema=SCHEMA,
    )


def downgrade() -> None:
    op.drop_column("analysis_run", "version", schema=SCHEMA)
    op.drop_column("test_run", "status_error", schema=SCHEMA)
    op.drop_column("test_run", "status", schema=SCHEMA)
