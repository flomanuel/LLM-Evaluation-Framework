#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.



from __future__ import annotations

from typing import Dict

from loguru import logger
from testframework.chatbots.base import BaseChatbot
from testframework import ChatbotName


class ChatbotStore:
    """Static registry for chatbot instances."""

    _chatbots: Dict[ChatbotName, BaseChatbot] = {}

    @staticmethod
    def add_chatbot(chatbot: BaseChatbot) -> None:
        ChatbotStore._chatbots[chatbot.name] = chatbot
        logger.info(f"Registered chatbot '{chatbot.name.value}'")

    @staticmethod
    def remove_chatbot(name: ChatbotName) -> None:
        ChatbotStore._chatbots.pop(name, None)
        logger.info(f"Removed chatbot '{name.value}'")

    @staticmethod
    def get_chatbots() -> Dict[ChatbotName, BaseChatbot]:
        return ChatbotStore._chatbots

    @staticmethod
    def get_chatbot(name: ChatbotName) -> BaseChatbot | None:
        return ChatbotStore._chatbots.get(name)
