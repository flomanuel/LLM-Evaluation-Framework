#  Copyright (c) 2026.
#  Florian Emanuel Sauer

from __future__ import annotations

from typing import cast, List

from deepteam.metrics import BaseRedTeamingMetric  # type: ignore
from deepteam.test_case import RTTestCase
from testframework.enums import Category
from testframework.testcases.base import BaseTestCase
from testframework.testcases.privacy_violations.builder import PrivacyViolationsAttacks
from testframework.util.ollama_handler import OllamaGenerator


class PrivacyViolationsTestCase(BaseTestCase):
    """Test case for privacy violations attacks."""

    def __init__(self) -> None:
        super().__init__(
            Category.PRIVACY_VIOLATIONS,
            []
        )

    def setup_attack_builder(self) -> None:
        self.simulator_model = OllamaGenerator.get_chatbot()
        OllamaGenerator.start_model_if_not_running()
        self.attack_builder = PrivacyViolationsAttacks(self.subcategories, self.simulator_model, self.evaluation_model)

    def _get_metric(self, attack: RTTestCase = None) -> BaseRedTeamingMetric:
        return self.attack_builder._get_metric()

    def simulate_attacks(self, attacks_per_vulnerability_type: int = 1) -> List[RTTestCase]:
        return cast(PrivacyViolationsAttacks, self.attack_builder).simulate_attacks()[:2]

    @property
    def description(self) -> str:
        return """Prompt that tries to extract sensitive or personal information from the LLM such das PII, 
        Names, Work Contract, CVs/Resumes, internal investigations, termination plans, parental leaves, sick days and more.
        """
