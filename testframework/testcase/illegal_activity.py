from __future__ import annotations

from deepteam.vulnerabilities import IllegalActivity  # type: ignore
from ..enums import Category
from ..models import TestCaseResult
from .base import BaseTestCase


class IllegalActivityTestCase(BaseTestCase):
    """Test case using DeepTeam's IllegalActivity vulnerability as an attack source."""

    def store_results(self, results: TestCaseResult) -> str:
        pass

    def __init__(self) -> None:
        super().__init__(name="illegal_activity", category=Category.ILLEGAL_ACTIVITY)
        self.vulnerability = IllegalActivity()
