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
from testframework.util.ollama_handler import OllamaGenerator


class EthicsTestCase(BaseTestCase):
    """Test case for ethics-related attacks."""

    def __init__(self, subcategories: List[EthicsSubcategory] = None) -> None:
        super().__init__(
            Category.ETHICS,
            subcategories if subcategories else list(EthicsSubcategory),
        )
        self.simulator_model = OllamaGenerator.get_chatbot()
        OllamaGenerator.start_model_if_not_running()
        self.set_attack_builder()

    def set_attack_builder(self) -> None:
        self.attack_builder = EthicsAttacks(self.subcategories, self.simulator_model, self.evaluation_model)

    def _get_metric(self, attack: RTTestCase) -> BaseRedTeamingMetric:
        return self.attack_builder._get_metric(attack)

    def simulate_attacks(self, attacks_per_vulnerability_type: int = 1) -> List[RTTestCase]:
        return cast(EthicsAttacks, self.attack_builder).simulate_attacks(
            attacks_per_vulnerability_type=attacks_per_vulnerability_type
        )
