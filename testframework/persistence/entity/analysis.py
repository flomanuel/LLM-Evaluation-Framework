#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Integer, String, Text, Boolean, ForeignKey, Identity
from sqlalchemy.orm import Mapped, mapped_column, relationship

from testframework.persistence.entity.base import Base
from testframework.persistence.session import POSTGRES_SCHEMA


class AnalysisRunEntity(Base):
    __tablename__ = "analysis_run"

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True, init=False)
    run_id: Mapped[str] = mapped_column(
        String, ForeignKey(f"{POSTGRES_SCHEMA}.test_run.run_id", ondelete="CASCADE")
    )
    exclude_scanners: Mapped[bool] = mapped_column(Boolean)
    consider_chatbot_success: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[datetime]

    test_run: Mapped[TestRunEntity] = relationship(  # type: ignore[name-defined]
        "TestRunEntity",
        back_populates="analysis_runs",
        init=False,
        default=None,
    )
    summary_rows: Mapped[list[SummaryRowEntity]] = relationship(
        "SummaryRowEntity",
        back_populates="analysis_run",
        cascade="all, delete-orphan",
        init=False,
        default_factory=list,
    )
    summary_errors: Mapped[list[SummaryErrorEntity]] = relationship(
        "SummaryErrorEntity",
        back_populates="analysis_run",
        cascade="all, delete-orphan",
        init=False,
        default_factory=list,
    )

    __table_args__ = {"schema": POSTGRES_SCHEMA}


class SummaryRowEntity(Base):
    __tablename__ = "summary_row"

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True, init=False)
    analysis_run_id: Mapped[int] = mapped_column(
        Integer, ForeignKey(f"{POSTGRES_SCHEMA}.analysis_run.id", ondelete="CASCADE")
    )
    node: Mapped[str] = mapped_column(Text)
    scope: Mapped[str] = mapped_column(Text)
    attack_category: Mapped[str] = mapped_column(Text)
    technique: Mapped[str] = mapped_column(Text)
    count: Mapped[int] = mapped_column(Integer)
    tp: Mapped[int] = mapped_column(Integer)
    fp: Mapped[int] = mapped_column(Integer)
    tn: Mapped[int] = mapped_column(Integer)
    fn: Mapped[int] = mapped_column(Integer)

    analysis_run: Mapped[AnalysisRunEntity] = relationship(
        "AnalysisRunEntity",
        back_populates="summary_rows",
        init=False,
        default=None,
    )

    __table_args__ = {"schema": POSTGRES_SCHEMA}


class SummaryErrorEntity(Base):
    __tablename__ = "summary_error"

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True, init=False)
    analysis_run_id: Mapped[int] = mapped_column(
        Integer, ForeignKey(f"{POSTGRES_SCHEMA}.analysis_run.id", ondelete="CASCADE")
    )
    node: Mapped[str] = mapped_column(Text)
    attack_category: Mapped[str] = mapped_column(Text)
    count: Mapped[int] = mapped_column(Integer)

    analysis_run: Mapped[AnalysisRunEntity] = relationship(
        "AnalysisRunEntity",
        back_populates="summary_errors",
        init=False,
        default=None,
    )

    __table_args__ = {"schema": POSTGRES_SCHEMA}
