#  Copyright (c) 2026.
#  Florian Emanuel Sauer

from __future__ import annotations

from abc import ABC, abstractmethod

from testframework import ChatbotName
from testframework.models import DetectionElement


class BaseGuardrail(ABC):
    """Abstract base for guardrails."""

    name: str

    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    def eval_attack(self, user_prompt: str, attack_description: str) -> DetectionElement:
        raise NotImplementedError

    @abstractmethod
    def eval_model_response(self, model_response: str, chatbot: ChatbotName, attack_description: str,  **kwargs) -> DetectionElement:
        raise NotImplementedError
