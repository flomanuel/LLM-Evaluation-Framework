#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Integer, Text, Boolean, Float, ForeignKey, Identity
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from testframework.persistence.entity.base import Base
from testframework.persistence.session import POSTGRES_SCHEMA


class ChatbotResponseEvaluationEntity(Base):
    __tablename__ = "chatbot_response_evaluation"

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True, init=False)
    attack_id: Mapped[int] = mapped_column(
        Integer, ForeignKey(f"{POSTGRES_SCHEMA}.attack.id", ondelete="CASCADE")
    )
    chatbot_name: Mapped[str] = mapped_column(Text)
    score: Mapped[float] = mapped_column(Float)
    reason: Mapped[str] = mapped_column(Text)
    success: Mapped[bool] = mapped_column(Boolean)
    metric: Mapped[str] = mapped_column(Text)
    error_type: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    error_timestamp: Mapped[datetime | None] = mapped_column(nullable=True, default=None)

    attack: Mapped[AttackEntity] = relationship(  # type: ignore[name-defined]
        "AttackEntity",
        back_populates="evaluations",
        init=False,
        default=None,
    )
    chatbot_response: Mapped[ChatbotResponseEntity | None] = relationship(
        "ChatbotResponseEntity",
        back_populates="evaluation",
        cascade="all, delete-orphan",
        uselist=False,
        init=False,
        default=None,
    )

    __table_args__ = {"schema": POSTGRES_SCHEMA}


class ChatbotResponseEntity(Base):
    __tablename__ = "chatbot_response"

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True, init=False)
    evaluation_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(f"{POSTGRES_SCHEMA}.chatbot_response_evaluation.id", ondelete="CASCADE"),
    )
    prompt: Mapped[str] = mapped_column(Text)
    raw_prompt: Mapped[str] = mapped_column(Text)
    response: Mapped[str] = mapped_column(Text)
    system_prompt: Mapped[str] = mapped_column(Text)
    prompt_tokens: Mapped[int] = mapped_column(Integer)
    response_tokens: Mapped[int] = mapped_column(Integer)
    tool_called: Mapped[bool] = mapped_column(Boolean)
    tool_name: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    tool_args: Mapped[Any | None] = mapped_column(JSONB, nullable=True, default=None)
    rag_embedding_model: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    rag_nodes: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True, default=None)
    document_content: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    file_path: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    error_type: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    error_timestamp: Mapped[datetime | None] = mapped_column(nullable=True, default=None)

    evaluation: Mapped[ChatbotResponseEvaluationEntity] = relationship(
        "ChatbotResponseEvaluationEntity",
        back_populates="chatbot_response",
        init=False,
        default=None,
    )

    __table_args__ = {"schema": POSTGRES_SCHEMA}
