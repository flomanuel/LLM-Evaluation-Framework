#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.



from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from uuid import uuid4
from loguru import logger
from testframework.models import TestRunResult, TestRunTimestamp, TestCaseResult
from testframework.storage import save_test_run, get_run_folder
from testframework.testcases.base import BaseTestCase


class Test(ABC):
    """Base class orchestrating a full test run."""

    def __init__(self, name: str, results_dir: Path | None = None) -> None:
        self.name = name
        self.results_dir = results_dir or Path("_runs")
        self.test_case_results: list[TestCaseResult] = []

    @abstractmethod
    def setup_chatbots(self) -> None:
        """Register chatbots in the ChatbotStore."""
        raise NotImplementedError

    @abstractmethod
    def get_test_cases(self) -> list[BaseTestCase]:
        """Return a list of BaseTestCase instances to execute."""
        raise NotImplementedError

    def run(self) -> TestRunResult:
        """Execute the test and return the results."""
        start = datetime.now(timezone.utc)
        run_id = str(uuid4())
        logger.info(
            "Starting test run '{}' (run_id={}, results_dir={})",
            self.name,
            run_id,
            self.results_dir,
        )

        run_folder = get_run_folder(run_id, start, self.results_dir)
        run_folder.mkdir(parents=True, exist_ok=True)
        logger.debug("Created run folder for run_id={}: {}", run_id, run_folder)

        self.setup_chatbots()
        logger.debug("Chatbot setup completed for run_id={}", run_id)
        self._execute_test_cases(run_folder)
        end = datetime.now(timezone.utc)
        tr = TestRunResult(
            run_id=run_id,
            timestamp=TestRunTimestamp(start=start, end=end),
            attack_categories=self.test_case_results,
        )
        self.store_test_run(tr)
        logger.info("Test run completed: {} (duration: {})", self.name, end - start)
        return tr

    def _execute_test_cases(self, run_folder: Path) -> None:
        """Execute all test cases and store results."""
        test_cases = self.get_test_cases()
        total_test_cases = len(test_cases)
        logger.info("Executing {} test case(s)", total_test_cases)
        for index, tc in enumerate(test_cases, start=1):
            tc_identifier = self._format_test_case_identifier(tc)
            logger.info(
                "=== Starting test case {}/{}: {} ===",
                index,
                total_test_cases,
                tc_identifier,
            )
            case_started = perf_counter()
            tc.run_folder = run_folder
            tc_results = tc.execute()
            self.test_case_results.append(tc_results)
            logger.opt(lazy=True).info(
                "Completed test case {}/{}: {} (attacks={}, duration={:.2f}s)",
                lambda current_index=index: current_index,
                lambda total=total_test_cases: total,
                lambda identifier=tc_identifier: identifier,
                lambda results=tc_results: len(results.attacks),
                lambda started=case_started: perf_counter() - started,
            )

    def store_test_run(self, test_run: TestRunResult) -> str:
        """Save the test run to a file."""
        path = save_test_run(test_run, base_dir=self.results_dir)
        logger.debug("Test run saved to: {}", path)
        return test_run.run_id

    @staticmethod
    def _format_test_case_identifier(test_case: BaseTestCase) -> str:
        """Format the test case identifier."""
        if not test_case.subcategories:
            return test_case.category.value

        subcategories = ";".join(str(subcat.value) for subcat in test_case.subcategories)
        return f"{test_case.category.value}_{subcategories}"
