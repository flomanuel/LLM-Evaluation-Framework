from __future__ import annotations

from deepteam.metrics import BaseRedTeamingMetric
from deepteam.test_case import RTTestCase

from testframework.enums import Category
from testframework.testcases.base import BaseTestCase


class SensitiveInformationDisclosureTestCase(BaseTestCase):
    """Test case for sensitive information disclosure attacks."""

    Subcategory = None

    def __init__(self) -> None:
        # TODO: Initialize with proper vulnerability builder
        super().__init__(
            Category.SENSITIVE_INFORMATION_DISCLOSURE,
            None,
            None,  # TODO: Add attack builder
        )

    def _get_metric(self, attack: RTTestCase = None) -> BaseRedTeamingMetric:
        # TODO: Implement metric
        raise NotImplementedError("SensitiveInformationDisclosureTestCase._get_metric not yet implemented")

    def enhance_base_attack(self, base_attack: str) -> tuple[str, str | None]:
        # TODO: Implement enhancement logic
        raise NotImplementedError("SensitiveInformationDisclosureTestCase.enhance_base_attack not yet implemented")
