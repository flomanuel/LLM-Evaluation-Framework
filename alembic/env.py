import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# Import all entity modules so their tables are registered on the metadata
import testframework.persistence.entity.test_run  # noqa: F401
import testframework.persistence.entity.test_case  # noqa: F401
import testframework.persistence.entity.attack  # noqa: F401
import testframework.persistence.entity.chatbot_response  # noqa: F401
import testframework.persistence.entity.detection  # noqa: F401
import testframework.persistence.entity.analysis  # noqa: F401
from testframework.persistence.entity.base import Base
from testframework.persistence.session import POSTGRES_SCHEMA

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

_host = os.environ.get("POSTGRES_HOST", "localhost")
_port = os.environ.get("POSTGRES_PORT", "5432")
_user = os.environ.get("POSTGRES_USER", "postgres")
_password = os.environ.get("POSTGRES_PASSWORD", "postgres")
_db = os.environ.get("POSTGRES_DB", "vectordb")
DATABASE_URL = f"postgresql+psycopg://{_user}:{_password}@{_host}:{_port}/{_db}"


def _include_object(obj, name, type_, reflected, compare_to):
    """Only autogenerate for objects in the evaluation schema."""
    if type_ == "table":
        return getattr(obj, "schema", None) == POSTGRES_SCHEMA
    if type_ == "schema":
        return name == POSTGRES_SCHEMA
    return True


def run_migrations_offline() -> None:
    """Run migrations in offline mode."""
    url = config.get_main_option("sqlalchemy.url") or DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
        include_object=_include_object,
        version_table_schema=POSTGRES_SCHEMA,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in online mode."""
    from sqlalchemy import text

    cfg = config.get_section(config.config_ini_section, {})
    cfg.setdefault("sqlalchemy.url", DATABASE_URL)

    connectable = engine_from_config(
        cfg,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {POSTGRES_SCHEMA}"))
        connection.commit()
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            include_object=_include_object,
            version_table_schema=POSTGRES_SCHEMA,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
