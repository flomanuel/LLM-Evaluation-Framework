#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

from testframework import ChatbotName
from testframework.chatbots.base import BaseChatbot
from testframework.chatbots.dummy_chatbot import DummyChatbot
from testframework.chatbots.langchain_ollama_chatbot import LangChainOllamaChatbot
from testframework.chatbots.store import ChatbotStore
from testframework.enums import Category
from testframework.models import AttackEnhancementResult, ChatbotResponse, ToolInfo
from testframework.testcases.base import BaseTestCase
from testframework.testcases.excessive_agency.test_case import ExcessiveAgencyTestCase
from testframework.tests.default_test import DefaultTest


class _TrackingChatbot(BaseChatbot):
    def __init__(self, name: ChatbotName, events: list[str]) -> None:
        super().__init__(name=name)
        self._events = events

    def prepare_for_test_case(self) -> None:
        self._events.append(f"prepare:{self.name.value}")

    def cleanup_after_test_case(self) -> None:
        self._events.append(f"cleanup:{self.name.value}")

    def query(
            self,
            user_prompt: str,
            is_rag: bool = True,
            file_path: str | None = None,
            system_prompt: str | None = None,
    ) -> ChatbotResponse:
        del is_rag, file_path, system_prompt
        return ChatbotResponse(
            prompt=user_prompt,
            raw_prompt=user_prompt,
            response="ok",
            system_prompt="",
            tool=ToolInfo(tool_called=False),
            prompt_tokens=-1,
            response_tokens=-1,
            rag_context=None,
            document_content=None,
        )


class _TrackingOllamaChatbot(LangChainOllamaChatbot):
    def __init__(self, events: list[str]) -> None:
        BaseChatbot.__init__(self, ChatbotName.LANGCHAIN_OLLAMA_GEMMA3_4B)
        self._events = events

    def prepare_for_test_case(self) -> None:
        self._events.append(f"prepare:{self.name.value}")

    def cleanup_after_test_case(self) -> None:
        self._events.append(f"cleanup:{self.name.value}")

    def query(
            self,
            user_prompt: str,
            is_rag: bool = True,
            file_path: str | None = None,
            system_prompt: str | None = None,
    ) -> ChatbotResponse:
        del is_rag, file_path, system_prompt
        return ChatbotResponse(
            prompt=user_prompt,
            raw_prompt=user_prompt,
            response="ok",
            system_prompt="",
            tool=ToolInfo(tool_called=False),
            prompt_tokens=-1,
            response_tokens=-1,
            rag_context=None,
            document_content=None,
        )


class _LifecycleTestCase(BaseTestCase):
    def __init__(self) -> None:
        super().__init__(Category.BENIGN, [])

    def setup_attack_builder(self) -> None:
        return None

    def simulate_attacks(self, attacks_per_vulnerability_type: int = 1):
        del attacks_per_vulnerability_type
        return []

    def _get_metric(self, attack=None):
        del attack
        raise AssertionError("Metric should not be requested in this test")


def test_execute_prepares_and_cleans_up_chatbots_per_test_case(monkeypatch):
    events: list[str] = []
    original_chatbots = ChatbotStore._chatbots.copy()
    ChatbotStore._chatbots = {
        ChatbotName.DUMMY: _TrackingChatbot(ChatbotName.DUMMY, events),
    }
    monkeypatch.setattr(
        "testframework.testcases.base.OllamaGenerator.require_local_model_shutdown",
        lambda: events.append("shutdown-simulator"),
    )
    monkeypatch.setattr(
        _LifecycleTestCase,
        "_generate_attacks",
        lambda self, enhancer, attacks_per_vulnerability_type, test_case_id: (
            [],
            AttackEnhancementResult(
                enhanced_attacks=[],
                planned_attack_count=0,
                failed_attack_count=0,
                error_threshold_percent=100.0,
            ),
            True,
        ),
    )
    monkeypatch.setattr(
        _LifecycleTestCase,
        "_start_attacks",
        lambda self, attack_results, chatbots, enhanced_attacks, skip_chatbot_execution, test_case_id: (
            events.append("start-attacks")
        ),
    )

    try:
        _LifecycleTestCase().execute()
    finally:
        ChatbotStore._chatbots = original_chatbots

    assert events == [
        "shutdown-simulator",
        "prepare:DUMMY",
        "start-attacks",
        "cleanup:DUMMY",
    ]


def test_excessive_agency_skips_the_ollama_chatbot():
    events: list[str] = []
    test_case = ExcessiveAgencyTestCase()

    active_chatbots = test_case._select_chatbots({
        ChatbotName.DUMMY: DummyChatbot(),
        ChatbotName.LANGCHAIN_OLLAMA_GEMMA3_4B: _TrackingOllamaChatbot(events),
    })

    assert list(active_chatbots) == [ChatbotName.DUMMY]


def test_default_test_registers_the_ollama_chatbot(monkeypatch):
    registrations: list[ChatbotName] = []

    class _FakeVectorStore:
        pass

    class _FakeLangChainChatbot(_TrackingChatbot):
        def __init__(self, name: ChatbotName, **kwargs) -> None:
            del kwargs
            super().__init__(name, [])

    class _FakeLangChainOllamaChatbot(_TrackingOllamaChatbot):
        def __init__(self, name: ChatbotName, **kwargs) -> None:
            del kwargs
            BaseChatbot.__init__(self, name)
            self._events = []

    monkeypatch.setattr(
        "testframework.tests.default_test.VectorStore",
        _FakeVectorStore,
    )
    monkeypatch.setattr(
        "testframework.tests.default_test.LangChainChatbot",
        _FakeLangChainChatbot,
    )
    monkeypatch.setattr(
        "testframework.tests.default_test.LangChainOllamaChatbot",
        _FakeLangChainOllamaChatbot,
    )
    monkeypatch.setattr(
        "testframework.tests.default_test.ChatbotStore.add_chatbot",
        lambda chatbot: registrations.append(chatbot.name),
    )

    DefaultTest().setup_chatbots()

    assert registrations == [
        ChatbotName.LANGCHAIN_GPT_5,
        ChatbotName.LANGCHAIN_GPT_41,
        ChatbotName.LANGCHAIN_OLLAMA_GEMMA3_4B,
    ]


class _BareOllama:
    def __init__(self, **kwargs):
        pass


def test_prepare_for_test_case_starts_model(monkeypatch):
    calls: list[tuple[str, str]] = []
    monkeypatch.setattr(
        "testframework.chatbots.langchain_ollama_chatbot.ChatOllama",
        _BareOllama,
    )
    monkeypatch.setattr(
        "testframework.chatbots.langchain_ollama_chatbot.OllamaGenerator.start_model_by_name_if_not_running",
        lambda model_id: calls.append(("start", model_id)),
    )

    chatbot = LangChainOllamaChatbot()
    chatbot.prepare_for_test_case()

    assert calls == [("start", "gemma3:4b")]


def test_cleanup_after_test_case_stops_model(monkeypatch):
    calls: list[tuple[str, str]] = []
    monkeypatch.setattr(
        "testframework.chatbots.langchain_ollama_chatbot.ChatOllama",
        _BareOllama,
    )
    monkeypatch.setattr(
        "testframework.chatbots.langchain_ollama_chatbot.OllamaGenerator.stop_model_by_name",
        lambda model_id: calls.append(("stop", model_id)),
    )

    chatbot = LangChainOllamaChatbot()
    chatbot.cleanup_after_test_case()

    assert calls == [("stop", "gemma3:4b")]
