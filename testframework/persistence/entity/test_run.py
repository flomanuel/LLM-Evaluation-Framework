#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

from __future__ import annotations

from datetime import datetime

from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from testframework.persistence.entity.base import Base
from testframework.persistence.session import POSTGRES_SCHEMA


class TestRunEntity(Base):
    __tablename__ = "test_run"

    run_id: Mapped[str] = mapped_column(String, primary_key=True)
    start_ts: Mapped[datetime]
    end_ts: Mapped[datetime | None] = mapped_column(nullable=True, default=None)
    version: Mapped[int] = mapped_column(Integer, default=1)

    test_cases: Mapped[list[TestCaseEntity]] = relationship(  # type: ignore[name-defined]
        "TestCaseEntity",
        back_populates="test_run",
        cascade="all, delete-orphan",
        init=False,
        default_factory=list,
    )
    analysis_runs: Mapped[list[AnalysisRunEntity]] = relationship(  # type: ignore[name-defined]
        "AnalysisRunEntity",
        back_populates="test_run",
        cascade="all, delete-orphan",
        init=False,
        default_factory=list,
    )

    __mapper_args__ = {"version_id_col": version}
    __table_args__ = {"schema": POSTGRES_SCHEMA}
