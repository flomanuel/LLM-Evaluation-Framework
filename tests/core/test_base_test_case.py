from enum import Enum
from types import SimpleNamespace
from unittest.mock import MagicMock

from testframework import ChatbotName
from testframework.chatbots.base import BaseChatbot
from testframework.chatbots.dummy_chatbot import DummyChatbot
from testframework.chatbots.langchain_ollama_chatbot import LangChainOllamaChatbot
from testframework.enums import Category
from testframework.metrics import ToolCallCodeInjectionMetric
from testframework.models import ChatbotResponse, ToolInfo
from testframework.testcases.base import BaseTestCase


class _ConcreteTestCase(BaseTestCase):
    def __init__(self, category=Category.ETHICS, subcategories=None):
        super().__init__(category, subcategories or [])

    def simulate_attacks(self, attacks_per_vulnerability_type=1):
        return []

    def setup_attack_builder(self):
        pass

    def _get_metric(self, attack):
        return object()


class _FakeOllamaBot(LangChainOllamaChatbot):
    """Minimal Ollama chatbot that bypasses the LangChain init."""
    def __init__(self):
        BaseChatbot.__init__(self, ChatbotName.LANGCHAIN_OLLAMA_GEMMA3_4B)

    def query(self, *a, **kw) -> ChatbotResponse:
        return ChatbotResponse(
            prompt="", raw_prompt="", response="", system_prompt="",
            tool=ToolInfo(tool_called=False), prompt_tokens=-1, response_tokens=-1,
            rag_context=None, document_content=None,
        )


class _FakeSubcategory(Enum):
    BRIBERY = "bribery"


# ---------------------------------------------------------------------------
# _test_case_identifier
# ---------------------------------------------------------------------------

def test_identifier_without_subcategories():
    tc = _ConcreteTestCase(category=Category.ETHICS, subcategories=[])
    assert tc._test_case_identifier() == "ethics"


def test_identifier_with_subcategories():
    tc = _ConcreteTestCase(category=Category.ETHICS, subcategories=[_FakeSubcategory.BRIBERY])
    assert tc._test_case_identifier() == "ethics_bribery"


# ---------------------------------------------------------------------------
# _build_query_kwargs
# ---------------------------------------------------------------------------

def _attack_with_metadata(metadata):
    return SimpleNamespace(metadata=metadata)


def test_build_query_kwargs_empty_when_no_metadata():
    assert BaseTestCase._build_query_kwargs(_attack_with_metadata(None)) == {}


def test_build_query_kwargs_includes_file_path():
    attack = _attack_with_metadata({"file_path": "/doc.pdf"})
    assert BaseTestCase._build_query_kwargs(attack) == {"file_path": "/doc.pdf"}


def test_build_query_kwargs_includes_is_rag():
    attack = _attack_with_metadata({"is_rag": False})
    assert BaseTestCase._build_query_kwargs(attack) == {"is_rag": False}


def test_build_query_kwargs_omits_keys_not_in_metadata():
    attack = _attack_with_metadata({})
    assert BaseTestCase._build_query_kwargs(attack) == {}


# ---------------------------------------------------------------------------
# _model_name
# ---------------------------------------------------------------------------

def test_model_name_with_string():
    assert BaseTestCase._model_name("gpt-4o") == "gpt-4o"


def test_model_name_with_none():
    assert BaseTestCase._model_name(None) is None


def test_model_name_with_deepeval_model():
    fake_model = MagicMock()
    fake_model.get_model_name.return_value = "mock-model"
    assert BaseTestCase._model_name(fake_model) == "mock-model"


def test_model_name_with_deepeval_model_raises():
    fake_model = MagicMock()
    fake_model.get_model_name.side_effect = RuntimeError("no name")
    result = BaseTestCase._model_name(fake_model)
    assert result == str(fake_model)


# ---------------------------------------------------------------------------
# _should_skip_ollama_chatbot
# ---------------------------------------------------------------------------

def test_should_skip_ollama_chatbot_true_for_excessive_agency():
    tc = _ConcreteTestCase(category=Category.EXCESSIVE_AGENCY)
    assert tc._should_skip_ollama_chatbot() is True


def test_should_skip_ollama_chatbot_false_for_other_categories():
    tc = _ConcreteTestCase(category=Category.ETHICS)
    assert tc._should_skip_ollama_chatbot() is False


# ---------------------------------------------------------------------------
# _select_chatbots
# ---------------------------------------------------------------------------

def test_select_chatbots_removes_ollama_for_excessive_agency():
    tc = _ConcreteTestCase(category=Category.EXCESSIVE_AGENCY)
    chatbots = {
        ChatbotName.DUMMY: DummyChatbot(),
        ChatbotName.LANGCHAIN_OLLAMA_GEMMA3_4B: _FakeOllamaBot(),
    }
    result = tc._select_chatbots(chatbots)
    assert ChatbotName.LANGCHAIN_OLLAMA_GEMMA3_4B not in result
    assert ChatbotName.DUMMY in result


def test_select_chatbots_keeps_all_for_non_excessive_agency():
    tc = _ConcreteTestCase(category=Category.ETHICS)
    chatbots = {
        ChatbotName.DUMMY: DummyChatbot(),
        ChatbotName.LANGCHAIN_OLLAMA_GEMMA3_4B: _FakeOllamaBot(),
    }
    result = tc._select_chatbots(chatbots)
    assert len(result) == 2


# ---------------------------------------------------------------------------
# _find_metric
# ---------------------------------------------------------------------------

def test_find_metric_returns_tool_call_metric_when_tool_check_true():
    tc = _ConcreteTestCase()
    attack = _attack_with_metadata({"tool_check": True})
    metric = tc._find_metric(attack)
    assert isinstance(metric, ToolCallCodeInjectionMetric)


def test_find_metric_returns_custom_metric_otherwise():
    sentinel = object()

    class _TC(_ConcreteTestCase):
        def _get_metric(self, attack):
            return sentinel

    tc = _TC()
    attack = _attack_with_metadata({"tool_check": False})
    assert tc._find_metric(attack) is sentinel


# ---------------------------------------------------------------------------
# store_results
# ---------------------------------------------------------------------------

def test_store_results_returns_none_when_run_folder_not_set():
    tc = _ConcreteTestCase()
    tc.run_folder = None
    assert tc.store_results() is None
