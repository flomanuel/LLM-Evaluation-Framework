from __future__ import annotations

from enum import Enum
from typing import cast, List

from deepteam.metrics import BaseRedTeamingMetric
from deepteam.test_case import RTTestCase
from deepteam.vulnerabilities import IllegalActivity  # type: ignore
from deepteam.vulnerabilities.illegal_activity import IllegalActivityType
from deepteam.attacks.single_turn import MathProblem

from testframework.enums import Category
from testframework.testcases.base import BaseTestCase


class IllegalActivityTestCase(BaseTestCase):
    """Test case using DeepTeam's IllegalActivity vulnerability as an attack source."""

    class Subcategory(str, Enum):
        """Subcategories for illegal activity attacks."""
        WEAPONS = "weapons"
        CHILD_EXPLOITATION = "child-exploitation"

        # todo: add a mapper from Enum.Subcategory to DeepTeam.IllegalActivityType

    def __init__(self, subcategory: Subcategory | None = None) -> None:
        self._subcategory = subcategory
        super().__init__(
            Category.ILLEGAL_ACTIVITY,
            subcategory,
        )
        # set only after simulator_model is available
        self._init_attack_builder()

    def _init_attack_builder(self) -> None:
        """Initialize the attack builder after simulator_model is available."""
        # todo: add "illegal activity" with sub categories "weapons" and "child-exploitation" for from CSV file.
        #  Use subcategories to select test cases for DeepTeam.IllegalActivity and CSV.IllegalActivity.

        self.attack_builder = IllegalActivity(simulator_model=self.simulator_model)

    def _get_metric(self, attack: RTTestCase = None) -> BaseRedTeamingMetric:
        illegal_activity: IllegalActivity = cast(IllegalActivity, self.attack_builder)
        attack_type = cast(IllegalActivityType, attack.vulnerability_type)
        return illegal_activity._get_metric(type=attack_type)  # pylint: disable=protected-access

    def enhance_base_attack(self, base_attack: str) -> tuple[str, str | None]:
        # todo: implement full enhancement logic
        mp = MathProblem()
        return mp.enhance(base_attack), "MathProblem"
