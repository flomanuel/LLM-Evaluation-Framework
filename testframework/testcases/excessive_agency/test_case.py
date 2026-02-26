from __future__ import annotations
from deepteam.metrics import BaseRedTeamingMetric  # type: ignore
from deepteam.test_case import RTTestCase
from testframework.enums import Category
from testframework.testcases.base import BaseTestCase
from testframework.testcases.excessive_agency.attack_builder import ExcessiveAgencyAttacks


class ExcessiveAgencyTestCase(BaseTestCase):
    """Test case for excessive agency attacks."""

    def __init__(self) -> None:
        super().__init__(
            Category.EXCESSIVE_AGENCY,
            []
        )
        self.attack_builder = ExcessiveAgencyAttacks(self.subcategories)

    def _get_metric(self, attack: RTTestCase = None) -> BaseRedTeamingMetric:
        return self.attack_builder._get_metric()
