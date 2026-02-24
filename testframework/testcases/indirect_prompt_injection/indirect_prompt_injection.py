from __future__ import annotations

from deepteam.metrics import BaseRedTeamingMetric
from deepteam.test_case import RTTestCase

from testframework.enums import Category
from testframework.testcases.base import BaseTestCase


class IndirectPromptInjectionTestCase(BaseTestCase):
    """Test case for indirect prompt injection attacks."""

    Subcategory = None

    def __init__(self) -> None:
        # TODO: Initialize with proper vulnerability builder
        super().__init__(
            Category.INDIRECT_PROMPT_INJECTION,
            None,
            None,  # TODO: Add attack builder
        )

    def _get_metric(self, attack: RTTestCase = None) -> BaseRedTeamingMetric:
        # TODO: Implement metric
        raise NotImplementedError("IndirectPromptInjectionTestCase._get_metric not yet implemented")

    def enhance_base_attack(self, base_attack: str) -> tuple[str, str | None]:
        # TODO: Implement enhancement logic
        raise NotImplementedError("IndirectPromptInjectionTestCase.enhance_base_attack not yet implemented")

