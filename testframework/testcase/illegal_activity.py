from __future__ import annotations

from typing import cast

from deepteam.metrics import BaseRedTeamingMetric
from deepteam.test_case import RTTestCase
from deepteam.vulnerabilities import IllegalActivity  # type: ignore
from deepteam.vulnerabilities.illegal_activity import IllegalActivityType
from deepteam.attacks.single_turn import MathProblem

from ..enums import Category, TestCaseName
from .base import BaseTestCase


class IllegalActivityTestCase(BaseTestCase):
    """Test case using DeepTeam's IllegalActivity vulnerability as an attack source."""

    def __init__(self) -> None:
        super().__init__(TestCaseName.ILLEGAL_ACTIVITY,
                         Category.ILLEGAL_ACTIVITY,
                         None,
                         IllegalActivity(simulator_model=self.simulator_model)
                         )

    def _get_metric(self, attack: RTTestCase = None) -> BaseRedTeamingMetric:
        illegal_activity: IllegalActivity = cast(IllegalActivity, self.attack_builder)
        attack_type = cast(IllegalActivityType, attack.vulnerability_type)
        return illegal_activity._get_metric(type=attack_type)  # pylint: disable=protected-access

    def enhance_base_attack(self, base_attack: str) -> tuple[str, str | None]:
        # todo: implement full enhancement logic
        mp = MathProblem()
        return mp.enhance(base_attack), "MathProblem"
