from __future__ import annotations

from abc import ABC, abstractmethod

from testframework.models import DetectionElement


class BaseGuardrail(ABC):
    """Abstract base for guardrails."""

    name: str

    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    def eval_attack(self, user_prompt: str) -> DetectionElement:
        raise NotImplementedError

    @abstractmethod
    def eval_model_response(self, model_response: str) -> DetectionElement:
        raise NotImplementedError
