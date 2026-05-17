import pytest

from testframework import ChatbotName
from testframework.chatbots.dummy_chatbot import DummyChatbot
from testframework.chatbots.store import ChatbotStore


@pytest.fixture(autouse=True)
def clear_store():
    ChatbotStore._chatbots.clear()
    yield
    ChatbotStore._chatbots.clear()


def test_add_chatbot_registers_by_name():
    bot = DummyChatbot()
    ChatbotStore.add_chatbot(bot)
    assert ChatbotStore.get_chatbot(ChatbotName.DUMMY) is bot


def test_add_chatbot_overwrites_existing():
    bot1 = DummyChatbot()
    bot2 = DummyChatbot()
    ChatbotStore.add_chatbot(bot1)
    ChatbotStore.add_chatbot(bot2)
    assert ChatbotStore.get_chatbot(ChatbotName.DUMMY) is bot2


def test_remove_chatbot_removes_registered():
    ChatbotStore.add_chatbot(DummyChatbot())
    ChatbotStore.remove_chatbot(ChatbotName.DUMMY)
    assert ChatbotStore.get_chatbot(ChatbotName.DUMMY) is None


def test_remove_chatbot_does_not_raise_when_not_registered():
    ChatbotStore.remove_chatbot(ChatbotName.DUMMY)


def test_get_chatbots_returns_all_registered():
    bot = DummyChatbot()
    ChatbotStore.add_chatbot(bot)
    all_bots = ChatbotStore.get_chatbots()
    assert ChatbotName.DUMMY in all_bots


def test_get_chatbot_returns_none_for_unknown_name():
    assert ChatbotStore.get_chatbot(ChatbotName.DUMMY) is None
