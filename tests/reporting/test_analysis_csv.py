#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

"""Unit tests (no HTTP, no DB) for the analysis -> CSV/ZIP reconstruction builder."""

import csv
import io
import zipfile
from datetime import datetime, timezone

from testframework.models import AnalysisRunResult, SummaryRow
from testframework.reporting.analysis_csv import (
    build_analyses_zip,
    group_rows_by_model,
    sanitize_model_name,
    write_summary_csv,
)

_NOW = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


def _row(node: str, scope: str = "overall", attack_category: str = "", technique: str = "") -> SummaryRow:
    return SummaryRow(
        node=node, scope=scope, attack_category=attack_category, technique=technique,
        count=10, tp=5, fp=1, tn=3, fn=1,
    )


def test_sanitize_model_name_strips_and_replaces_slash():
    assert sanitize_model_name(" gpt-4/turbo ") == "gpt-4_turbo"


def test_group_rows_by_model_splits_node_on_first_slash():
    rows = [
        _row("gpt-4/baseline"),
        _row("gpt-4/prompt_hardening/extra", scope="attack_category", attack_category="ethics"),
        _row("gpt-3.5/baseline"),
    ]
    grouped = group_rows_by_model(rows)

    assert set(grouped.keys()) == {"gpt-4", "gpt-3.5"}
    assert len(grouped["gpt-4"]) == 2
    # only the FIRST '/' is split — the rest stays part of the node name
    assert grouped["gpt-4"][1]["node"] == "prompt_hardening/extra"
    assert grouped["gpt-4"][0]["node"] == "baseline"
    assert len(grouped["gpt-3.5"]) == 1


def test_write_summary_csv_matches_historical_fieldnames_and_order():
    rows = group_rows_by_model([_row("gpt-4/baseline")])["gpt-4"]
    csv_text = write_summary_csv(rows)

    reader = csv.reader(io.StringIO(csv_text))
    header = next(reader)
    assert header == ["node", "scope", "attack_category", "technique", "count", "tp", "fp", "tn", "fn"]
    data_row = next(reader)
    assert data_row == ["baseline", "overall", "", "", "10", "5", "1", "3", "1"]


def _make_analysis(consider_chatbot_success: bool, rows: list[SummaryRow]) -> AnalysisRunResult:
    return AnalysisRunResult(
        id=1,
        run_id="run-1",
        exclude_scanners=True,
        consider_chatbot_success=consider_chatbot_success,
        created_at=_NOW,
        version=1,
        summary_rows=rows,
    )


def test_build_analyses_zip_layout_has_one_folder_per_variant():
    analyses = [
        _make_analysis(True, [_row("gpt-4/baseline"), _row("gpt-3.5/baseline")]),
        _make_analysis(False, [_row("gpt-4/baseline")]),
    ]

    zip_bytes = build_analyses_zip(analyses)

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        names = set(zf.namelist())
        assert names == {
            "consider_model_alignment/gpt-4/summary.csv",
            "consider_model_alignment/gpt-3.5/summary.csv",
            "without_model_alignment/gpt-4/summary.csv",
        }
        content = zf.read("consider_model_alignment/gpt-4/summary.csv").decode("utf-8")
        assert content.startswith("node,scope,attack_category,technique,count,tp,fp,tn,fn")


def test_build_analyses_zip_csv_contains_all_scopes_for_a_model():
    rows = [
        _row("gpt-4/baseline", scope="overall"),
        _row("gpt-4/baseline", scope="attack_category", attack_category="ethics"),
        _row("gpt-4/baseline", scope="technique", attack_category="ethics", technique="Prefix"),
    ]
    analyses = [_make_analysis(True, rows)]

    zip_bytes = build_analyses_zip(analyses)

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        content = zf.read("consider_model_alignment/gpt-4/summary.csv").decode("utf-8")
        data_rows = list(csv.reader(io.StringIO(content)))[1:]
        assert len(data_rows) == 3
        assert {r[1] for r in data_rows} == {"overall", "attack_category", "technique"}
