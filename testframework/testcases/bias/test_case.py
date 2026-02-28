#  Copyright (c) 2026.
#  Florian Emanuel Sauer

from __future__ import annotations

from typing import cast

from deepteam.metrics import BaseRedTeamingMetric  # type: ignore
from deepteam.test_case import RTTestCase
from deepteam.vulnerabilities import Bias  # type: ignore
from deepteam.vulnerabilities.bias import BiasType

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
        self.attack_builder = Bias(simulator_model=self.simulator_model, evaluation_model=self.evaluation_model)

    def _get_metric(self, attack: RTTestCase) -> BaseRedTeamingMetric:
        attack_type = cast(BiasType, attack.vulnerability_type)
        return cast(Bias, self.attack_builder)._get_metric(type=attack_type)  # pylint: disable=protected-access
