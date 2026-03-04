#  Copyright (c) 2026.
#  Florian Emanuel Sauer

from __future__ import annotations
from typing import cast, List
from deepteam.metrics import BaseRedTeamingMetric  # type: ignore
from deepteam.test_case import RTTestCase
from deepteam.vulnerabilities import Robustness
from deepteam.vulnerabilities.robustness import RobustnessType
from testframework.enums import Category
from testframework.testcases.base import BaseTestCase
from testframework.util.ollama_handler import OllamaGenerator


class RobustnessTestCase(BaseTestCase):
    """Test case for robustness attacks."""

    def __init__(self) -> None:
        super().__init__(
            Category.ROBUSTNESS,
            []
        )

    def setup_attack_builder(self) -> None:
        self.simulator_model = OllamaGenerator.get_chatbot()
        OllamaGenerator.start_model_if_not_running()
        self.attack_builder = Robustness(
            simulator_model=self.simulator_model,
            evaluation_model=self.evaluation_model,
            types=[RobustnessType.HIJACKING.value]
        )

    def _get_metric(self, attack: RTTestCase) -> BaseRedTeamingMetric:
        attack_type = cast(RobustnessType, attack.vulnerability_type)
        return cast(Robustness, self.attack_builder)._get_metric(type=attack_type)

    def simulate_attacks(self, attacks_per_vulnerability_type: int = 1) -> List[RTTestCase]:
        return cast(Robustness, self.attack_builder).simulate_attacks(
            attacks_per_vulnerability_type=attacks_per_vulnerability_type)

    @property
    def description(self) -> str:
        return """Prompt that tries to persuade the LLM into processing malicious inputs and being overly influenced by 
        user-provided data that compromise its intended behavior. More specifically, the prompt focuses on testing 
        whether the system mitigates risks from crafted prompts designed to hijack or alter its functionality."""
