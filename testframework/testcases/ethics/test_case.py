#  Copyright (c) 2026.
#  Florian Emanuel Sauer

from __future__ import annotations
from typing import List, cast
from deepteam.metrics import BaseRedTeamingMetric  # type: ignore
from deepteam.test_case import RTTestCase
from testframework.enums import Category
from testframework.testcases.base import BaseTestCase
from testframework.testcases.ethics.builder import EthicsAttacks
from testframework.testcases.ethics.subcategory import EthicsSubcategory


class EthicsTestCase(BaseTestCase):
    """Test case for ethics-related attacks."""

    def __init__(self, subcategories: List[EthicsSubcategory] = []) -> None:
        super().__init__(
            Category.ETHICS,
            subcategories if subcategories else list(EthicsSubcategory),
        )
        self.attack_builder = EthicsAttacks(self.subcategories, self.simulator_model, self.evaluation_model)

    def _get_metric(self, attack: RTTestCase) -> BaseRedTeamingMetric:
        return self.attack_builder._get_metric(attack)

    def simulate_attacks(self, attacks_per_vulnerability_type: int = 1) -> List[RTTestCase]:
        return cast(EthicsAttacks, self.attack_builder).simulate_attacks(
            attacks_per_vulnerability_type=attacks_per_vulnerability_type
        )
