from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Union

from loguru import logger

from .models import TestRunResult


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


def load_test_run(path_or_id: Union[Path, str], base_dir: Path | None = None) -> TestRunResult:
    """Load a test run result from disk."""
    path = Path(path_or_id)
    if path.is_dir():
        path = path / "result.json"
    if not path.exists():
        logger.error(f"Test run file not found: {path}")
        raise FileNotFoundError(path)
    logger.debug(f"Loading test run from: {path}")
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    # For now, return raw dict; structured re-hydration can be added later.
    # This keeps the implementation simple while satisfying the storage contract.
    logger.warning("Deserialization into TestRunResult is not implemented yet")
    raise NotImplementedError("Deserialization into TestRunResult is not implemented yet.")


