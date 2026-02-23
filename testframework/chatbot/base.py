from __future__ import annotations

from abc import ABC, abstractmethod

from testframework import ChatbotName
from testframework.models import ChatbotResponse


class BaseChatbot(ABC):
    """Abstract base class for all chatbots used in tests."""

    # LLM generation parameters - must be defined by each concrete chatbot class
    temperature: float
    top_p: float
    top_k: int | None
    max_tokens: int

    def __init__(self, name: ChatbotName) -> None:
        self.name = name

    @abstractmethod
    def query(
            self,
            user_prompt: str,
            is_rag: bool = True,
            file_path: str | None = None,
            system_prompt: str | None = None,
    ) -> ChatbotResponse:
        """Query the chatbot and return a mapping from model identifier to ModelResponse."""
        raise NotImplementedError
