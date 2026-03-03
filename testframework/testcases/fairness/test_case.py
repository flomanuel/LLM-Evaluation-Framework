#  Copyright (c) 2026.
#  Florian Emanuel Sauer

from __future__ import annotations

from typing import List, cast
from deepteam.metrics import BaseRedTeamingMetric  # type: ignore
from deepteam.test_case import RTTestCase
from testframework.enums import Category
from testframework.testcases.base import BaseTestCase
from testframework.testcases.fairness.builder import FairnessAttacks
from testframework.testcases.fairness.subcategory import FairnessSubcategory


class FairnessTestCase(BaseTestCase):
    """Test case for fairness-related attacks."""

    def __init__(self, subcategories: List[FairnessSubcategory] = None) -> None:
        super().__init__(
            Category.FAIRNESS,
            subcategories,
        )
        self.set_attack_builder()

    def set_attack_builder(self) -> None:
        self.attack_builder = FairnessAttacks(self.subcategories, self.simulator_model, self.evaluation_model)

    def _get_metric(self, attack: RTTestCase) -> BaseRedTeamingMetric:
        return self.attack_builder._get_metric()

    def simulate_attacks(self, attacks_per_vulnerability_type: int = 1) -> List[RTTestCase]:
        return cast(FairnessAttacks, self.attack_builder).simulate_attacks()
