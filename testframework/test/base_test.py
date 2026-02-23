from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import List
from uuid import uuid4

from loguru import logger

from testframework.models import TestRunResult, TestRunTimestamp, TestCaseResult
from testframework.storage import save_test_run


class Test(ABC):
    """Base class orchestrating a full test run."""

    def __init__(self, name: str, results_dir: Path | None = None) -> None:
        self.name = name
        self.results_dir = results_dir or Path("runs")
        self.test_case_results: List[TestCaseResult] = []

    @abstractmethod
    def setup_chatbots(self) -> None:
        """Register chatbots in the ChatbotStore."""
        raise NotImplementedError

    @abstractmethod
    def get_test_cases(self) -> List:
        """Return a list of BaseTestCase instances to execute."""
        raise NotImplementedError

    def run(self) -> TestRunResult:
        logger.info(f"Starting test run: {self.name}")
        start = datetime.now(timezone.utc)
        self.setup_chatbots()
        logger.debug("Chatbots configured")
        self._execute_test_cases()
        end = datetime.now(timezone.utc)
        tr = TestRunResult(
            run_id=str(uuid4()),
            timestamp=TestRunTimestamp(start=start, end=end),
            attack_categories=self.test_case_results,
        )
        self.store_test_run(tr)
        logger.info(f"Test run completed: {self.name} (duration: {end - start})")
        return tr

    def _execute_test_cases(self) -> None:
        test_cases = self.get_test_cases()
        logger.info(f"Executing {len(test_cases)} test case(s)")
        for tc in test_cases:
            logger.debug(f"Running test case: {tc.name}")
            tc_results = tc.execute()
            self.test_case_results.append(tc_results)
            logger.debug(f"Test case completed: {tc.name} with ({len(tc_results.attacks)} result(s))")

    def store_test_run(self, test_run: TestRunResult) -> str:
        path = save_test_run(test_run, base_dir=self.results_dir)
        logger.info(f"Test run saved to: {path}")
        return test_run.run_id

    def _calculate_stats(self) -> dict[str, float]:
        # Placeholder for stats calculation logic, e.g., success rates or F1
        # todo: implement
        pass

    def resume(self, test_run_id: str):
        # Placeholder for resuming a test run from a saved state
        # todo: implement
        pass
