from __future__ import annotations

from typing import List

from deepteam.metrics import BaseRedTeamingMetric  # type: ignore
from deepteam.test_case import RTTestCase

from testframework.enums import Category
from testframework.testcases.base import BaseTestCase
from testframework.testcases.toxicity.attack_builder import ToxicityAttacks
from testframework.testcases.toxicity.subcategory import ToxicitySubcategory


class ToxicityTestCase(BaseTestCase):
    """Test case for toxicity attacks."""

    def __init__(self, subcategories: List[ToxicitySubcategory] | None = None) -> None:
        super().__init__(
            Category.TOXICITY,
            subcategories,
        )
        self.attack_builder = ToxicityAttacks(self.subcategories, self.simulator_model)

    def _get_metric(self, attack: RTTestCase) -> BaseRedTeamingMetric:
        return self.attack_builder._get_metric(attack)

    def enhance_base_attack(self, base_attack: str) -> tuple[str, list[str]]:
        return base_attack, []
