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
        self.simulator_model = OllamaGenerator.get_chatbot()
        OllamaGenerator.start_model_if_not_running()
        self.set_attack_builder()

    def set_attack_builder(self) -> None:
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
