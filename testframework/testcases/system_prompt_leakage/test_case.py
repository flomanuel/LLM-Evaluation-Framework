#  Copyright (c) 2026.
#  Florian Emanuel Sauer

from __future__ import annotations
from typing import List, cast
from deepteam.metrics import BaseRedTeamingMetric  # type: ignore
from deepteam.test_case import RTTestCase
from testframework.enums import Category
from testframework.testcases.base import BaseTestCase
from testframework.testcases.system_prompt_leakage.builder import SystemPromptLeakageAttacks
from testframework.testcases.system_prompt_leakage.subcategory import SystemPromptLeakageSubcategory


class SystemPromptLeakageTestCase(BaseTestCase):
    """Test case for system prompt leakage attacks."""

    def __init__(self, subcategories: List[SystemPromptLeakageSubcategory] = None) -> None:
        super().__init__(
            Category.SYSTEM_PROMPT_LEAKAGE,
            subcategories
        )
        self.set_attack_builder()

    def set_attack_builder(self) -> None:
        self.attack_builder = SystemPromptLeakageAttacks(self.subcategories, self.simulator_model,
                                                         self.evaluation_model)

    def _get_metric(self, attack: RTTestCase) -> BaseRedTeamingMetric:
        return self.attack_builder._get_metric(attack)

    def simulate_attacks(self, attacks_per_vulnerability_type: int = 1) -> List[RTTestCase]:
        return cast(SystemPromptLeakageAttacks, self.attack_builder).simulate_attacks(
            attacks_per_vulnerability_type=attacks_per_vulnerability_type)
