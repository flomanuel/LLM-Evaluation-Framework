#  Copyright (c) 2026.
#  Florian Emanuel Sauer

from __future__ import annotations

from typing import cast, List
from deepteam.metrics import BaseRedTeamingMetric
from deepteam.test_case import RTTestCase
from deepteam.vulnerabilities import Competition
from deepteam.vulnerabilities.competition import CompetitionType

from testframework.enums import Category
from testframework.testcases.base import BaseTestCase


class CompetitionTestCase(BaseTestCase):
    """Test case for competition-related attacks."""

    def __init__(self) -> None:
        super().__init__(
            Category.COMPETITION,
            [],
        )
        self.set_attack_builder()

    def set_attack_builder(self) -> None:
        self.attack_builder = Competition(simulator_model=self.simulator_model, evaluation_model=self.evaluation_model)

    def _get_metric(self, attack: RTTestCase) -> BaseRedTeamingMetric:
        attack_type = cast(CompetitionType, attack.vulnerability_type)
        return cast(Competition, self.attack_builder)._get_metric(type=attack_type)  # pylint: disable=protected-access

    def simulate_attacks(self, attacks_per_vulnerability_type: int = 1) -> List[RTTestCase]:
        return cast(Competition, self.attack_builder).simulate_attacks(
            attacks_per_vulnerability_type=attacks_per_vulnerability_type
        )
