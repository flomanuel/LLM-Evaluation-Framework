#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.


from __future__ import annotations

from typing import Any

from langchain_ollama import ChatOllama

from testframework.chatbots.langchain_base_chatbot import BaseLangChainChatbot
from testframework.chatbots.rag.vector_store import VectorStore
from testframework.enums import ChatbotName
from testframework.util.ollama_handler import OllamaGenerator


class LangChainOllamaChatbot(BaseLangChainChatbot):
    """LangChain chatbot that uses the local Ollama inference API."""

    DEFAULT_MODEL = "gemma3:4b"

    def __init__(
            self,
            name: ChatbotName = ChatbotName.LANGCHAIN_OLLAMA_GEMMA3_4B,
            model: str = DEFAULT_MODEL,
            vector_store: VectorStore | None = None,
            rag_k: int = 4,
            timeout: float | None = None,
            timeout_retries: int = BaseLangChainChatbot.DEFAULT_TIMEOUT_RETRIES,
            **kwargs,
    ) -> None:
        super().__init__(
            name=name,
            model=model,
            vector_store=vector_store,
            rag_k=rag_k,
            timeout=timeout,
            timeout_retries=timeout_retries,
            skip_tools=True,
            **kwargs,
        )

    def _create_llm(self, model: str, timeout: float, **kwargs) -> Any:
        """Create the Ollama LangChain backend."""
        reasoning = kwargs.get("reasoning")
        # https://docs.langchain.com/oss/python/integrations/chat/ollama
        return ChatOllama(
            model=model,
            reasoning=reasoning,
            client_kwargs={"timeout": timeout},
        )

    def prepare_for_test_case(self) -> None:
        """Start the Ollama model before chatbot execution starts."""
        OllamaGenerator.start_model_by_name_if_not_running(self._model_name)

    def cleanup_after_test_case(self) -> None:
        """Stop the Ollama model once the test case is done."""
        OllamaGenerator.stop_model_by_name(self._model_name)
