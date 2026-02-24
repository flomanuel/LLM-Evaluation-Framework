from __future__ import annotations

import datetime
import uuid
from datetime import datetime, timezone
from .base import BaseGuardrail
from .. import Category
from ..models import DetectionElement


class PromptHardeningGuardrail(BaseGuardrail):
    """Guardrail that implements prompt hardening via engineered system prompts and simple heuristics."""

    def __init__(self, name: str = "prompt_hardening") -> None:
        super().__init__(name=name)

    def eval_attack(self, user_prompt: str) -> DetectionElement:
        # todo: implement
        return DetectionElement(
            success=False,
            detected_type=Category.ILLEGAL_ACTIVITY,
            severity=1.0,
            judge_raw_response=f"Lorem ipsum dolor sit amet, consectetur adipiscing elit. {uuid.uuid4()}",
            timestamp=datetime.now(timezone.utc)
        )

    def eval_model_response(self, model_response: str) -> DetectionElement:
        # todo: implement
        return DetectionElement(
            success=False,
            detected_type=Category.ILLEGAL_ACTIVITY,
            severity=0.0,
            judge_raw_response=f"Lorem ipsum dolor sit amet, consectetur adipiscing elit. {uuid.uuid4()}",
            timestamp=datetime.now(timezone.utc)
        )
