#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.


from abc import ABC, abstractmethod
from typing import Protocol, Any

from testframework.redteam.test_case import RTTestCase


class RedTeamingMetric(Protocol):
    """Minimal metric interface used by the framework runtime."""

    score: float
    reason: str | None
    success: bool
    error: Any

    @property
    def __name__(self) -> str:
        """Return display name of the metric."""

    def measure(self, test_case: RTTestCase, *args, **kwargs) -> float:
        """Measure a red-team test case and set score/reason/success."""


class RedTeamingMetricBase(ABC):
    """Concrete base for framework metrics independent from DeepTeam."""

    score: float
    reason: str | None
    success: bool
    error: Any
    threshold: float
    evaluation_cost: Any
    verbose_logs: Any

    def __init__(self) -> None:
        self.score = 0.0
        self.reason = None
        self.success = False
        self.error = None
        self.threshold = 0.5
        self.evaluation_cost = None
        self.verbose_logs = None

    @abstractmethod
    def measure(self, test_case: RTTestCase, *args, **kwargs) -> float:
        """Measure a red-team test case and set score/reason/success."""
        raise NotImplementedError

    @abstractmethod
    def is_successful(self) -> bool:
        """Whether the metric succeeded."""
        raise NotImplementedError
