from __future__ import annotations

from enum import Enum

from deepteam.metrics import BaseRedTeamingMetric
from deepteam.test_case import RTTestCase

from testframework.enums import Category
from testframework.testcases.base import BaseTestCase


class EthicsTestCase(BaseTestCase):
    """Test case for ethics-related attacks."""

    class Subcategory(str, Enum):
        """Subcategories for ethics attacks."""
        BANKING = "banking"
        HARM_PREVENTION = "harm-prevention"
        MORAL_INTEGRITY = "moral-integrity"

    # TODO: Map to deepteam types when available
    SUBCATEGORY_TO_TYPE: dict[Subcategory, str] = {
        Subcategory.BANKING: "banking",
        Subcategory.HARM_PREVENTION: "harm_prevention",
        Subcategory.MORAL_INTEGRITY: "moral_integrity",
    }

    def __init__(self, subcategory: Subcategory | None = None) -> None:
        self._subcategory = subcategory
        # TODO: Initialize with proper vulnerability builder
        super().__init__(
            Category.ETHICS,
            subcategory,
            None,  # TODO: Add attack builder
        )

    def _get_metric(self, attack: RTTestCase = None) -> BaseRedTeamingMetric:
        # TODO: Implement metric
        raise NotImplementedError("EthicsTestCase._get_metric not yet implemented")

    def enhance_base_attack(self, base_attack: str) -> tuple[str, str | None]:
        # TODO: Implement enhancement logic
        raise NotImplementedError("EthicsTestCase.enhance_base_attack not yet implemented")
