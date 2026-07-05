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
from testframework.persistence.service.analysis_service import AnalysisService
from testframework.persistence.service.test_run_service import TestRunService
from testframework.testcases.base import BaseTestCase


class Test(ABC):
    """Base class orchestrating a full test run."""

    def __init__(
        self,
        name: str,
        results_dir: Path | None = None,
        run_id: str | None = None,
    ) -> None:
        self.name = name
        self.results_dir = results_dir or Path("_runs")
        self.test_case_results: list[TestCaseResult] = []
        self._run_service = TestRunService()
        self._run_id = run_id

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
        run_id = self._run_id or str(uuid4())
        logger.info(
            "Starting test run '{}' (run_id={}, results_dir={})",
            self.name,
            run_id,
            self.results_dir,
        )

        try:
            self._run_service.start_run(run_id, start)
            logger.debug("Persisted test_run row for run_id={}", run_id)
        except Exception as e:
            logger.warning("Could not persist run start (DB unavailable?): {}", e)

        self.setup_chatbots()
        logger.debug("Chatbot setup completed for run_id={}", run_id)
        self._execute_test_cases(run_id)
        end = datetime.now(timezone.utc)

        try:
            self._run_service.finalize_run(run_id, end)
            logger.debug("Finalized test_run row for run_id={}", run_id)
        except Exception as e:
            logger.warning("Could not finalize run (DB unavailable?): {}", e)

        for consider_chatbot_success in (True, False):
            try:
                AnalysisService().summarize_and_store(
                    run_id,
                    exclude_scanners=True,
                    consider_chatbot_success=consider_chatbot_success,
                )
                logger.debug(
                    "Persisted analysis for run_id={} (consider_chatbot_success={})",
                    run_id,
                    consider_chatbot_success,
                )
            except Exception as e:
                logger.warning(
                    "Could not persist analysis (run_id={}, consider_chatbot_success={}): {}",
                    run_id,
                    consider_chatbot_success,
                    e,
                )

        tr = TestRunResult(
            run_id=run_id,
            timestamp=TestRunTimestamp(start=start, end=end),
            attack_categories=self.test_case_results,
        )
        logger.info("Test run completed: {} (duration: {})", self.name, end - start)
        return tr

    def _execute_test_cases(self, run_id: str) -> None:
        """Execute all test cases and persist each result incrementally."""
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
            tc_results = tc.execute()
            self.test_case_results.append(tc_results)
            try:
                self._run_service.persist_test_case(run_id, tc_results)
                logger.debug("Persisted test case '{}' for run_id={}", tc_identifier, run_id)
            except Exception as e:
                logger.warning(
                    "Could not persist test case '{}' (DB unavailable?): {}",
                    tc_identifier,
                    e,
                )
            logger.opt(lazy=True).info(
                "Completed test case {}/{}: {} (attacks={}, duration={:.2f}s)",
                lambda current_index=index: current_index,
                lambda total=total_test_cases: total,
                lambda identifier=tc_identifier: identifier,
                lambda results=tc_results: len(results.attacks),
                lambda started=case_started: perf_counter() - started,
            )

    @staticmethod
    def _format_test_case_identifier(test_case: BaseTestCase) -> str:
        """Format the test case identifier."""
        if not test_case.subcategories:
            return test_case.category.value

        subcategories = ";".join(str(subcat.value) for subcat in test_case.subcategories)
        return f"{test_case.category.value}_{subcategories}"
