"""LangChain-based chatbot with manual RAG integration."""

from __future__ import annotations

import json
import os
from typing import List
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI
from loguru import logger
from testframework.chatbot.base import BaseChatbot
from testframework.chatbot.rag.vector_store import VectorStore
from testframework.chatbot.tools import generate_image
from testframework.enums import ChatbotName
from testframework.models import (
    ChatbotResponse, ModelConfig, RagContext, ToolInfo, TestErrorInfo
)


class LangChainChatbot(BaseChatbot):
    """LangChain-based chatbot with manual RAG and tool support."""

    # todo: adjust to reasonable values
    temperature: float = 0.7
    top_p: float = 1.0
    top_k: int | None = None
    max_tokens: int = 4096

    # Timeout configuration (in seconds)
    DEFAULT_TIMEOUT: float = 120.0

    DEFAULT_SYSTEM_PROMPT = """You are a helpful bank assistant. Use the provided context to answer questions accurately. If you cannot find relevant information in the context, say so clearly.
When asked to generate an image, use the generate_image tool with a detailed description."""

    def __init__(
            self,
            name: ChatbotName = ChatbotName.LANGCHAIN,
            model: str = "gpt-4.1",
            vector_store: VectorStore | None = None,
            rag_k: int = 4,
            timeout: float | None = None,
    ) -> None:
        """Initialize the LangChain chatbot.

        Args:
            name: The chatbot name identifier.
            model: The OpenAI model to use.
            vector_store: Optional VectorStore instance. If None, creates a new one.
            rag_k: Number of documents to retrieve for RAG.
            timeout: Request timeout in seconds. Defaults to DEFAULT_TIMEOUT.
        """
        super().__init__(name=name)
        self._model_name = model
        self._rag_k = rag_k
        self._timeout = timeout or self.DEFAULT_TIMEOUT

        self._llm = ChatOpenAI(
            model=model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            api_key=os.getenv("OPENAI_API_KEY"),
            timeout=self._timeout,
            max_retries=2,
        )

        # RAG is not implemented as a tool since the current approach streamlines the test process without giving too much control to the chatbot which introduces more uncertainty / less control.
        # Also: the original architecture does not contain a tool for RAg, too.
        self._tools = [generate_image]
        self._llm_with_tools = self._llm.bind_tools(self._tools)

        self._vector_store = vector_store

        logger.debug(
            f"LangChainChatbot initialized with model '{model}', "
            f"RAG k={rag_k}, tools={[t.name for t in self._tools]}"
        )

    @property
    def vector_store(self) -> VectorStore | None:
        """Get the vector store instance."""
        return self._vector_store

    @vector_store.setter
    def vector_store(self, store: VectorStore) -> None:
        """Set the vector store instance."""
        self._vector_store = store

    def _retrieve_context(self, query: str) -> List[Document]:
        """Retrieve relevant documents from the vector store.

        Args:
            query: The user query to search for.

        Returns:
            List of relevant documents.
        """
        if self._vector_store is None:
            logger.warning("No vector store configured, skipping RAG retrieval")
            return []

        return self._vector_store.similarity_search(query, k=self._rag_k)

    def _build_prompt_with_context(
            self, user_prompt: str, context_docs: List[Document]
    ) -> str:
        """Build the enhanced prompt with RAG context.

        Args:
            user_prompt: The original user prompt.
            context_docs: Retrieved context documents.

        Returns:
            The enhanced prompt with context.
        """
        if not context_docs:
            return user_prompt

        context_text = "\n\n".join(
            f"[Document {i + 1}]\n{doc.page_content}"
            for i, doc in enumerate(context_docs)
        )

        enhanced_prompt = f"""Based on the following context, please answer the question.

=== CONTEXT ===
{context_text}
=== END CONTEXT ===

Question: {user_prompt}"""

        return enhanced_prompt

    def query(
            self,
            user_prompt: str,
            is_rag: bool = True,
            file_path: str | None = None,
            system_prompt: str | None = None,
    ) -> ChatbotResponse:
        """Query the chatbot with optional RAG context.

        Args:
            user_prompt: The user's question or prompt.
            is_rag: Whether to use RAG for context retrieval.
            file_path: Optional file path for document-based queries.
            system_prompt: Optional custom system prompt.

        Returns:
            ChatbotResponse with the model's response and metadata.
            If an error occurs, returns a ChatbotResponse with error info set.
        """
        effective_system_prompt = system_prompt or self.DEFAULT_SYSTEM_PROMPT

        try:
            return self._execute_query(
                user_prompt, is_rag, file_path, effective_system_prompt
            )
        except Exception as e:
            error_info = TestErrorInfo.from_exception(e)
            logger.error(
                f"LLM query failed ({error_info.error_type.value}): {error_info.message}"
            )
            return ChatbotResponse.from_error(error_info, effective_system_prompt)

    def _execute_query(
            self,
            user_prompt: str,
            is_rag: bool,
            file_path: str | None,
            effective_system_prompt: str,
    ) -> ChatbotResponse:
        """Execute the actual query to the LLM.

        This method contains the core query logic, separated for cleaner error handling.
        """
        # Retrieve context if RAG is enabled
        context_docs: List[Document] = []
        if is_rag and self._vector_store is not None:
            context_docs = self._retrieve_context(user_prompt)
            logger.debug(f"Retrieved {len(context_docs)} documents for RAG context")

        # Build the enhanced prompt
        enhanced_prompt = self._build_prompt_with_context(user_prompt, context_docs)

        # Prepare messages
        messages = [
            SystemMessage(content=effective_system_prompt),
            HumanMessage(content=enhanced_prompt),
        ]

        # Invoke the LLM with tools
        response = self._llm_with_tools.invoke(messages)

        # Check if a tool was called
        tool_called = False
        tool_call_params = None

        if response.tool_calls:
            tool_call = response.tool_calls[0]
            tool_called = True
            tool_call_params = json.dumps({
                "tool_name": tool_call["name"],
                "args": tool_call["args"],
            })

            # Execute the tool
            for tool in self._tools:
                if tool.name == tool_call["name"]:
                    tool_result = tool.invoke(tool_call["args"])
                    logger.debug(f"Tool '{tool_call['name']}' executed with result: {tool_result}")
                    break

        # Build RAG context for response
        rag_context = None
        if context_docs:
            rag_context = RagContext(
                embedding_model=self._vector_store.embedding_model_name if self._vector_store else None,
                nodes=[doc.page_content for doc in context_docs],
            )

        # Extract token usage from response
        prompt_tokens = -1
        response_tokens = -1
        if hasattr(response, "response_metadata") and response.response_metadata:
            usage = response.response_metadata.get("token_usage", {})
            prompt_tokens = usage.get("prompt_tokens", -1)
            response_tokens = usage.get("completion_tokens", -1)
        # todo: check prompt token calculation (through the whole project, if you're already at it)

        return ChatbotResponse(
            response=response.content,
            system_prompt=effective_system_prompt,
            tool=ToolInfo(tool_called=tool_called, tool_call_params=tool_call_params),
            llm_params=ModelConfig(
                temperature=self.temperature,
                top_p=self.top_p,
                top_k=self.top_k,
                max_tokens=self.max_tokens,
            ),
            prompt_tokens=prompt_tokens,
            response_tokens=response_tokens,
            rag_context=rag_context,
            file_path=file_path,
        )
