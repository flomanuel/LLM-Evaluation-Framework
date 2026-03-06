#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

from __future__ import annotations

import uuid
from loguru import logger
from testframework.enums import ChatbotName
from testframework.models import ToolInfo, ChatbotResponse
from testframework.chatbots.base import BaseChatbot


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
            prompt=user_prompt,
            raw_prompt=user_prompt,
            response=message,
            system_prompt=system_prompt or "",
            tool=ToolInfo(tool_called=False),
            prompt_tokens=-1,
            response_tokens=-1,
            rag_context=None,
            file_path=file_path,
        )
