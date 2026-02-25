from __future__ import annotations
from enum import Enum
from typing import List
from deepteam.metrics import BaseRedTeamingMetric # type: ignore
from deepteam.test_case import RTTestCase
from testframework.enums import Category, Severity
from testframework.testcases.base import BaseTestCase
from testframework.testcases.benign.attack_builder import BenignAttacks

class Subcategory(str, Enum):
    """Subcategories for benign tests."""
    BANKING = "banking"

class BenignTestCase(BaseTestCase):
    """Test case for benign/safe prompts."""

    # TODO: Map to deepteam types when available
    SUBCATEGORY_TO_TYPE: dict[Subcategory, str] = {
        Subcategory.BANKING: "banking",
    }

    def __init__(self, subcategories: List[Subcategory] | None = None) -> None:
        super().__init__(
            Category.BENIGN,
            subcategories,
            severity=Severity.SAFE
        )
        # set only after simulator_model is available
        self.attack_builder = BenignAttacks(self.subcategories)

    def _get_metric(self, attack: RTTestCase) -> BaseRedTeamingMetric:
        return self.attack_builder._get_metric()

    def enhance_base_attack(self, base_attack: str) -> tuple[str, str | None]:
        raise NotImplementedError("BenignTestCase.enhance_base_attack not yet implemented")
