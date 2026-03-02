#  Copyright (c) 2026.
#  Florian Emanuel Sauer

from __future__ import annotations
from typing import List, cast
from deepteam.metrics import BaseRedTeamingMetric
from deepteam.test_case import RTTestCase
from testframework.enums import Category
from testframework.testcases.base import BaseTestCase
from testframework.testcases.illegal_activity.builder import IllegalActivity
from testframework.testcases.illegal_activity.subcategory import IllegalActivitySubcategory
from testframework.util.OllamaGenerator import OllamaGenerator


class IllegalActivityTestCase(BaseTestCase):
    """Test case using DeepTeam's IllegalActivity vulnerability as an attack source."""

    def __init__(self, subcategories: List[IllegalActivitySubcategory]) -> None:
        super().__init__(
            Category.ILLEGAL_ACTIVITY,
            subcategories,
        )

        self.simulator_model = OllamaGenerator.get_chatbot()
        OllamaGenerator.start_model_if_not_running()
        self.set_attack_builder()

    def set_attack_builder(self) -> None:
        self.attack_builder = IllegalActivity(self.subcategories, self.simulator_model, self.evaluation_model)

    def _get_metric(self, attack: RTTestCase) -> BaseRedTeamingMetric:
        return self.attack_builder._get_metric(attack)

    def simulate_attacks(self, attacks_per_vulnerability_type: int = 1) -> List[RTTestCase]:
        return cast(IllegalActivity, self.attack_builder).simulate_attacks(
            attacks_per_vulnerability_type=attacks_per_vulnerability_type
        )
