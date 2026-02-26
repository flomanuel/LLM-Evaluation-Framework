from __future__ import annotations
from typing import cast
from deepteam.metrics import BaseRedTeamingMetric  # type: ignore
from deepteam.test_case import RTTestCase
from deepteam.vulnerabilities import Robustness
from deepteam.vulnerabilities.robustness import RobustnessType
from testframework.enums import Category
from testframework.testcases.base import BaseTestCase


class RobustnessTestCase(BaseTestCase):
    """Test case for robustness attacks."""

    def __init__(self) -> None:
        super().__init__(
            Category.ROBUSTNESS,
            []
        )
        self.attack_builder = Robustness(
            simulator_model=self.simulator_model,
            types=[RobustnessType.HIJACKING.value]
        )

    def _get_metric(self, attack: RTTestCase) -> BaseRedTeamingMetric:
        attack_type = cast(RobustnessType, attack.vulnerability_type)
        return cast(Robustness, self.attack_builder)._get_metric(type=attack_type)

    def enhance_base_attack(self, base_attack: str) -> tuple[str, str | None]:
        return base_attack, None
