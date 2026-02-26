from __future__ import annotations

from typing import List
from deepteam.metrics import BaseRedTeamingMetric  # type: ignore
from deepteam.test_case import RTTestCase
from testframework.enums import Category
from testframework.testcases.base import BaseTestCase
from testframework.testcases.privacy_violations.attack_builder import PrivacyViolationsAttacks


class PrivacyViolationsTestCase(BaseTestCase):
    """Test case for privacy violations attacks."""

    def __init__(self) -> None:
        super().__init__(
            Category.PRIVACY_VIOLATIONS,
            []
        )
        self.attack_builder = PrivacyViolationsAttacks(self.subcategories)

    def _get_metric(self, attack: RTTestCase = None) -> BaseRedTeamingMetric:
        return self.attack_builder._get_metric()

    def enhance_base_attack(self, base_attack: str) -> tuple[str, list[str]]:
        return base_attack, []

