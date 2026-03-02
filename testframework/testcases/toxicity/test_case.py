#  Copyright (c) 2026.
#  Florian Emanuel Sauer

from __future__ import annotations
import os
import shlex
import time
from typing import List, cast
from deepeval.models import OllamaModel
from deepteam.metrics import BaseRedTeamingMetric  # type: ignore
from deepteam.test_case import RTTestCase
from testframework.enums import Category
from testframework.testcases.base import BaseTestCase
from testframework.testcases.toxicity.builder import ToxicityAttacks
from testframework.testcases.toxicity.subcategory import ToxicitySubcategory
from testframework.util.OllamaGenerator import OllamaGenerator


class ToxicityTestCase(BaseTestCase):
    """Test case for toxicity attacks."""

    def __init__(self, subcategories: List[ToxicitySubcategory]) -> None:
        super().__init__(
            Category.TOXICITY,
            subcategories,
        )

        self.simulator_model = OllamaGenerator.get_chatbot()
        OllamaGenerator.start_model_if_not_running()
        self.set_attack_builder()

    def set_attack_builder(self) -> None:
        self.attack_builder = ToxicityAttacks(self.subcategories, self.simulator_model, self.evaluation_model)

    def _get_metric(self, attack: RTTestCase) -> BaseRedTeamingMetric:
        return self.attack_builder._get_metric(attack)

    def simulate_attacks(self, attacks_per_vulnerability_type: int = 1) -> List[RTTestCase]:
        return cast(ToxicityAttacks, self.attack_builder).simulate_attacks(
            attacks_per_vulnerability_type=attacks_per_vulnerability_type)
