#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.


from __future__ import annotations

import os
from typing import Any
from langchain_openai import ChatOpenAI
from testframework.chatbots.langchain_base_chatbot import BaseLangChainChatbot
from testframework.chatbots.rag.vector_store import VectorStore
from testframework.enums import ChatbotName


class LangChainChatbot(BaseLangChainChatbot):
    """LangChain chatbot that uses the OpenAI inference API."""

    def __init__(
            self,
            name: ChatbotName = ChatbotName.LANGCHAIN,
            model: str = "gpt-4.1",
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
            **kwargs,
        )

    def _create_llm(self, model: str, timeout: float, **kwargs) -> Any:
        """Create the OpenAI LangChain backend."""
        reasoning = kwargs.get("reasoning")
        # https://docs.langchain.com/oss/python/integrations/chat/openai
        return ChatOpenAI(
            model=model,
            max_retries=2,
            api_key=os.getenv("OPENAI_API_KEY"),
            timeout=timeout,
            use_responses_api=True,
            store=False,
            reasoning=reasoning,
        )
