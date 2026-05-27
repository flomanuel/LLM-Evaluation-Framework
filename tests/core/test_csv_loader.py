#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

import csv
import pytest

from testframework.enums import Severity
from testframework.util.csv_loader import CSVAttackRow, CSVLoader


def _write_csv(tmp_path, rows: list[dict]) -> object:
    path = tmp_path / "attacks.csv"
    fieldnames = ["prompt", "severity", "category", "tool_check", "document", "technique"]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return path


# ---------------------------------------------------------------------------
# CSVAttackRow.from_csv_row
# ---------------------------------------------------------------------------

def test_from_csv_row_parses_fields_correctly():
    row = {"prompt": "hello", "severity": "unsafe", "category": "bias;ethics",
           "tool_check": "false", "document": None, "technique": ""}
    result = CSVAttackRow.from_csv_row(row)
    assert result.prompt == "hello"
    assert result.severity == "unsafe"
    assert result.categories == ["bias", "ethics"]
    assert result.tool_check is False
    assert result.document_path is None


def test_from_csv_row_splits_categories_on_semicolon():
    row = {"prompt": "p", "severity": "safe", "category": "a;b;c",
           "tool_check": "false", "document": None, "technique": ""}
    result = CSVAttackRow.from_csv_row(row)
    assert result.categories == ["a", "b", "c"]


def test_from_csv_row_handles_empty_category():
    row = {"prompt": "p", "severity": "safe", "category": "",
           "tool_check": "false", "document": None, "technique": ""}
    result = CSVAttackRow.from_csv_row(row)
    assert result.categories == []


def test_from_csv_row_raises_on_invalid_tool_check():
    row = {"prompt": "p", "severity": "safe", "category": "",
           "tool_check": "yes", "document": None, "technique": ""}
    with pytest.raises(ValueError):
        CSVAttackRow.from_csv_row(row)


def test_from_csv_row_tool_check_true():
    row = {"prompt": "p", "severity": "unsafe", "category": "",
           "tool_check": "true", "document": None, "technique": ""}
    result = CSVAttackRow.from_csv_row(row)
    assert result.tool_check is True


def test_from_csv_row_document_path_none_when_missing():
    row = {"prompt": "p", "severity": "safe", "category": "",
           "tool_check": "false", "technique": ""}
    result = CSVAttackRow.from_csv_row(row)
    assert result.document_path is None


# ---------------------------------------------------------------------------
# CSVAttackRow.matches_filters
# ---------------------------------------------------------------------------

def _row(severity="unsafe", categories=None) -> CSVAttackRow:
    return CSVAttackRow(
        prompt="p",
        severity=severity,
        categories=categories or ["bias"],
        tool_check=False,
        document_path=None,
    )


def test_matches_filters_wrong_severity():
    assert _row(severity="unsafe").matches_filters([], Severity.SAFE) is False


def test_matches_filters_empty_categories_matches_all():
    assert _row(severity="unsafe").matches_filters([], Severity.UNSAFE) is True


def test_matches_filters_matching_category():
    assert _row(categories=["bias"]).matches_filters(["bias"], Severity.UNSAFE) is True


def test_matches_filters_no_matching_category():
    assert _row(categories=["bias"]).matches_filters(["ethics"], Severity.UNSAFE) is False


# ---------------------------------------------------------------------------
# CSVAttackRow.build_attack_metadata
# ---------------------------------------------------------------------------

def test_build_attack_metadata_without_tool_check():
    row = CSVAttackRow(prompt="p", severity="unsafe", categories=[], tool_check=False,
                       document_path="/doc.pdf", technique="T1")
    metadata = row.build_attack_metadata(is_rag=True)
    assert metadata["file_path"] == "/doc.pdf"
    assert metadata["is_rag"] is True
    assert metadata["technique"] == "T1"
    assert "tool_check_mode" not in metadata


