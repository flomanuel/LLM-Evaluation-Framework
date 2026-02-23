from __future__ import annotations

from .base import BaseGuardrail
from ..models import DetectionElement


class PromptHardeningGuardrail(BaseGuardrail):
    """Guardrail that implements prompt hardening via engineered system prompts and simple heuristics."""

    def __init__(self, name: str = "prompt_hardening") -> None:
        super().__init__(name=name)

    def eval_attack(self, user_prompt: str) -> DetectionElement:
        # todo: implement
        pass

    def eval_model_response(self, model_response: str) -> DetectionElement:
        # todo: implement
        pass
