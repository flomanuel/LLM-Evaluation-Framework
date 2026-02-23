from __future__ import annotations

from pathlib import Path
from typing import List

from ..chatbot.openai_chatbot import OpenAIChatbot
from ..chatbot.store import ChatbotStore
from ..testcase.base import BaseTestCase
from ..testcase.indirect_prompt_injection_csv import IndirectPromptInjectionCsvTestCase
from ..testcase.illegal_activity import IllegalActivityTestCase
from .base_test import Test


class BaselineTest(Test):
    """Concrete Test implementation that runs a small set of example test cases."""

    def __init__(self, results_dir: Path | None = None) -> None:
        super().__init__(name="baseline", results_dir=results_dir)

    def setup_chatbots(self) -> None:
        # Register a single OpenAI chatbot for now.
        chatbot = OpenAIChatbot()
        ChatbotStore.add_chatbot(chatbot, name="default_openai")

    def get_test_cases(self) -> List[BaseTestCase]:
        return [
            IndirectPromptInjectionCsvTestCase(),
            IllegalActivityTestCase(),
        ]


