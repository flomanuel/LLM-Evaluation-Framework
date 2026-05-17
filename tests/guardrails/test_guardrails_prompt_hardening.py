import pytest

from testframework import ChatbotName
from testframework.chatbots.dummy_chatbot import DummyChatbot
from testframework.chatbots.store import ChatbotStore
from testframework.guardrails.prompt_hardening.prompt_hardening import PromptHardeningGuardrail
from testframework.models import PromptHardeningDetectionElement


# ---------------------------------------------------------------------------
# eval_attack – no-op placeholder that doesn't error
# ---------------------------------------------------------------------------

def test_eval_attack_returns_detection_element_without_error():
    guard = PromptHardeningGuardrail()
    result = guard.eval_attack("some attack")
    assert isinstance(result, PromptHardeningDetectionElement)
    assert result.is_error is False


# ---------------------------------------------------------------------------
# eval_model_response
# ---------------------------------------------------------------------------

class _FakeMetric:
    harm_category = "test_harm"

    def __init__(self, success: bool, score: float):
        self.success = success
        self.score = score
        self.reason = "fake reason"

    def measure(self, test_case, tool_info=None):
        return self.score


class _ErrorChatbot(DummyChatbot):
    def query(self, *args, **kwargs):
        raise RuntimeError("chatbot failed")


def test_eval_model_response_safe_when_chatbot_responds_safely():
    original = ChatbotStore._chatbots.copy()
    ChatbotStore._chatbots = {ChatbotName.DUMMY: DummyChatbot()}
    try:
        guard = PromptHardeningGuardrail()
        result = guard.eval_model_response(
            "Attack prompt",
            chatbot=ChatbotName.DUMMY,
            metric=_FakeMetric(success=True, score=1.0),
        )
        assert result.success is True
    finally:
        ChatbotStore._chatbots = original


def test_eval_model_response_unsafe_when_chatbot_responds_harmfully():
    original = ChatbotStore._chatbots.copy()
    ChatbotStore._chatbots = {ChatbotName.DUMMY: DummyChatbot()}
    try:
        guard = PromptHardeningGuardrail()
        result = guard.eval_model_response(
            "Attack prompt",
            chatbot=ChatbotName.DUMMY,
            metric=_FakeMetric(success=False, score=0.0),
        )
        assert result.success is False
    finally:
        ChatbotStore._chatbots = original


def test_eval_model_response_returns_error_when_chatbot_query_fails():
    original = ChatbotStore._chatbots.copy()
    ChatbotStore._chatbots = {ChatbotName.DUMMY: _ErrorChatbot()}
    try:
        guard = PromptHardeningGuardrail()
        with pytest.raises(RuntimeError, match="chatbot failed"):
            guard.eval_model_response(
                "Attack prompt",
                chatbot=ChatbotName.DUMMY,
                metric=_FakeMetric(success=True, score=1.0),
            )
    finally:
        ChatbotStore._chatbots = original
