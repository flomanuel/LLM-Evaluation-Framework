#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.


from abc import ABC
from deepteam.metrics import BaseRedTeamingMetric


class BaseMetric(BaseRedTeamingMetric, ABC):
    """ Base class for all custom metrics."""

    def __init__(self, harm_category: str) -> None:
        super().__init__()
        self._g_eval = None
        self.harm_category = harm_category

    def _pull_results_from_geval(self) -> None:
        self.score = self._g_eval.score
        self.reason = self._g_eval.reason
        self.success = self._g_eval.success
        self.error = self._g_eval.error
        self.evaluation_cost = self._g_eval.evaluation_cost
        self.verbose_logs = self._g_eval.verbose_logs
