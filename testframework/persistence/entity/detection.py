#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Integer, Text, Boolean, Float, ForeignKey, Identity
from sqlalchemy.orm import Mapped, mapped_column, relationship

from testframework.persistence.entity.base import Base
from testframework.persistence.session import POSTGRES_SCHEMA


class DetectionResultEntity(Base):
    __tablename__ = "detection_result"

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True, init=False)
    attack_id: Mapped[int] = mapped_column(
        Integer, ForeignKey(f"{POSTGRES_SCHEMA}.attack.id", ondelete="CASCADE")
    )
    guardrail_name: Mapped[str] = mapped_column(Text)
    chatbot_name: Mapped[str] = mapped_column(Text)

    attack: Mapped[AttackEntity] = relationship(  # type: ignore[name-defined]
        "AttackEntity",
        back_populates="detection_results",
        init=False,
        default=None,
    )
    detection_elements: Mapped[list[DetectionElementEntity]] = relationship(
        "DetectionElementEntity",
        back_populates="detection_result",
        cascade="all, delete-orphan",
        init=False,
        default_factory=list,
    )

    __table_args__ = {"schema": POSTGRES_SCHEMA}


class DetectionElementEntity(Base):
    __tablename__ = "detection_element"

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True, init=False)
    detection_result_id: Mapped[int] = mapped_column(
        Integer, ForeignKey(f"{POSTGRES_SCHEMA}.detection_result.id", ondelete="CASCADE")
    )
    stage: Mapped[str] = mapped_column(Text)
    success: Mapped[bool] = mapped_column(Boolean)
    score: Mapped[float] = mapped_column(Float)
    judge_raw_response: Mapped[str] = mapped_column(Text)
    detected_type: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    latency: Mapped[float | None] = mapped_column(Float, nullable=True, default=None)
    error_type: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    error_timestamp: Mapped[datetime | None] = mapped_column(nullable=True, default=None)
    chatbot_response_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey(f"{POSTGRES_SCHEMA}.chatbot_response.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )

    detection_result: Mapped[DetectionResultEntity] = relationship(
        "DetectionResultEntity",
        back_populates="detection_elements",
        init=False,
        default=None,
    )
    scanner_details: Mapped[list[ScannerDetailEntity]] = relationship(
        "ScannerDetailEntity",
        back_populates="detection_element",
        cascade="all, delete-orphan",
        init=False,
        default_factory=list,
    )
    # Nullable FK to chatbot_response for prompt-hardening output elements
    prompt_hardening_chatbot_response: Mapped[ChatbotResponseEntity | None] = relationship(  # type: ignore[name-defined]
        "ChatbotResponseEntity",
        foreign_keys=[chatbot_response_id],
        init=False,
        default=None,
    )

    __table_args__ = {"schema": POSTGRES_SCHEMA}


class ScannerDetailEntity(Base):
    __tablename__ = "scanner_detail"

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True, init=False)
    detection_element_id: Mapped[int] = mapped_column(
        Integer, ForeignKey(f"{POSTGRES_SCHEMA}.detection_element.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(Text)
    score: Mapped[float] = mapped_column(Float)
    reason: Mapped[str] = mapped_column(Text)
    sanitized_input: Mapped[str] = mapped_column(Text)
    is_valid: Mapped[bool | None] = mapped_column(Boolean, nullable=True, default=None)

    detection_element: Mapped[DetectionElementEntity] = relationship(
        "DetectionElementEntity",
        back_populates="scanner_details",
        init=False,
        default=None,
    )

    __table_args__ = {"schema": POSTGRES_SCHEMA}
