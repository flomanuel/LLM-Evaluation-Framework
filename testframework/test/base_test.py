from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, List
from uuid import UUID, uuid4

from loguru import logger

from ..models import AttackCategoryResult, TestRunResult, TestRunTimestamp, TestCaseResult
from ..enums import Category
from ..chatbot.store import ChatbotStore


class Test(ABC):
    """Base class orchestrating a full test run."""

    def __init__(self, name: str, results_dir: Path | None = None) -> None:
        self.name = name
        self.results_dir = results_dir or Path("runs")
        self.test_case_results: Dict[str, TestCaseResult] = {}

    @abstractmethod
    def setup_chatbots(self) -> None:
        """Register chatbots in ChatbotStore."""
        raise NotImplementedError

    @abstractmethod
    def get_test_cases(self) -> List:
        """Return a list of BaseTestCase instances to execute."""
        raise NotImplementedError

    def run(self) -> TestRunResult:
        logger.info(f"Starting test run: {self.name}")
        start = datetime.utcnow()
        self.setup_chatbots()
        logger.debug("Chatbots configured")
        self.execute_test_cases()
        end = datetime.utcnow()

        attack_categories: Dict[Category, AttackCategoryResult] = {}
        for attack_id, tcr in self.test_case_results.items():
            cat = tcr.attack.metadata and tcr.attack.metadata.category_raw
            category_enum = tcr.attack.protection.prompt_hardening.gpt_41.input_detection.detected_type if (
                tcr.attack.protection.prompt_hardening
                and tcr.attack.protection.prompt_hardening.gpt_41
            ) else None
            # Fallback to AttackCategory from subcategory mapping if needed; simplified for now.
            if category_enum is None:
                category_enum = Category.BENIGN
            if category_enum not in attack_categories:
                attack_categories[category_enum] = AttackCategoryResult(
                    category_id=uuid4(),
                    name=category_enum,
                    attacks={},
                )
            attack_categories[category_enum].attacks[attack_id] = tcr.attack

        tr = TestRunResult(
            run_id=uuid4(),
            timestamp=TestRunTimestamp(start=start, end=end),
            attack_categories=list(attack_categories.values()),
        )
        self.store_test_run(tr)
        logger.info(f"Test run completed: {self.name} (duration: {end - start})")
        return tr

    def execute_test_cases(self) -> None:
        test_cases = self.get_test_cases()
        logger.info(f"Executing {len(test_cases)} test case(s)")
        for tc in test_cases:
            logger.debug(f"Running test case: {tc.name}")
            results = tc.execute()
            self.test_case_results.update(results)
            logger.debug(f"Test case completed: {tc.name} ({len(results)} result(s))")

    def store_test_run(self, test_run: TestRunResult) -> UUID:
        from ..storage import save_test_run

        path = save_test_run(test_run, base_dir=self.results_dir)
        logger.info(f"Test run saved to: {path}")
        return test_run.run_id


