#  Copyright (c) 2026.
#  Florian Emanuel Sauer

from __future__ import annotations

from typing import cast, List

from deepteam.metrics import BaseRedTeamingMetric  # type: ignore
from deepteam.test_case import RTTestCase
from testframework.enums import Category
from testframework.testcases.base import BaseTestCase
from testframework.testcases.excessive_agency.builder import ExcessiveAgencyAttacks


class ExcessiveAgencyTestCase(BaseTestCase):
    """Test case for excessive agency attacks."""

    def __init__(self) -> None:
        super().__init__(
            Category.EXCESSIVE_AGENCY,
            []
        )
        self.set_attack_builder()

    def set_attack_builder(self) -> None:
        self.attack_builder = ExcessiveAgencyAttacks(self.subcategories, self.simulator_model, self.evaluation_model)

    def _get_metric(self, attack: RTTestCase = None) -> BaseRedTeamingMetric:
        return self.attack_builder._get_metric()

    def simulate_attacks(self, attacks_per_vulnerability_type: int = 1) -> List[RTTestCase]:
        return cast(ExcessiveAgencyAttacks, self.attack_builder).simulate_attacks()
