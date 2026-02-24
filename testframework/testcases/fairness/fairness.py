from __future__ import annotations

from enum import Enum

from deepteam.metrics import BaseRedTeamingMetric
from deepteam.test_case import RTTestCase

from testframework.enums import Category
from testframework.testcases.base import BaseTestCase


class FairnessTestCase(BaseTestCase):
    """Test case for fairness-related attacks."""

    class Subcategory(str, Enum):
        """Subcategories for fairness attacks."""
        BANKING = "banking"
        DISCRIMINATION = "discrimination"
        DISTRIBUTIVE_FAIRNESS = "distributive-fairness"
        PROCEDURAL_FAIRNESS = "procedural-fairness"

    # TODO: Map to deepteam types when available
    SUBCATEGORY_TO_TYPE: dict[Subcategory, str] = {
        Subcategory.BANKING: "banking",
        Subcategory.DISCRIMINATION: "discrimination",
        Subcategory.DISTRIBUTIVE_FAIRNESS: "distributive_fairness",
        Subcategory.PROCEDURAL_FAIRNESS: "procedural_fairness",
    }

    def __init__(self, subcategory: Subcategory | None = None) -> None:
        self._subcategory = subcategory
        # TODO: Initialize with proper vulnerability builder
        super().__init__(
            Category.FAIRNESS,
            subcategory,
            None,  # TODO: Add attack builder
        )

    def _get_metric(self, attack: RTTestCase = None) -> BaseRedTeamingMetric:
        # TODO: Implement metric
        raise NotImplementedError("FairnessTestCase._get_metric not yet implemented")

    def enhance_base_attack(self, base_attack: str) -> tuple[str, str | None]:
        # TODO: Implement enhancement logic
        raise NotImplementedError("FairnessTestCase.enhance_base_attack not yet implemented")
