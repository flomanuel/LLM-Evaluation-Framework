#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

import pytest

from sqlalchemy import inspect, text


def test_upgrade_creates_evaluation_schema(db_engine):
    """Migration creates the evaluation schema."""
    with db_engine.connect() as conn:
        result = conn.execute(
            text("SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'evaluation'")
        )
        assert result.fetchone() is not None


def test_upgrade_creates_all_tables(db_engine):
    """Migration creates all expected tables in the evaluation schema."""
    expected = {
        "test_run", "test_case", "attack",
        "chatbot_response_evaluation", "chatbot_response",
        "detection_result", "detection_element", "scanner_detail",
        "analysis_run", "summary_row", "summary_error",
    }
    inspector = inspect(db_engine)
    tables = set(inspector.get_table_names(schema="evaluation"))
    assert expected <= tables


def test_downgrade_drops_all_tables(pg_container):
    """Migration downgrade removes all domain tables (schema remains for Alembic)."""
    from sqlalchemy import create_engine
    from alembic.config import Config
    from alembic import command

    url = pg_container.get_connection_url(driver="psycopg")
    engine = create_engine(url)

    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", url)

    command.downgrade(alembic_cfg, "base")

    inspector = inspect(engine)
    tables = set(inspector.get_table_names(schema="evaluation"))
    domain_tables = tables - {"alembic_version"}
    assert domain_tables == set(), f"Expected no domain tables, found: {domain_tables}"

    command.upgrade(alembic_cfg, "head")

    engine.dispose()
