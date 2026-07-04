#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Integer, String, Text, ForeignKey, Identity
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from testframework.persistence.entity.base import Base
from testframework.persistence.session import POSTGRES_SCHEMA


class TestCaseEntity(Base):
    __tablename__ = "test_case"

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True, init=False)
    run_id: Mapped[str] = mapped_column(
        String, ForeignKey(f"{POSTGRES_SCHEMA}.test_run.run_id", ondelete="CASCADE")
    )
    category: Mapped[str] = mapped_column(Text)
    model_attack_generation: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    subcategories: Mapped[list[str]] = mapped_column(ARRAY(Text), default_factory=list)
    generation_error_type: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    generation_error_message: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    generation_error_timestamp: Mapped[datetime | None] = mapped_column(nullable=True, default=None)
    enhancement_error_type: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    enhancement_error_message: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    enhancement_error_timestamp: Mapped[datetime | None] = mapped_column(nullable=True, default=None)

    test_run: Mapped[TestRunEntity] = relationship(  # type: ignore[name-defined]
        "TestRunEntity",
        back_populates="test_cases",
        init=False,
        default=None,
    )
    attacks: Mapped[list[AttackEntity]] = relationship(  # type: ignore[name-defined]
        "AttackEntity",
        back_populates="test_case",
        cascade="all, delete-orphan",
        init=False,
        default_factory=list,
    )

    __table_args__ = {"schema": POSTGRES_SCHEMA}
