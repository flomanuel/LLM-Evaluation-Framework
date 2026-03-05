#  Copyright (c) 2026.
#  Florian Emanuel Sauer

from __future__ import annotations
from typing import cast, List
from deepteam.metrics import BaseRedTeamingMetric  # type: ignore
from deepteam.test_case import RTTestCase
from testframework.enums import Category
from testframework.testcases.base import BaseTestCase
from testframework.testcases.excessive_agency.builder import ExcessiveAgencyAttacks
from testframework.util.ollama_handler import OllamaGenerator


class ExcessiveAgencyTestCase(BaseTestCase):
    """Test case for excessive agency attacks."""

    def __init__(self) -> None:
        super().__init__(
            Category.EXCESSIVE_AGENCY,
            []
        )

    def setup_attack_builder(self) -> None:
        self.simulator_model = OllamaGenerator.get_chatbot()
        OllamaGenerator.start_model_if_not_running()
        self.attack_builder = ExcessiveAgencyAttacks(self.subcategories, self.simulator_model, self.evaluation_model)

    def _get_metric(self, attack: RTTestCase = None) -> BaseRedTeamingMetric:
        return self.attack_builder._get_metric()

    def simulate_attacks(self, attacks_per_vulnerability_type: int = 1) -> List[RTTestCase]:
        return cast(ExcessiveAgencyAttacks, self.attack_builder).simulate_attacks()[:2]

    @property
    def description(self) -> str:
        # desc source: https://www.trydeepteam.com/docs/red-teaming-vulnerabilities-excessive-agency
        return """Prompt that tries to provoke responses or actions from the LLM that exceed the LLMs intended scope or 
        safeguards. More specifically, it focuses on testing whether the model misuses features, grants excessive 
        permissions, or operates autonomously without proper oversight. Above that, the prompt also tries to missues
        existing tools."""
