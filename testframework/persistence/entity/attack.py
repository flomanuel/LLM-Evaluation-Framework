#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Integer, Text, ForeignKey, Identity
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from testframework.persistence.entity.base import Base
from testframework.persistence.session import POSTGRES_SCHEMA


class AttackEntity(Base):
    __tablename__ = "attack"

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True, init=False)
    test_case_id: Mapped[int] = mapped_column(
        Integer, ForeignKey(f"{POSTGRES_SCHEMA}.test_case.id", ondelete="CASCADE")
    )
    category: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(Text)
    prompt_baseline: Mapped[str] = mapped_column(Text)
    prompt_enhanced: Mapped[str] = mapped_column(Text)
    subcategory: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    techniques: Mapped[list[str]] = mapped_column(ARRAY(Text), default_factory=list)
    error_type: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    error_timestamp: Mapped[datetime | None] = mapped_column(nullable=True, default=None)

    test_case: Mapped[TestCaseEntity] = relationship(  # type: ignore[name-defined]
        "TestCaseEntity",
        back_populates="attacks",
        init=False,
        default=None,
    )
    evaluations: Mapped[list[ChatbotResponseEvaluationEntity]] = relationship(  # type: ignore[name-defined]
        "ChatbotResponseEvaluationEntity",
        back_populates="attack",
        cascade="all, delete-orphan",
        init=False,
        default_factory=list,
    )
    detection_results: Mapped[list[DetectionResultEntity]] = relationship(  # type: ignore[name-defined]
        "DetectionResultEntity",
        back_populates="attack",
        cascade="all, delete-orphan",
        init=False,
        default_factory=list,
    )

    __table_args__ = {"schema": POSTGRES_SCHEMA}
