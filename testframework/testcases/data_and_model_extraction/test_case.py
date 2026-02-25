from __future__ import annotations

from deepteam.metrics import BaseRedTeamingMetric
from deepteam.test_case import RTTestCase

from testframework.enums import Category
from testframework.testcases.base import BaseTestCase


class DataAndModelExtractionTestCase(BaseTestCase):
    """Test case for data and model extraction attacks."""

    Subcategory = None

    def __init__(self) -> None:
        # TODO: Initialize with proper vulnerability builder
        super().__init__(
            Category.DATA_AND_MODEL_EXTRACTION,
            None,
            None,  # TODO: Add attack builder
        )

    def _get_metric(self, attack: RTTestCase = None) -> BaseRedTeamingMetric:
        # TODO: Implement metric
        raise NotImplementedError("DataAndModelExtractionTestCase._get_metric not yet implemented")

    def enhance_base_attack(self, base_attack: str) -> tuple[str, str | None]:
        # TODO: Implement enhancement logic
        raise NotImplementedError("DataAndModelExtractionTestCase.enhance_base_attack not yet implemented")
