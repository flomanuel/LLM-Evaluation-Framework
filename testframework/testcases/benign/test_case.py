#  Copyright (c) 2026.
#  Florian Emanuel Sauer

from __future__ import annotations
from typing import List, cast
from deepteam.metrics import BaseRedTeamingMetric  # type: ignore
from deepteam.test_case import RTTestCase
from testframework.enums import Category, Severity
from testframework.testcases.base import BaseTestCase
from testframework.testcases.benign.builder import BenignAttacks
from testframework.testcases.benign.subcategory import BenignSubcategory
from testframework.util.ollama_handler import OllamaGenerator


class BenignTestCase(BaseTestCase):
    """Test case for benign/safe prompts."""

    def __init__(self, subcategories: List[BenignSubcategory] = None) -> None:
        super().__init__(
            Category.BENIGN,
            subcategories,
            severity=Severity.SAFE,
        )

    def setup_attack_builder(self) -> None:
        self.simulator_model = OllamaGenerator.get_chatbot()
        OllamaGenerator.start_model_if_not_running()
        # set only after simulator_model and evaluation_model are available
        self.attack_builder = BenignAttacks(self.subcategories, self.simulator_model, self.evaluation_model)

    def _get_metric(self, attack: RTTestCase) -> BaseRedTeamingMetric:
        return self.attack_builder._get_metric()

    def simulate_attacks(self, attacks_per_vulnerability_type: int = 1) -> List[RTTestCase]:
        return cast(BenignAttacks, self.attack_builder).simulate_attacks()

    @property
    def description(self) -> str:
        return "Benign prompt that doesn't have any attacks, harmful content or malicious intents."
