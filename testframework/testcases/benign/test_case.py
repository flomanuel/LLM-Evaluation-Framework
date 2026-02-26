from __future__ import annotations

from typing import List

from deepteam.metrics import BaseRedTeamingMetric  # type: ignore
from deepteam.test_case import RTTestCase

from testframework.enums import Category, Severity
from testframework.testcases.base import BaseTestCase
from testframework.testcases.benign.attack_builder import BenignAttacks
from testframework.testcases.benign.subcategory import BenignSubcategory


class BenignTestCase(BaseTestCase):
    """Test case for benign/safe prompts."""

    def __init__(self, subcategories: List[BenignSubcategory] | None = None) -> None:
        super().__init__(
            Category.BENIGN,
            subcategories,
            severity=Severity.SAFE
        )
        # set only after simulator_model is available
        self.attack_builder = BenignAttacks(self.subcategories)

    def _get_metric(self, attack: RTTestCase) -> BaseRedTeamingMetric:
        return self.attack_builder._get_metric()
