from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict
from uuid import UUID

from ..enums import Category
from ..models import TestCaseResult


class BaseTestCase(ABC):
    """Abstract base for all test cases."""

    def __init__(self, name: str, category: Category) -> None:
        self.name = name
        self.category = category

    @abstractmethod
    def execute(self) -> Dict[str, TestCaseResult]:
        """Run the test case and return a mapping from attack_id to TestCaseResult."""
        raise NotImplementedError

