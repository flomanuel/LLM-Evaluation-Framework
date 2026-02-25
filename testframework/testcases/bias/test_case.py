from __future__ import annotations
from enum import Enum
from typing import List
from deepteam.metrics import BaseRedTeamingMetric # type: ignore
from deepteam.test_case import RTTestCase
from deepeval.models import DeepEvalBaseLLM
from deepteam.vulnerabilities import Bias # type: ignore
from testframework.enums import Category
from testframework.testcases.base import BaseTestCase


class BiasTestCase(BaseTestCase):
    """Test case for bias attacks."""

    def __init__(self) -> None:
        super().__init__(
            Category.BIAS,
            [],
        )
        # set only after simulator_model is available
        self.attack_builder = Bias(simulator_model=self.simulator_model)

    def _get_metric(self, attack: RTTestCase) -> BaseRedTeamingMetric:
        return self.attack_builder._get_metric(attack)

    def enhance_base_attack(self, base_attack: str) -> tuple[str, str | None]:
        # TODO: Implement enhancement logic
        raise NotImplementedError("BiasTestCase.enhance_base_attack not yet implemented")
