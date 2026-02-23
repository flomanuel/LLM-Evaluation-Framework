from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Union

from loguru import logger

from .models import TestRunResult, TestCaseResult


def get_run_folder(run_id: str, timestamp: datetime, base_dir: Path | None = None) -> Path:
    """Get the folder path for a test run."""
    base = base_dir or Path("runs")
    ts = timestamp.strftime("%Y%m%d_%H%M%S")
    return base / f"{ts}_{run_id}"


def save_test_run(test_run: TestRunResult, base_dir: Path | None = None) -> Path:
    """Save a test run result to disk."""
    folder = get_run_folder(str(test_run.run_id), test_run.timestamp.start, base_dir)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "result.json"
    logger.debug(f"Saving test run to: {path}")
    with path.open("w", encoding="utf-8") as f:
        json.dump(test_run.to_json_dict(), f, default=str, indent=2)
    logger.info(f"Test run saved successfully: {path}")
    return path


def save_test_case_result(result: TestCaseResult, run_folder: Path) -> Path:
    """Save a single test case result as a backup to the run folder.

    Args:
        result: The TestCaseResult to save.
        run_folder: The folder path for the current test run.

    Returns:
        The path to the saved JSON file.
    """
    testcase_folder = run_folder / "testcase"
    testcase_folder.mkdir(parents=True, exist_ok=True)

    # Use the test case name as the filename
    filename = f"{result.name.value}.json"
    path = testcase_folder / filename

    logger.debug(f"Saving test case result to: {path}")
    with path.open("w", encoding="utf-8") as f:
        json.dump(asdict(result), f, default=str, indent=2)
    logger.info(f"Test case result saved successfully: {path}")
    return path
