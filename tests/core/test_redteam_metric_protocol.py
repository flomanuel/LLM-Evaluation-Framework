#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

from testframework.redteam.metric_protocol import RedTeamingMetricBase
from testframework.redteam.test_case import RTTestCase


class _Metric(RedTeamingMetricBase):
    def measure(self, test_case: RTTestCase, *args, **kwargs) -> float:
        del test_case, args, kwargs
        self.score = 0.7
        self.success = True
        self.reason = "ok"
        return self.score

    def is_successful(self) -> bool:
        return self.score >= self.threshold


def test_redteam_metric_base_defaults():
    metric = _Metric()
    assert metric.score == 0.0
    assert metric.success is False
    assert metric.threshold == 0.5


def test_redteam_metric_base_measure_sets_values():
    metric = _Metric()
    score = metric.measure(RTTestCase(vulnerability="x", input="p"))
    assert score == 0.7
    assert metric.is_successful() is True
