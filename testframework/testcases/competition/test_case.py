from __future__ import annotations

from typing import cast
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
        self.attack_builder = Competition(simulator_model=self.simulator_model, evaluation_model=self.evaluation_model)

    def _get_metric(self, attack: RTTestCase) -> BaseRedTeamingMetric:
        attack_type = cast(CompetitionType, attack.vulnerability_type)
        return cast(Competition, self.attack_builder)._get_metric(type=attack_type) # pylint: disable=protected-access
