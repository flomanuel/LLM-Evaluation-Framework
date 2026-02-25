from __future__ import annotations

from enum import Enum
from typing import List
from deepteam.metrics import BaseRedTeamingMetric # type: ignore
from deepteam.test_case import RTTestCase
from deepteam.vulnerabilities import IllegalActivity  # type: ignore
from deepteam.attacks.single_turn import MathProblem
from testframework.enums import Category
from testframework.testcases.base import BaseTestCase
from testframework.testcases.illegal_activity.attack_builder import IllegalActivity


class Subcategory(str, Enum):
    """Subcategories for illegal activity attacks."""
    WEAPONS = "weapons"
    CHILD_EXPLOITATION = "child-exploitation"
    ILLEGAL_DRUGS = "illegal-drugs"
    VIOLENT_CRIME = "violent-crime"
    NONVIOLENT_CRIME = "nonviolent-crime"
    SEX_CRIME = "sex-crime"
    CYBERCRIME = "cyber-crime"

class IllegalActivityTestCase(BaseTestCase):
    """Test case using DeepTeam's IllegalActivity vulnerability as an attack source."""

        # todo: add a mapper from Enum.Subcategory to DeepTeam.IllegalActivityType

    def __init__(self, subcategories: List[Subcategory]) -> None:
        super().__init__(
            Category.ILLEGAL_ACTIVITY,
            subcategories,
        )
        # set only after simulator_model is available
        self.attack_builder = IllegalActivity(self.subcategories, self.simulator_model)

    def _get_metric(self, attack: RTTestCase) -> BaseRedTeamingMetric:
        return self.attack_builder._get_metric(attack)

    def enhance_base_attack(self, base_attack: str) -> tuple[str, str | None]:
        # todo: implement full enhancement logic
        mp = MathProblem()
        return mp.enhance(base_attack), "MathProblem"

# prompt,secerity,category,tool_check,tool_check_condition,remote_attack_generation,document
