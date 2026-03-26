#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

from __future__ import annotations

from abc import ABC, abstractmethod

from testframework import ChatbotName
from testframework.models import ChatbotResponse


class BaseChatbot(ABC):
    """Abstract base class for all chatbots used in tests."""

    def __init__(self, name: ChatbotName) -> None:
        self.name = name

    def prepare_for_test_case(self) -> None:
        """Prepare chatbot resources before a test case starts."""

    def cleanup_after_test_case(self) -> None:
        """Release chatbot resources after a test case finishes."""

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
