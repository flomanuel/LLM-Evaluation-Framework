#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

import os
import pytest

from testcontainers.postgres import PostgresContainer
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

import testframework.persistence.session as _session_module
from testframework.persistence.entity.base import Base

# Import all entities so their tables are registered on metadata
import testframework.persistence.entity.test_run  # noqa: F401
import testframework.persistence.entity.test_case  # noqa: F401
import testframework.persistence.entity.attack  # noqa: F401
import testframework.persistence.entity.chatbot_response  # noqa: F401
import testframework.persistence.entity.detection  # noqa: F401
import testframework.persistence.entity.analysis  # noqa: F401

from alembic.config import Config
from alembic import command


@pytest.fixture(scope="session")
def pg_container():
    """Start a Postgres container for the whole test session."""
    with PostgresContainer("postgres:16") as pg:
        yield pg


@pytest.fixture(scope="session")
def db_engine(pg_container):
    """Create an engine pointing at the test container and run migrations."""
    url = pg_container.get_connection_url(driver="psycopg")

    engine = create_engine(url, pool_pre_ping=True)

    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", url)

    command.upgrade(alembic_cfg, "head")

    _session_module.engine = engine
    _session_module.Session = sessionmaker(engine, autoflush=False)

    yield engine

    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    """Provide a transactional session that rolls back after each test."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection, autoflush=False)()

    yield session

    session.close()
    transaction.rollback()
    connection.close()
