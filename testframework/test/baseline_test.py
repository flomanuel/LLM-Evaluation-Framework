from __future__ import annotations

from pathlib import Path
from typing import List

from testframework import ChatbotName
from testframework.chatbot import LangChainChatbot, VectorStore
from testframework.chatbot.store import ChatbotStore
from testframework.testcase.base import BaseTestCase
from testframework.testcase.illegal_activity import IllegalActivityTestCase
from testframework.test.base_test import Test


class BaselineTest(Test):
    """Concrete Test implementation that runs a small set of example test cases."""

    def __init__(self, results_dir: Path | None = None) -> None:
        super().__init__(name="baseline", results_dir=results_dir)

    def setup_chatbots(self) -> None:
        # Register a single OpenAI chatbot for now.
        # chatbot = DummyChatbot()
        vector_store = VectorStore()
        rag_chatbot = LangChainChatbot(vector_store=vector_store)
        # todo: RAG chatbot - create two chatbot instances, one for GPT_4.1 and one dor GPT_5.1 -> make the same rag class configurable
        ChatbotStore.add_chatbot(rag_chatbot, ChatbotName.LANGCHAIN)

    def get_test_cases(self) -> List[BaseTestCase]:
        return [
            IllegalActivityTestCase(),
        ]
