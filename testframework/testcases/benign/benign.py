from __future__ import annotations

from enum import Enum
from typing import List

from deepteam.metrics import BaseRedTeamingMetric
from deepteam.test_case import RTTestCase
from deepteam.vulnerabilities import BaseVulnerability

from testframework.enums import Category, Severity
from testframework.testcases.base import BaseTestCase


class BenignTestCase(BaseTestCase):
    """Test case for benign/safe prompts."""

    class Subcategory(str, Enum):
        """Subcategories for benign tests."""
        BANKING = "banking"

    # TODO: Map to deepteam types when available
    SUBCATEGORY_TO_TYPE: dict[Subcategory, str] = {
        Subcategory.BANKING: "banking",
    }

    def __init__(self, subcategory: Subcategory | None = None) -> None:
        self._subcategory = subcategory
        # TODO: Initialize with proper vulnerability builder
        super().__init__(
            Category.BENIGN,
            subcategory,
            None,  # TODO: Add attack builder
            severity=Severity.SAFE
        )

    def _get_metric(self, attack: RTTestCase = None) -> BaseRedTeamingMetric:
        # TODO: Implement metric
        raise NotImplementedError("BenignTestCase._get_metric not yet implemented")

    def enhance_base_attack(self, base_attack: str) -> tuple[str, str | None]:
        # TODO: Implement enhancement logic
        raise NotImplementedError("BenignTestCase.enhance_base_attack not yet implemented")
