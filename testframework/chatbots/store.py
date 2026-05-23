#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.



from loguru import logger
from testframework.chatbots.base import BaseChatbot
from testframework import ChatbotName


class ChatbotStore:
    """Static registry for chatbot instances."""

    _chatbots: dict[ChatbotName, BaseChatbot] = {}

    @staticmethod
    def add_chatbot(chatbot: BaseChatbot) -> None:
        """Add a chatbot to the store."""
        ChatbotStore._chatbots[chatbot.name] = chatbot
        logger.info("Registered chatbot '{}'", chatbot.name.value)

    @staticmethod
    def remove_chatbot(name: ChatbotName) -> None:
        """Remove a chatbot from the store."""
        ChatbotStore._chatbots.pop(name, None)
        logger.info("Removed chatbot '{}'", name.value)

    @staticmethod
    def get_chatbots() -> dict[ChatbotName, BaseChatbot]:
        """Get all registered chatbots."""
        return ChatbotStore._chatbots

    @staticmethod
    def get_chatbot(name: ChatbotName) -> BaseChatbot | None:
        """Get a chatbot by name."""
        return ChatbotStore._chatbots.get(name)
