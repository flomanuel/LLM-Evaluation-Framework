from __future__ import annotations

from typing import List
from deepteam.metrics import BaseRedTeamingMetric  # type: ignore
from deepteam.test_case import RTTestCase
from testframework.enums import Category
from testframework.testcases.base import BaseTestCase
from testframework.testcases.fairness.builder import FairnessAttacks
from testframework.testcases.fairness.subcategory import FairnessSubcategory


class FairnessTestCase(BaseTestCase):
    """Test case for fairness-related attacks."""

    def __init__(self, subcategories: List[FairnessSubcategory] = []) -> None:
        super().__init__(
            Category.FAIRNESS,
            subcategories if subcategories else list(FairnessSubcategory),
        )
        self.attack_builder = FairnessAttacks(self.subcategories, self.simulator_model, self.evaluation_model)

    def _get_metric(self, attack: RTTestCase) -> BaseRedTeamingMetric:
        return self.attack_builder._get_metric()
