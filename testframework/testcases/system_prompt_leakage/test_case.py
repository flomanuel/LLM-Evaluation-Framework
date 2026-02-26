from __future__ import annotations
from typing import List
from deepteam.metrics import BaseRedTeamingMetric  # type: ignore
from deepteam.test_case import RTTestCase
from testframework.enums import Category
from testframework.testcases.base import BaseTestCase
from testframework.testcases.system_prompt_leakage.attack_builder import SystemPromptLeakageAttacks
from testframework.testcases.system_prompt_leakage.subcategory import SystemPromptLeakageSubcategory


class SystemPromptLeakageTestCase(BaseTestCase):
    """Test case for system prompt leakage attacks."""

    def __init__(self, subcategories: List[SystemPromptLeakageSubcategory] | None = None) -> None:
        super().__init__(
            Category.SYSTEM_PROMPT_LEAKAGE,
            subcategories
        )
        self.attack_builder = SystemPromptLeakageAttacks(self.subcategories, self.simulator_model)

    def _get_metric(self, attack: RTTestCase) -> BaseRedTeamingMetric:
        return self.attack_builder._get_metric(attack)
