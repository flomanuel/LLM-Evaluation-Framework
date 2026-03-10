#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.


from __future__ import annotations
from typing import cast, List
from deepteam.metrics import BaseRedTeamingMetric
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
        """Setup the attack builder."""
        self.simulator_model = OllamaGenerator.get_chatbot()
        OllamaGenerator.start_model_if_not_running()
        self.attack_builder = ExcessiveAgencyAttacks(self.subcategories, self.simulator_model, self.evaluation_model)

    def _get_metric(self, attack: RTTestCase = None) -> BaseRedTeamingMetric:
        """Get the metric for the test case."""
        return self.attack_builder._get_metric()

    def simulate_attacks(self, attacks_per_vulnerability_type: int = 1) -> List[RTTestCase]:
        """Simulate attacks for the test case."""
        return cast(ExcessiveAgencyAttacks, self.attack_builder).simulate_attacks()
