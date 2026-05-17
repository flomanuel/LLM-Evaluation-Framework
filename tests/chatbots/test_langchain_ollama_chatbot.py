from testframework import LLMErrorType
from testframework.chatbots.langchain_ollama_chatbot import LangChainOllamaChatbot


class _FakeResponse:
    def __init__(self, text: str, content=None) -> None:
        self.text = text
        self.content = content if content is not None else text
        self.tool_calls = []
        self.usage_metadata = {
            "input_tokens": 5,
            "output_tokens": 3,
        }


class _FakeBoundLLM:
    def __init__(self, responses: list[object]) -> None:
        self._responses = responses

    def invoke(self, messages):
        del messages
        result = self._responses.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


class _FakeChatOllama:
    responses: list[object] = []
    init_kwargs: dict | None = None

    def __init__(self, **kwargs) -> None:
        self.__class__.init_kwargs = kwargs

    def invoke(self, messages):
        del messages
        result = self.__class__.responses.pop(0)
        if isinstance(result, Exception):
            raise result
        return result

    def bind_tools(self, tools):
        del tools
        return _FakeBoundLLM(self.responses.copy())


def test_query_uses_official_langchain_ollama_backend(monkeypatch):
    _FakeChatOllama.responses = [_FakeResponse("gemma response")]
    _FakeChatOllama.init_kwargs = None
    monkeypatch.setattr(
        "testframework.chatbots.langchain_ollama_chatbot.ChatOllama",
        _FakeChatOllama,
    )

    chatbot = LangChainOllamaChatbot()

    response = chatbot.query("Hello")

    assert response.is_error is False
    assert response.response == "gemma response"
    assert _FakeChatOllama.init_kwargs == {
        "model": "gemma3:4b",
        "reasoning": None,
        "client_kwargs": {"timeout": chatbot.DEFAULT_TIMEOUT},
    }


def test_prepare_and_cleanup_delegate_to_ollama_handler(monkeypatch):
    calls: list[tuple[str, str]] = []
    monkeypatch.setattr(
        "testframework.chatbots.langchain_ollama_chatbot.ChatOllama",
        _FakeChatOllama,
    )
    monkeypatch.setattr(
        "testframework.chatbots.langchain_ollama_chatbot.OllamaGenerator.start_model_by_name_if_not_running",
        lambda model_id: calls.append(("start", model_id)),
    )
    monkeypatch.setattr(
        "testframework.chatbots.langchain_ollama_chatbot.OllamaGenerator.stop_model_by_name",
        lambda model_id: calls.append(("stop", model_id)),
    )

    chatbot = LangChainOllamaChatbot()
    chatbot.prepare_for_test_case()
    chatbot.cleanup_after_test_case()

    assert calls == [
        ("start", "gemma3:4b"),
        ("stop", "gemma3:4b"),
    ]


def test_query_returns_response_on_success(monkeypatch):
    _FakeChatOllama.responses = [_FakeResponse("success reply")]
    _FakeChatOllama.init_kwargs = None
    monkeypatch.setattr(
        "testframework.chatbots.langchain_ollama_chatbot.ChatOllama",
        _FakeChatOllama,
    )

    chatbot = LangChainOllamaChatbot()
    response = chatbot.query("Hello")

    assert response.is_error is False
    assert response.response == "success reply"


def test_query_returns_error_on_timeout(monkeypatch):
    _FakeChatOllama.responses = [Exception("Request timed out"), Exception("Request timed out")]
    monkeypatch.setattr(
        "testframework.chatbots.langchain_ollama_chatbot.ChatOllama",
        _FakeChatOllama,
    )

    chatbot = LangChainOllamaChatbot(timeout_retries=1)
    response = chatbot.query("Hello")

    assert response.is_error is True
    assert response.error is not None
    assert response.error.error_type == LLMErrorType.TIMEOUT


def test_query_returns_error_on_connection_error(monkeypatch):
    _FakeChatOllama.responses = [ConnectionError("Connection refused")]
    monkeypatch.setattr(
        "testframework.chatbots.langchain_ollama_chatbot.ChatOllama",
        _FakeChatOllama,
    )

    chatbot = LangChainOllamaChatbot(timeout_retries=0)
    response = chatbot.query("Hello")

    assert response.is_error is True
    assert response.error is not None
    assert response.error.error_type == LLMErrorType.CONNECTION_ERROR
