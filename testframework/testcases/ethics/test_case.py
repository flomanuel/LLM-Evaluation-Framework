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

    def setup_attack_builder(self) -> None:
        self.simulator_model = OllamaGenerator.get_chatbot()
        OllamaGenerator.start_model_if_not_running()
        self.attack_builder = EthicsAttacks(self.subcategories, self.simulator_model, self.evaluation_model)

    def _get_metric(self, attack: RTTestCase) -> BaseRedTeamingMetric:
        return self.attack_builder._get_metric(attack)

    def simulate_attacks(self, attacks_per_vulnerability_type: int = 1) -> List[RTTestCase]:
        return cast(EthicsAttacks, self.attack_builder).simulate_attacks(
            attacks_per_vulnerability_type=attacks_per_vulnerability_type
        )

    @property
    def description(self) -> str:
        return """Prompt that tries to provoke responses from the chatbot that show whether the target LLM can reason 
        and act in ways that align with ethical principles and organizational values. More specifically, it focuses on 
        testing whether the target LLM can be influenced to produce outputs that violate moral reasoning, obscure truth,
        disrespect cultural norms, bypass consent, enable harmful or dual-use behavior, or avoid accountability.
        Above that, it also tries to produce responses that support illegal, forbidden or non-compliant banking-specific 
        activities."""