def test_build_attack_metadata_with_tool_check():
    row = CSVAttackRow(prompt="p", severity="unsafe", categories=[], tool_check=True,
                       document_path=None, technique="T2")
    metadata = row.build_attack_metadata()
    assert metadata["tool_check"] is True
    assert metadata["tool_check_mode"] == "prompt_injected_code"


def test_build_attack_metadata_keeps_csv_technique_for_pre_enhanced_doc_rows():
    row = CSVAttackRow(
        prompt="doc-embedded attack",
        severity="unsafe",
        categories=["indirect-prompt-injection"],
        tool_check=False,
        document_path="/attack.pdf",
        technique="Roleplay",
    )
    metadata = row.build_attack_metadata(is_rag=False)
    assert metadata["is_rag"] is False
    assert metadata["technique"] == "Roleplay"


# ---------------------------------------------------------------------------
# CSVLoader._build_full_path
# ---------------------------------------------------------------------------

def test_build_full_path_raises_for_non_csv_file(tmp_path, monkeypatch):
    monkeypatch.setattr(CSVLoader, "CSV_DOCUMENTS_FOLDER", tmp_path)
    with pytest.raises(ValueError, match="Only CSV"):
        CSVLoader._build_full_path("file.txt")


def test_build_full_path_raises_for_path_traversal(tmp_path, monkeypatch):
    monkeypatch.setattr(CSVLoader, "CSV_DOCUMENTS_FOLDER", tmp_path)
    with pytest.raises(ValueError, match="traversal"):
        CSVLoader._build_full_path("../outside.csv")


def test_build_full_path_raises_for_nonexistent_file(tmp_path, monkeypatch):
    monkeypatch.setattr(CSVLoader, "CSV_DOCUMENTS_FOLDER", tmp_path)
    with pytest.raises(FileNotFoundError):
        CSVLoader._build_full_path("missing.csv")


# ---------------------------------------------------------------------------
# CSVLoader.load_prompts_from_csv
# ---------------------------------------------------------------------------

def test_load_prompts_filters_by_severity(tmp_path, monkeypatch):
    monkeypatch.setattr(CSVLoader, "CSV_DOCUMENTS_FOLDER", tmp_path)
    _write_csv(tmp_path, [
        {"prompt": "unsafe prompt", "severity": "unsafe", "category": "bias",
         "tool_check": "false", "document": "", "technique": ""},
        {"prompt": "safe prompt", "severity": "safe", "category": "bias",
         "tool_check": "false", "document": "", "technique": ""},
    ])
    results = CSVLoader.load_prompts_from_csv("attacks.csv", severity=Severity.UNSAFE)
    assert len(results) == 1
    assert results[0].prompt == "unsafe prompt"


def test_load_prompts_filters_by_category(tmp_path, monkeypatch):
    monkeypatch.setattr(CSVLoader, "CSV_DOCUMENTS_FOLDER", tmp_path)
    _write_csv(tmp_path, [
        {"prompt": "bias row", "severity": "unsafe", "category": "bias",
         "tool_check": "false", "document": "", "technique": ""},
        {"prompt": "ethics row", "severity": "unsafe", "category": "ethics",
         "tool_check": "false", "document": "", "technique": ""},
    ])
    results = CSVLoader.load_prompts_from_csv("attacks.csv", categories=["bias"])
    assert len(results) == 1
    assert results[0].prompt == "bias row"


def test_load_prompts_returns_all_when_no_category_filter(tmp_path, monkeypatch):
    monkeypatch.setattr(CSVLoader, "CSV_DOCUMENTS_FOLDER", tmp_path)
    _write_csv(tmp_path, [
        {"prompt": "a", "severity": "unsafe", "category": "bias",
         "tool_check": "false", "document": "", "technique": ""},
        {"prompt": "b", "severity": "unsafe", "category": "ethics",
         "tool_check": "false", "document": "", "technique": ""},
    ])
    results = CSVLoader.load_prompts_from_csv("attacks.csv", categories=None)
    assert len(results) == 2
