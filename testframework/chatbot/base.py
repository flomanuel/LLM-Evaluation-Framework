from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict

from ..models import ModelResponse


class BaseChatbot(ABC):
    """Abstract base class for all chatbots used in tests."""

    model_name: str

    def __init__(self, model_name: str) -> None:
        self.model_name = model_name

    @abstractmethod
    def query(
        self,
        user_prompt: str,
        is_rag: bool = True,
        file_path: str | None = None,
        system_prompt: str | None = None,
    ) -> Dict[str, ModelResponse]:
        """Query the chatbot and return a mapping from model identifier to ModelResponse."""
        raise NotImplementedError


