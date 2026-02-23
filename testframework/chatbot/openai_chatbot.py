from __future__ import annotations

import os
from typing import Dict

from loguru import logger
from openai import OpenAI

from ..enums import Chatbot
from ..models import ToolInfo, ChatbotResponse
from .base import BaseChatbot


class OpenAIChatbot(BaseChatbot):
    """Concrete chatbot implementation using OpenAI's Chat Completions API."""

    def __init__(self, model_name: str = "gpt-4.1", temperature: float = 0.0) -> None:
        super().__init__(model_name=model_name)
        self.temperature = temperature
        self._client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        logger.debug(f"OpenAI chatbot initialized with model: {model_name}")

    def query(
        self,
        user_prompt: str,
        is_rag: bool = True,
        file_path: str | None = None,
        system_prompt: str | None = None,
    ) -> Dict[str, ChatbotResponse]:
        logger.debug(f"Querying OpenAI API with model: {self.model_name}")
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})

        completion = self._client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=self.temperature,
        )
        message = completion.choices[0].message
        text = message.content or ""
        usage = completion.usage
        total_tokens = usage.total_tokens if usage is not None else 0

        logger.debug(f"OpenAI API response received (tokens: {total_tokens})")

        response = ChatbotResponse(
            response=text,
            token_count=total_tokens,
            tool=ToolInfo(tool_called=False, tool_call_params=None),
        )

        # For now, we map the configured model to GPT_41; this can be extended.
        return {Chatbot.V_GPT_41.value: response}


