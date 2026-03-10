#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.



from __future__ import annotations
from typing import List, cast
from deepteam.metrics import BaseRedTeamingMetric
from deepteam.test_case import RTTestCase
from testframework.enums import Category
from testframework.testcases.base import BaseTestCase
from testframework.testcases.system_prompt_leakage.builder import SystemPromptLeakageAttacks
from testframework.testcases.system_prompt_leakage.subcategory import SystemPromptLeakageSubcategory
from testframework.util.ollama_handler import OllamaGenerator


class SystemPromptLeakageTestCase(BaseTestCase):
    """Test case for system prompt leakage attacks."""

    def __init__(self, subcategories: List[SystemPromptLeakageSubcategory] = None) -> None:
        super().__init__(
            Category.SYSTEM_PROMPT_LEAKAGE,
            subcategories
        )

    def setup_attack_builder(self) -> None:
        self.simulator_model = OllamaGenerator.get_chatbot()
        OllamaGenerator.start_model_if_not_running()
        self.attack_builder = SystemPromptLeakageAttacks(self.subcategories, self.simulator_model,
                                                         self.evaluation_model)

    def _get_metric(self, attack: RTTestCase) -> BaseRedTeamingMetric:
        return self.attack_builder._get_metric(attack)

    def simulate_attacks(self, attacks_per_vulnerability_type: int = 1) -> List[RTTestCase]:
        return cast(SystemPromptLeakageAttacks, self.attack_builder).simulate_attacks(
            attacks_per_vulnerability_type=attacks_per_vulnerability_type)
