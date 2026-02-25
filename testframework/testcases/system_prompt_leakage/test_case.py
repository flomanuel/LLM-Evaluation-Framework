from __future__ import annotations

from deepteam.metrics import BaseRedTeamingMetric
from deepteam.test_case import RTTestCase

from testframework.enums import Category
from testframework.testcases.base import BaseTestCase


class SystemPromptLeakageTestCase(BaseTestCase):
    """Test case for system prompt leakage attacks."""

    Subcategory = None

    def __init__(self) -> None:
        # TODO: Initialize with proper vulnerability builder
        super().__init__(
            Category.SYSTEM_PROMPT_LEAKAGE,
            None,
            None,  # TODO: Add attack builder
        )

    def _get_metric(self, attack: RTTestCase = None) -> BaseRedTeamingMetric:
        # TODO: Implement metric
        raise NotImplementedError("SystemPromptLeakageTestCase._get_metric not yet implemented")

    def enhance_base_attack(self, base_attack: str) -> tuple[str, str | None]:
        # TODO: Implement enhancement logic
        raise NotImplementedError("SystemPromptLeakageTestCase.enhance_base_attack not yet implemented")
