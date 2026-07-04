#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

_HOST = os.environ.get("EVAL_DB_HOST", "localhost")
_PORT = os.environ.get("EVAL_DB_PORT", "5433")
_USER = os.environ.get("EVAL_DB_USER", "postgres")
_PASSWORD = os.environ.get("EVAL_DB_PASSWORD", "postgres")
_DB = os.environ.get("EVAL_DB_NAME", "evaluation_db")
POSTGRES_SCHEMA: str = os.environ.get("POSTGRES_SCHEMA", "evaluation")

DATABASE_URL = f"postgresql+psycopg://{_USER}:{_PASSWORD}@{_HOST}:{_PORT}/{_DB}"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
Session = sessionmaker(engine, autoflush=False)
