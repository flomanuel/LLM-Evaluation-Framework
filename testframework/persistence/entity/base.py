#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass

from testframework.persistence.session import POSTGRES_SCHEMA

_metadata = MetaData(schema=POSTGRES_SCHEMA)


class Base(MappedAsDataclass, DeclarativeBase):
    metadata = _metadata
