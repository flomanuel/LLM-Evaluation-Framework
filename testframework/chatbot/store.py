from __future__ import annotations

from typing import Dict

from .base import BaseChatbot
from .. import ChatbotName


class ChatbotStore:
    """Static registry for chatbot instances."""

    _chatbots: Dict[ChatbotName, BaseChatbot] = {}

    @staticmethod
    def add_chatbot(chatbot: BaseChatbot, name: ChatbotName) -> None:
        ChatbotStore._chatbots[name] = chatbot

    @staticmethod
    def remove_chatbot(name: ChatbotName) -> None:
        ChatbotStore._chatbots.pop(name, None)

    @staticmethod
    def get_chatbots() -> Dict[ChatbotName, BaseChatbot]:
        return ChatbotStore._chatbots

    @staticmethod
    def get_chatbot(name: ChatbotName) -> BaseChatbot | None:
        return ChatbotStore._chatbots.get(name)
