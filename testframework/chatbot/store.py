from __future__ import annotations

from typing import Dict

from .base import BaseChatbot


class ChatbotStore:
    """Static registry for chatbot instances."""

    _chatbots: Dict[str, BaseChatbot] = {}

    @staticmethod
    def add_chatbot(chatbot: BaseChatbot, name: str) -> None:
        ChatbotStore._chatbots[name] = chatbot

    @staticmethod
    def remove_chatbot(name: str) -> None:
        ChatbotStore._chatbots.pop(name, None)

    @staticmethod
    def get_chatbots() -> Dict[str, BaseChatbot]:
        return dict(ChatbotStore._chatbots)

    @staticmethod
    def get_chatbot(name: str) -> BaseChatbot | None:
        return ChatbotStore._chatbots.get(name)


