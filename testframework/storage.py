#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.


from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from loguru import logger
from testframework.models import TestRunResult, TestCaseResult


def get_run_folder(run_id: str, timestamp: datetime, base_dir: Path | None = None) -> Path:
    """Get the folder path for a test run."""
    base = base_dir or Path("_runs")
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
    """Save a single test case result as a backup to the run folder."""
    testcase_folder = run_folder / "testcase"
    testcase_folder.mkdir(parents=True, exist_ok=True)

    filename = f"{result.identifier}.json"
    path = testcase_folder / filename

    logger.debug(f"Saving test case result to: {path}")
    with path.open("w", encoding="utf-8") as f:
        json.dump(asdict(result), f, default=str, indent=2)
    logger.info(f"Test case result saved successfully: {path}")
    return path
