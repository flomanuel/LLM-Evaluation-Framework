from testframework import ChatbotName
from testframework.chatbots.dummy_chatbot import DummyChatbot
from testframework.models import ChatbotResponse


def test_dummy_chatbot_query_returns_chatbot_response():
    assert isinstance(DummyChatbot().query("hello"), ChatbotResponse)


def test_dummy_chatbot_query_is_not_error():
    assert DummyChatbot().query("hello").is_error is False


def test_dummy_chatbot_query_echoes_prompt():
    assert DummyChatbot().query("hello").prompt == "hello"


def test_dummy_chatbot_query_response_is_not_empty():
    assert len(DummyChatbot().query("hello").response) > 0


def test_dummy_chatbot_query_sets_file_path():
    response = DummyChatbot().query("hello", file_path="/tmp/f.pdf")
    assert response.file_path == "/tmp/f.pdf"


def test_dummy_chatbot_query_tool_not_called():
    assert DummyChatbot().query("hello").tool.tool_called is False


def test_dummy_chatbot_default_name_is_dummy():
    assert DummyChatbot().name == ChatbotName.DUMMY


def test_dummy_chatbot_response_is_unique_per_call():
    bot = DummyChatbot()
    r1 = bot.query("hello")
    r2 = bot.query("hello")
    assert r1.response != r2.response
