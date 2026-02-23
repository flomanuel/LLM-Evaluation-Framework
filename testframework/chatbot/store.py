from __future__ import annotations

from typing import Dict

from .base import BaseChatbot
from .. import Chatbot


class ChatbotStore:
    """Static registry for chatbot instances."""

    _chatbots: Dict[Chatbot, BaseChatbot] = {}

    @staticmethod
    def add_chatbot(chatbot: BaseChatbot, name: Chatbot) -> None:
        ChatbotStore._chatbots[name] = chatbot

    @staticmethod
    def remove_chatbot(name: Chatbot) -> None:
        ChatbotStore._chatbots.pop(name, None)

    @staticmethod
    def get_chatbots() -> Dict[Chatbot, BaseChatbot]:
        return dict(ChatbotStore._chatbots)

    @staticmethod
    def get_chatbot(name: Chatbot) -> BaseChatbot | None:
        return ChatbotStore._chatbots.get(name)
