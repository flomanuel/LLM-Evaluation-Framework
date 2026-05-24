#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.


from typing import cast
from testframework.redteam.metric_protocol import RedTeamingMetric
from testframework.redteam.test_case import RTTestCase
from testframework.enums import Category
from testframework.testcases.base import BaseTestCase
from testframework.testcases.bias.builder import BiasAttacks
from testframework.testcases.bias.subcategory import BiasSubcategory
from testframework.util.ollama_handler import OllamaGenerator


class BiasTestCase(BaseTestCase):
    """Test case for bias attacks."""

    def __init__(self, subcategories: list[BiasSubcategory]) -> None:
        super().__init__(
            Category.BIAS,
            subcategories,
        )

    def setup_attack_builder(self) -> None:
        """Set up the attack builder."""
        self.simulator_model = OllamaGenerator.get_chatbot()
        OllamaGenerator.start_model_if_not_running()
        self.attack_builder: BiasAttacks = BiasAttacks(self.subcategories, self.simulator_model, self.evaluation_model)

    def _get_metric(self, attack: RTTestCase) -> RedTeamingMetric:
        """Get the metric for the test case."""
        return self.attack_builder._get_metric(attack)  # pylint: disable=protected-access

    def simulate_attacks(self, attacks_per_vulnerability_type: int = 1) -> list[RTTestCase]:
        """Simulate attacks for the test case."""
        return cast(BiasAttacks, self.attack_builder).simulate_attacks(
            attacks_per_vulnerability_type=attacks_per_vulnerability_type
        )
