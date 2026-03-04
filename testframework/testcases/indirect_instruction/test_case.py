#  Copyright (c) 2026.
#  Florian Emanuel Sauer

from __future__ import annotations

from typing import List, cast
from deepteam.metrics import BaseRedTeamingMetric  # type: ignore
from deepteam.test_case import RTTestCase
from testframework.enums import Category
from testframework.testcases.base import BaseTestCase
from testframework.testcases.indirect_instruction.builder import IndirectInstructionAttacks
from testframework.testcases.indirect_instruction.subcategory import IndirectInstructionSubcategory
from testframework.util.ollama_handler import OllamaGenerator


class IndirectInstructionTestCase(BaseTestCase):
    """Test case for indirect instruction attacks."""

    def __init__(self, subcategories: List[IndirectInstructionSubcategory]) -> None:
        super().__init__(
            Category.INDIRECT_PROMPT_INJECTION,
            subcategories,
        )

    def setup_attack_builder(self) -> None:
        self.simulator_model = OllamaGenerator.get_chatbot()
        OllamaGenerator.start_model_if_not_running()
        self.attack_builder = IndirectInstructionAttacks(self.subcategories, self.simulator_model,
                                                         self.evaluation_model)

    def _get_metric(self, attack: RTTestCase = None) -> BaseRedTeamingMetric:
        return self.attack_builder._get_metric(attack)

    def simulate_attacks(self, attacks_per_vulnerability_type: int = 1) -> List[RTTestCase]:
        return cast(IndirectInstructionAttacks, self.attack_builder).simulate_attacks()
