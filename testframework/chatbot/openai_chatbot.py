from __future__ import annotations

import uuid
from loguru import logger

from ..enums import ChatbotName
from ..models import ToolInfo, ChatbotResponse, ModelConfig
from .base import BaseChatbot


class DummyChatbot(BaseChatbot):
    """Dummy chatbot implementation."""

    def __init__(self, name: ChatbotName = ChatbotName.DUMMY) -> None:
        super().__init__(name=name)
        logger.debug(f"Dummy chatbot initialized.")

    def query(
            self,
            user_prompt: str,
            is_rag: bool = True,
            file_path: str | None = None,
            system_prompt: str | None = None,
    ) -> ChatbotResponse:
        message = f"Lorem ipsum dolor sit amet, consectetur adipiscing elit.{uuid.uuid4()}"
        return ChatbotResponse(
            response=message,
            system_prompt=system_prompt,
            tool=ToolInfo(tool_called=False, tool_call_params=None),
            llm_params=ModelConfig(temperature=-1),
            prompt_tokens=-1,
            response_tokens=-1,
            rag_context=None,
            file_path=file_path,
        )
