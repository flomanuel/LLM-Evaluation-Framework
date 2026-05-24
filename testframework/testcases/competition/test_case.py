#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

from testframework.redteam.metric_protocol import RedTeamingMetric
from testframework.redteam.registry import create_builder, create_metric
from testframework.redteam.test_case import RTTestCase

from testframework.enums import Category
from testframework.testcases.base import BaseTestCase
from testframework.util.ollama_handler import OllamaGenerator


class CompetitionTestCase(BaseTestCase):
    """Test case for competition-related attacks."""

    def __init__(self) -> None:
        super().__init__(
            Category.COMPETITION,
            [],
        )

    def setup_attack_builder(self) -> None:
        """Set up the attack builder."""
        self.simulator_model = OllamaGenerator.get_chatbot()
        OllamaGenerator.start_model_if_not_running()
        self.attack_builder = create_builder(
            "competition",
            self.subcategories,
            self.simulator_model,
            self.evaluation_model,
        )

    def _get_metric(self, attack: RTTestCase) -> RedTeamingMetric:
        """Get the metric for the test case."""
        return create_metric("competition", self.evaluation_model, attack)

    def simulate_attacks(self, attacks_per_vulnerability_type: int = 1) -> list[RTTestCase]:
        """Simulate attacks for the test case."""
        return self.attack_builder.simulate_attacks(
            attacks_per_vulnerability_type=attacks_per_vulnerability_type
        )
