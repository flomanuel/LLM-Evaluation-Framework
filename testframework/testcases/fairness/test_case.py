#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.



from __future__ import annotations

from typing import List, cast
from deepteam.metrics import BaseRedTeamingMetric  # type: ignore
from deepteam.test_case import RTTestCase
from testframework.enums import Category
from testframework.testcases.base import BaseTestCase
from testframework.testcases.fairness.builder import FairnessAttacks
from testframework.testcases.fairness.subcategory import FairnessSubcategory
from testframework.util.ollama_handler import OllamaGenerator


class FairnessTestCase(BaseTestCase):
    """Test case for fairness-related attacks."""

    def __init__(self, subcategories: List[FairnessSubcategory] = None) -> None:
        super().__init__(
            Category.FAIRNESS,
            subcategories,
        )

    def setup_attack_builder(self) -> None:
        self.simulator_model = OllamaGenerator.get_chatbot()
        OllamaGenerator.start_model_if_not_running()
        self.attack_builder = FairnessAttacks(self.subcategories, self.simulator_model, self.evaluation_model)

    def _get_metric(self, attack: RTTestCase) -> BaseRedTeamingMetric:
        return self.attack_builder._get_metric()

    def simulate_attacks(self, attacks_per_vulnerability_type: int = 1) -> List[RTTestCase]:
        return cast(FairnessAttacks, self.attack_builder).simulate_attacks()

    @property
    def description(self) -> str:
        # desc source: https://www.trydeepteam.com/docs/red-teaming-vulnerabilities-fairness
        return """Prompt that tries to provoke responses that do NOT uphold equitable treatment and decision-making 
        across groups, individuals, and contexts. More specifically, it tests if the target LLM can be influenced to 
        produce outputs that support the user in treating other people unfairly or discriminate against groups.
        """
