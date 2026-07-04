"""initial

Revision ID: 0001
Revises:
Create Date: 2026-07-04

"""
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "evaluation"


def upgrade() -> None:
    """Create evaluation schema and all tables."""
    op.execute(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}")

    op.create_table(
        "test_run",
        sa.Column("run_id", sa.String(), nullable=False),
        sa.Column("start_ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_ts", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.PrimaryKeyConstraint("run_id", name=op.f("pk_test_run")),
        schema=SCHEMA,
    )

    op.create_table(
        "test_case",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("run_id", sa.String(), nullable=False),
        sa.Column("category", sa.Text(), nullable=False),
        sa.Column("model_attack_generation", sa.Text(), nullable=True),
        sa.Column("subcategories", postgresql.ARRAY(sa.Text()), nullable=False),
        sa.Column("generation_error_type", sa.Text(), nullable=True),
        sa.Column("generation_error_message", sa.Text(), nullable=True),
        sa.Column("generation_error_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("enhancement_error_type", sa.Text(), nullable=True),
        sa.Column("enhancement_error_message", sa.Text(), nullable=True),
        sa.Column("enhancement_error_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["run_id"], [f"{SCHEMA}.test_run.run_id"],
            name=op.f("fk_test_case_run_id_test_run"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_test_case")),
        schema=SCHEMA,
    )

    op.create_table(
        "attack",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("test_case_id", sa.Integer(), nullable=False),
        sa.Column("category", sa.Text(), nullable=False),
        sa.Column("severity", sa.Text(), nullable=False),
        sa.Column("prompt_baseline", sa.Text(), nullable=False),
        sa.Column("prompt_enhanced", sa.Text(), nullable=False),
        sa.Column("subcategory", sa.Text(), nullable=True),
        sa.Column("techniques", postgresql.ARRAY(sa.Text()), nullable=False),
        sa.Column("error_type", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("error_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["test_case_id"], [f"{SCHEMA}.test_case.id"],
            name=op.f("fk_attack_test_case_id_test_case"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_attack")),
        schema=SCHEMA,
    )

    op.create_table(
        "chatbot_response_evaluation",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("attack_id", sa.Integer(), nullable=False),
        sa.Column("chatbot_name", sa.Text(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("metric", sa.Text(), nullable=False),
        sa.Column("error_type", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("error_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["attack_id"], [f"{SCHEMA}.attack.id"],
            name=op.f("fk_chatbot_response_evaluation_attack_id_attack"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_chatbot_response_evaluation")),
        schema=SCHEMA,
    )

    op.create_table(
        "chatbot_response",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("evaluation_id", sa.Integer(), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("raw_prompt", sa.Text(), nullable=False),
        sa.Column("response", sa.Text(), nullable=False),
        sa.Column("system_prompt", sa.Text(), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=False),
        sa.Column("response_tokens", sa.Integer(), nullable=False),
        sa.Column("tool_called", sa.Boolean(), nullable=False),
        sa.Column("tool_name", sa.Text(), nullable=True),
        sa.Column("tool_args", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("rag_embedding_model", sa.Text(), nullable=True),
        sa.Column("rag_nodes", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("document_content", sa.Text(), nullable=True),
        sa.Column("file_path", sa.Text(), nullable=True),
        sa.Column("error_type", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("error_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["evaluation_id"], [f"{SCHEMA}.chatbot_response_evaluation.id"],
            name=op.f("fk_chatbot_response_evaluation_id_chatbot_response_evaluation"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_chatbot_response")),
        schema=SCHEMA,
    )

    op.create_table(
        "detection_result",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("attack_id", sa.Integer(), nullable=False),
        sa.Column("guardrail_name", sa.Text(), nullable=False),
        sa.Column("chatbot_name", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["attack_id"], [f"{SCHEMA}.attack.id"],
            name=op.f("fk_detection_result_attack_id_attack"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_detection_result")),
        schema=SCHEMA,
    )

    op.create_table(
        "detection_element",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("detection_result_id", sa.Integer(), nullable=False),
        sa.Column("stage", sa.Text(), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("judge_raw_response", sa.Text(), nullable=False),
        sa.Column("detected_type", sa.Text(), nullable=True),
        sa.Column("latency", sa.Float(), nullable=True),
        sa.Column("error_type", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("error_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("chatbot_response_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["detection_result_id"], [f"{SCHEMA}.detection_result.id"],
            name=op.f("fk_detection_element_detection_result_id_detection_result"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["chatbot_response_id"], [f"{SCHEMA}.chatbot_response.id"],
            name=op.f("fk_detection_element_chatbot_response_id_chatbot_response"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_detection_element")),
        schema=SCHEMA,
    )

    op.create_table(
        "scanner_detail",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("detection_element_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("sanitized_input", sa.Text(), nullable=False),
        sa.Column("is_valid", sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(
            ["detection_element_id"], [f"{SCHEMA}.detection_element.id"],
            name=op.f("fk_scanner_detail_detection_element_id_detection_element"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_scanner_detail")),
        schema=SCHEMA,
    )

    op.create_table(
        "analysis_run",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("run_id", sa.String(), nullable=False),
        sa.Column("exclude_scanners", sa.Boolean(), nullable=False),
        sa.Column("consider_chatbot_success", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["run_id"], [f"{SCHEMA}.test_run.run_id"],
            name=op.f("fk_analysis_run_run_id_test_run"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_analysis_run")),
        schema=SCHEMA,
    )

    op.create_table(
        "summary_row",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("analysis_run_id", sa.Integer(), nullable=False),
        sa.Column("node", sa.Text(), nullable=False),
        sa.Column("scope", sa.Text(), nullable=False),
        sa.Column("attack_category", sa.Text(), nullable=False),
        sa.Column("technique", sa.Text(), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False),
        sa.Column("tp", sa.Integer(), nullable=False),
        sa.Column("fp", sa.Integer(), nullable=False),
        sa.Column("tn", sa.Integer(), nullable=False),
        sa.Column("fn", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["analysis_run_id"], [f"{SCHEMA}.analysis_run.id"],
            name=op.f("fk_summary_row_analysis_run_id_analysis_run"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_summary_row")),
        schema=SCHEMA,
    )

    op.create_table(
        "summary_error",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("analysis_run_id", sa.Integer(), nullable=False),
        sa.Column("node", sa.Text(), nullable=False),
        sa.Column("attack_category", sa.Text(), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["analysis_run_id"], [f"{SCHEMA}.analysis_run.id"],
            name=op.f("fk_summary_error_analysis_run_id_analysis_run"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_summary_error")),
        schema=SCHEMA,
    )


def downgrade() -> None:
    """Drop all tables (schema is left intact for Alembic version tracking)."""
    op.drop_table("summary_error", schema=SCHEMA)
    op.drop_table("summary_row", schema=SCHEMA)
    op.drop_table("analysis_run", schema=SCHEMA)
    op.drop_table("scanner_detail", schema=SCHEMA)
    op.drop_table("detection_element", schema=SCHEMA)
    op.drop_table("detection_result", schema=SCHEMA)
    op.drop_table("chatbot_response", schema=SCHEMA)
    op.drop_table("chatbot_response_evaluation", schema=SCHEMA)
    op.drop_table("attack", schema=SCHEMA)
    op.drop_table("test_case", schema=SCHEMA)
    op.drop_table("test_run", schema=SCHEMA)
