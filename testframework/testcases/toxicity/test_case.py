#  Copyright (c) 2026.
#  Florian Emanuel Sauer

from __future__ import annotations
from typing import List
from deepteam.metrics import BaseRedTeamingMetric  # type: ignore
from deepteam.test_case import RTTestCase
from testframework.enums import Category
from testframework.testcases.base import BaseTestCase
from testframework.testcases.toxicity.builder import ToxicityAttacks
from testframework.testcases.toxicity.subcategory import ToxicitySubcategory


class ToxicityTestCase(BaseTestCase):
    """Test case for toxicity attacks."""

    def __init__(self, subcategories: List[ToxicitySubcategory] = []) -> None:
        super().__init__(
            Category.TOXICITY,
            subcategories,
        )
        self.attack_builder = ToxicityAttacks(self.subcategories, self.simulator_model, self.evaluation_model)

    def _get_metric(self, attack: RTTestCase) -> BaseRedTeamingMetric:
        return self.attack_builder._get_metric(attack)
