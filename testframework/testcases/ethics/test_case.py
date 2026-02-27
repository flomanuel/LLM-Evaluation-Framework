from __future__ import annotations
from typing import List
from deepteam.metrics import BaseRedTeamingMetric  # type: ignore
from deepteam.test_case import RTTestCase
from testframework.enums import Category
from testframework.testcases.base import BaseTestCase
from testframework.testcases.ethics.builder import EthicsAttacks
from testframework.testcases.ethics.subcategory import EthicsSubcategory


class EthicsTestCase(BaseTestCase):
    """Test case for ethics-related attacks."""

    def __init__(self, subcategories: List[EthicsSubcategory] | None = None) -> None:
        super().__init__(
            Category.ETHICS,
            subcategories if subcategories else list(EthicsSubcategory),
        )
        self.attack_builder = EthicsAttacks(self.subcategories, self.simulator_model, self.evaluation_model)

    def _get_metric(self, attack: RTTestCase) -> BaseRedTeamingMetric:
        return self.attack_builder._get_metric(attack)
