#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

import httpx
from openai import APITimeoutError

from testframework import ChatbotName, LLMErrorType, TestErrorInfo
from testframework.chatbots.langchain_chatbot import LangChainChatbot


class _FakeResponse:
    def __init__(self, text: str, content=None) -> None:
        self.text = text
        self.content = content if content is not None else text
        self.tool_calls = []
        self.usage_metadata = {
            "input_tokens": 12,
            "output_tokens": 7,
        }


class _FakeBoundLLM:
    def __init__(self, responses: list[object]) -> None:
        self._responses = responses
        self.invoke_calls = 0

    def invoke(self, messages):
        self.invoke_calls += 1
        result = self._responses.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


class _FakeChatOpenAI:
    responses: list[object] = []
    last_bound_llm: _FakeBoundLLM | None = None

    def __init__(self, **kwargs) -> None:
        self.kwargs = kwargs

    def bind_tools(self, tools):
        del tools
        bound = _FakeBoundLLM(self.responses.copy())
        self.__class__.last_bound_llm = bound
        return bound


def _timeout_error() -> APITimeoutError:
    request = httpx.Request("POST", "https://api.openai.com/v1/responses")
    return APITimeoutError(request=request)


def test_from_exception_classifies_openai_timeout_as_timeout():
    error = TestErrorInfo.from_exception(_timeout_error())

    assert error.error_type == LLMErrorType.TIMEOUT
    assert error.message == "Request timed out."


def test_query_retries_once_after_timeout(monkeypatch):
    _FakeChatOpenAI.responses = [_timeout_error(), _FakeResponse("Recovered response")]
    _FakeChatOpenAI.last_bound_llm = None
    monkeypatch.setattr(
        "testframework.chatbots.langchain_chatbot.ChatOpenAI",
        _FakeChatOpenAI,
    )

    chatbot = LangChainChatbot(
        name=ChatbotName.LANGCHAIN_GPT_5,
        model="gpt-5",
        timeout_retries=1,
    )

    response = chatbot.query("Hello")

    assert response.is_error is False
    assert response.response == "Recovered response"
    assert _FakeChatOpenAI.last_bound_llm is not None
    assert _FakeChatOpenAI.last_bound_llm.invoke_calls == 2


def test_query_returns_timeout_error_after_retry_exhausted(monkeypatch):
    _FakeChatOpenAI.responses = [_timeout_error(), _timeout_error()]
    _FakeChatOpenAI.last_bound_llm = None
    monkeypatch.setattr(
        "testframework.chatbots.langchain_chatbot.ChatOpenAI",
        _FakeChatOpenAI,
    )

    chatbot = LangChainChatbot(
        name=ChatbotName.LANGCHAIN_GPT_5,
        model="gpt-5",
        timeout_retries=1,
    )

    response = chatbot.query("Hello")

    assert response.is_error is True
    assert response.error is not None
    assert response.error.error_type == LLMErrorType.TIMEOUT
    assert _FakeChatOpenAI.last_bound_llm is not None
    assert _FakeChatOpenAI.last_bound_llm.invoke_calls == 2


def test_query_extracts_output_text_blocks(monkeypatch):
    _FakeChatOpenAI.responses = [
        _FakeResponse(
            "",
            content=[
                {"type": "reasoning", "text": "internal"},
                {"type": "output_text", "text": "Visible answer"},
            ],
        )
    ]
    _FakeChatOpenAI.last_bound_llm = None
    monkeypatch.setattr(
        "testframework.chatbots.langchain_chatbot.ChatOpenAI",
        _FakeChatOpenAI,
    )

    chatbot = LangChainChatbot(
        name=ChatbotName.LANGCHAIN_GPT_5,
        model="gpt-5",
    )

    response = chatbot.query("Hello")

    assert response.is_error is False
    assert response.response == "Visible answer"


# ---------------------------------------------------------------------------
# TestErrorInfo.from_exception – additional classifiers
# ---------------------------------------------------------------------------

from testframework.models import TestErrorInfo, LLMErrorType  # noqa: E402


def test_from_exception_classifies_timeout_by_message():
    error = TestErrorInfo.from_exception(Exception("Request timed out"))
    assert error.error_type == LLMErrorType.TIMEOUT


def test_from_exception_classifies_connection_error():
    error = TestErrorInfo.from_exception(ConnectionError("refused"))
    assert error.error_type == LLMErrorType.CONNECTION_ERROR


def test_from_exception_classifies_deepeval_error():
    class _DeepEvalError(Exception):
        pass
    _DeepEvalError.__module__ = "deepeval.metrics.something"
    error = TestErrorInfo.from_exception(_DeepEvalError("metric failed"))
    assert error.error_type == LLMErrorType.GENERATION_ERROR


def test_from_exception_classifies_unknown_error():
    error = TestErrorInfo.from_exception(ValueError("something went wrong"))
    assert error.error_type == LLMErrorType.UNKNOWN
