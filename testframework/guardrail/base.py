from __future__ import annotations

from abc import ABC, abstractmethod

from ..enums import Category
from ..models import DetectionResult, TimestampRange
from datetime import datetime


class BaseGuardrail(ABC):
    """Abstract base for guardrails."""

    name: str

    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    def eval_user_prompt(self, user_prompt: str, category: Category | None = None) -> DetectionResult:
        raise NotImplementedError

    @abstractmethod
    def eval_model_response(self, model_response: str, category: Category | None = None) -> DetectionResult:
        raise NotImplementedError

    @staticmethod
    def _empty_detection() -> DetectionResult:
        now = datetime.utcnow()
        return DetectionResult(
            success=False,
            detected_type=None,
            severity=0.0,
            judge_raw_response="",
            timestamp=TimestampRange(start=now, end=now),
        )


