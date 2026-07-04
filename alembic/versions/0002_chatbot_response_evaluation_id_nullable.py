"""chatbot_response.evaluation_id nullable

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-05

"""
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, Sequence[str], None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "evaluation"


def upgrade() -> None:
    """Allow chatbot_response rows with no owning evaluation (prompt-hardening artifacts)."""
    op.alter_column(
        "chatbot_response",
        "evaluation_id",
        existing_type=sa.Integer(),
        nullable=True,
        schema=SCHEMA,
    )


def downgrade() -> None:
    op.alter_column(
        "chatbot_response",
        "evaluation_id",
        existing_type=sa.Integer(),
        nullable=False,
        schema=SCHEMA,
    )
