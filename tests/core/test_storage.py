#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

import json
from datetime import datetime, timezone

from testframework.enums import Category
from testframework.models import TestCaseResult, TestRunResult
from testframework.storage import get_run_folder, save_test_case_result, save_test_run


# ---------------------------------------------------------------------------
# get_run_folder
# ---------------------------------------------------------------------------

def test_get_run_folder_default_base():
    ts = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    folder = get_run_folder("abc", ts)
    assert str(folder).startswith("_runs/")


def test_get_run_folder_custom_base(tmp_path):
    ts = datetime(2025, 6, 15, 12, 30, 0, tzinfo=timezone.utc)
    folder = get_run_folder("my-run", ts, base_dir=tmp_path)
    assert str(folder).startswith(str(tmp_path))


def test_get_run_folder_path_contains_run_id(tmp_path):
    ts = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    folder = get_run_folder("my-unique-id", ts, base_dir=tmp_path)
    assert "my-unique-id" in folder.name


def test_get_run_folder_path_contains_formatted_timestamp(tmp_path):
    ts = datetime(2025, 3, 14, 9, 26, 53, tzinfo=timezone.utc)
    folder = get_run_folder("r", ts, base_dir=tmp_path)
    assert "20250314_092653" in folder.name


# ---------------------------------------------------------------------------
# save_test_run
# ---------------------------------------------------------------------------

def test_save_test_run_creates_result_json(tmp_path):
    run = TestRunResult.new_empty()
    path = save_test_run(run, base_dir=tmp_path)
    assert path.exists()
    assert path.name == "result.json"


def test_save_test_run_returns_path_to_result_json(tmp_path):
    run = TestRunResult.new_empty()
    path = save_test_run(run, base_dir=tmp_path)
    assert path.name == "result.json"


def test_save_test_run_result_is_valid_json(tmp_path):
    run = TestRunResult.new_empty()
    path = save_test_run(run, base_dir=tmp_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)


# ---------------------------------------------------------------------------
# save_test_case_result
# ---------------------------------------------------------------------------

def _minimal_test_case_result() -> TestCaseResult:
    return TestCaseResult(
        category=Category.BENIGN,
        subcategories=[],
    )


def test_save_test_case_result_creates_testcase_folder(tmp_path):
    run_folder = tmp_path / "run"
    result = _minimal_test_case_result()
    save_test_case_result(result, run_folder)
    assert (run_folder / "testcase").is_dir()


def test_save_test_case_result_filename_matches_identifier(tmp_path):
    run_folder = tmp_path / "run"
    result = _minimal_test_case_result()
    path = save_test_case_result(result, run_folder)
    assert path.stem == result.identifier


def test_save_test_case_result_is_valid_json(tmp_path):
    run_folder = tmp_path / "run"
    result = _minimal_test_case_result()
    path = save_test_case_result(result, run_folder)
    data = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
