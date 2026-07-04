#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from testframework.enums import ChatbotName
from testframework.persistence.entity.chatbot_response import (
    ChatbotResponseEntity,
    ChatbotResponseEvaluationEntity,
)


class ChatbotResponseInputModel(BaseModel):
    """Input model for a raw chatbot response."""

    prompt: str
    raw_prompt: str
    response: str
    system_prompt: str
    prompt_tokens: int = Field(ge=0)
    response_tokens: int = Field(ge=0)
    tool_called: bool
    tool_name: str | None = None
    tool_args: Any | None = None
    rag_embedding_model: str | None = None
    rag_nodes: list[str] | None = None
    document_content: str | None = None
    file_path: str | None = None

    def to_entity(self) -> ChatbotResponseEntity:
        entity = ChatbotResponseEntity(
            evaluation_id=0,  # FK set by caller
            prompt=self.prompt,
            raw_prompt=self.raw_prompt,
            response=self.response,
            system_prompt=self.system_prompt,
            prompt_tokens=self.prompt_tokens,
            response_tokens=self.response_tokens,
            tool_called=self.tool_called,
            tool_name=self.tool_name,
            tool_args=self.tool_args,
            rag_embedding_model=self.rag_embedding_model,
            rag_nodes=self.rag_nodes,
            document_content=self.document_content,
            file_path=self.file_path,
        )
        return entity


class ChatbotResponseEvaluationInputModel(BaseModel):
    """Input model for a chatbot response evaluation (LLM-as-a-Judge result)."""

    chatbot_name: ChatbotName
    score: float = Field(ge=0.0, le=1.0)
    reason: str
    success: bool
    metric: str = Field(min_length=1)
    chatbot_response: ChatbotResponseInputModel | None = None

    def to_entity(self) -> ChatbotResponseEvaluationEntity:
        entity = ChatbotResponseEvaluationEntity(
            attack_id=0,  # FK set by caller
            chatbot_name=self.chatbot_name,
            score=self.score,
            reason=self.reason,
            success=self.success,
            metric=self.metric,
        )
        if self.chatbot_response is not None:
            resp = self.chatbot_response.to_entity()
            entity.chatbot_response = resp
        return entity
