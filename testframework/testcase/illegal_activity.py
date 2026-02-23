from __future__ import annotations

from typing import cast

from deepteam.metrics import BaseRedTeamingMetric
from deepteam.test_case import RTTestCase
from deepteam.vulnerabilities import IllegalActivity  # type: ignore
from deepteam.vulnerabilities.illegal_activity import IllegalActivityType

from ..enums import Category, TestCaseName
from ..models import TestCaseResult, Attack
from .base import BaseTestCase


class IllegalActivityTestCase(BaseTestCase):
    """Test case using DeepTeam's IllegalActivity vulnerability as an attack source."""

    def __init__(self) -> None:
        super().__init__(TestCaseName.ILLEGAL_ACTIVITY,
                         Category.ILLEGAL_ACTIVITY,
                         None,
                         IllegalActivity()
                         )

    def _get_metric(self, attack: RTTestCase = None) -> BaseRedTeamingMetric:
        illegal_activity = cast(IllegalActivity, self.attack_builder)
        attack_type = cast(IllegalActivityType, attack.vulnerability_type)
        return illegal_activity._get_metric(type=attack_type)

    def enhance_base_attack(self, base_attack: str) -> str:
        pass

    def store_results(self, results: TestCaseResult) -> str:
        pass
