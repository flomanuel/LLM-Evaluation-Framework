#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

"""API tests for the read router (R1-R8) — services are mocked, no DB involved."""

import io
import zipfile
from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from testframework.api import app
from testframework.enums import Category
from testframework.models import (
    AnalysisRunResult,
    SummaryRow,
    TestCaseResult,
    TestRunResult,
    TestRunStatusResult,
    TestRunTimestamp,
)

_NOW = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def client():
    return TestClient(app)


def _make_run(run_id: str = "run-1", version: int = 3, n_cases: int = 1) -> TestRunResult:
    return TestRunResult(
        run_id=run_id,
        timestamp=TestRunTimestamp(start=_NOW, end=_NOW),
        attack_categories=[
            TestCaseResult(
                id=i,
                category=Category.ILLEGAL_ACTIVITY,
                subcategories=[],
                model=TestCaseResult.ModelInfo(attack_and_vulnerability_generation="gpt-4"),
                attacks={},
            )
            for i in range(n_cases)
        ],
        status="completed",
        version=version,
    )


def test_get_by_id_returns_run_with_etag(client):
    run = _make_run(version=3)
    with patch("testframework.api.dependencies.TestRunService") as mock_svc:
        mock_svc.return_value.get_run.return_value = run
        response = client.get("/api/v1/test-runs/run-1")

    assert response.status_code == 200
    assert response.headers["etag"] == '"3"'
    assert "version" not in response.json()
    assert response.json()["run_id"] == "run-1"


def test_get_by_id_304_when_if_none_match_matches(client):
    run = _make_run(version=3)
    with patch("testframework.api.dependencies.TestRunService") as mock_svc:
        mock_svc.return_value.get_run.return_value = run
        response = client.get("/api/v1/test-runs/run-1", headers={"if-none-match": '"3"'})

    assert response.status_code == 304


def test_get_by_id_404_when_missing(client):
    with patch("testframework.api.dependencies.TestRunService") as mock_svc:
        mock_svc.return_value.get_run.return_value = None
        response = client.get("/api/v1/test-runs/unknown")

    assert response.status_code == 404


def test_get_test_cases_paginated(client):
    run = _make_run(n_cases=3)
    with patch("testframework.api.dependencies.TestRunService") as mock_svc:
        mock_svc.return_value.get_run.return_value = run
        response = client.get("/api/v1/test-runs/run-1/test-cases?page=0&size=2")

    assert response.status_code == 200
    body = response.json()
    assert len(body["content"]) == 2
    assert body["page"] == {"size": 2, "number": 0, "total_elements": 3, "total_pages": 2}


def test_get_analyses_returns_list(client):
    analysis = AnalysisRunResult(
        id=1,
        run_id="run-1",
        exclude_scanners=True,
        consider_chatbot_success=True,
        created_at=_NOW,
        version=1,
    )
    with (
        patch("testframework.api.dependencies.TestRunService") as mock_run_svc,
        patch("testframework.api.router.test_run_read_router.AnalysisService") as mock_analysis_svc,
    ):
        mock_run_svc.return_value.exists.return_value = True
        mock_analysis_svc.return_value.find_by_run_id.return_value = [analysis]
        response = client.get("/api/v1/test-runs/run-1/analyses")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["version"] == 1
    assert body[0]["consider_chatbot_success"] is True


def test_get_analyses_404_when_run_missing(client):
    with patch("testframework.api.dependencies.TestRunService") as mock_run_svc:
        mock_run_svc.return_value.exists.return_value = False
        response = client.get("/api/v1/test-runs/unknown/analyses")

    assert response.status_code == 404


def _make_analysis(consider_chatbot_success: bool, exclude_scanners: bool = True) -> AnalysisRunResult:
    return AnalysisRunResult(
        id=1 if consider_chatbot_success else 2,
        run_id="run-1",
        exclude_scanners=exclude_scanners,
        consider_chatbot_success=consider_chatbot_success,
        created_at=_NOW,
        version=1,
        summary_rows=[
            SummaryRow(node="gpt-4/baseline", scope="overall", attack_category="", technique="",
                       count=10, tp=5, fp=1, tn=3, fn=1)
        ],
    )


def test_export_analyses_zip_contains_both_variants_by_default(client):
    analyses = [_make_analysis(True), _make_analysis(False)]
    with (
        patch("testframework.api.dependencies.TestRunService") as mock_run_svc,
        patch("testframework.api.router.test_run_read_router.AnalysisService") as mock_analysis_svc,
    ):
        mock_run_svc.return_value.exists.return_value = True
        mock_analysis_svc.return_value.find_by_run_id.return_value = analyses
        response = client.get("/api/v1/test-runs/run-1/analyses/export")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"
    assert response.headers["content-disposition"] == 'attachment; filename="analyses_run-1.zip"'
    with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
        assert set(zf.namelist()) == {
            "consider_model_alignment/gpt-4/summary.csv",
            "without_model_alignment/gpt-4/summary.csv",
        }


def test_export_analyses_filters_by_consider_chatbot_success(client):
    analyses = [_make_analysis(True), _make_analysis(False)]
    with (
        patch("testframework.api.dependencies.TestRunService") as mock_run_svc,
        patch("testframework.api.router.test_run_read_router.AnalysisService") as mock_analysis_svc,
    ):
        mock_run_svc.return_value.exists.return_value = True
        mock_analysis_svc.return_value.find_by_run_id.return_value = analyses
        response = client.get(
            "/api/v1/test-runs/run-1/analyses/export?consider_chatbot_success=true"
        )

    assert response.status_code == 200
    with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
        assert set(zf.namelist()) == {"consider_model_alignment/gpt-4/summary.csv"}


def test_export_analyses_404_when_exclude_scanners_false_has_no_data(client):
    analyses = [_make_analysis(True), _make_analysis(False)]
    with (
        patch("testframework.api.dependencies.TestRunService") as mock_run_svc,
        patch("testframework.api.router.test_run_read_router.AnalysisService") as mock_analysis_svc,
    ):
        mock_run_svc.return_value.exists.return_value = True
        mock_analysis_svc.return_value.find_by_run_id.return_value = analyses
        response = client.get(
            "/api/v1/test-runs/run-1/analyses/export?exclude_scanners=false"
        )

    assert response.status_code == 404


def test_export_analyses_404_when_run_missing(client):
    with patch("testframework.api.dependencies.TestRunService") as mock_run_svc:
        mock_run_svc.return_value.exists.return_value = False
        response = client.get("/api/v1/test-runs/unknown/analyses/export")

    assert response.status_code == 404


def test_get_test_case_by_id_returns_matching_case(client):
    run = _make_run(n_cases=3)
    with patch("testframework.api.dependencies.TestRunService") as mock_svc:
        mock_svc.return_value.get_run.return_value = run
        response = client.get("/api/v1/test-runs/run-1/test-cases/1")

    assert response.status_code == 200
    assert response.json()["id"] == 1


def test_get_test_case_by_id_404_when_id_not_in_run(client):
    run = _make_run(n_cases=2)
    with patch("testframework.api.dependencies.TestRunService") as mock_svc:
        mock_svc.return_value.get_run.return_value = run
        response = client.get("/api/v1/test-runs/run-1/test-cases/999")

    assert response.status_code == 404


def test_get_test_case_by_id_404_when_run_missing(client):
    with patch("testframework.api.dependencies.TestRunService") as mock_svc:
        mock_svc.return_value.get_run.return_value = None
        response = client.get("/api/v1/test-runs/unknown/test-cases/1")

    assert response.status_code == 404


def test_get_analysis_by_id_returns_analysis_with_etag(client):
    analysis = _make_analysis(True)
    with patch("testframework.api.router.test_run_read_router.AnalysisService") as mock_svc:
        mock_svc.return_value.find_by_id.return_value = analysis
        response = client.get("/api/v1/test-runs/run-1/analyses/1")

    assert response.status_code == 200
    assert response.headers["etag"] == '"1"'
    assert "version" not in response.json()


def test_get_analysis_by_id_304_when_if_none_match_matches(client):
    analysis = _make_analysis(True)
    with patch("testframework.api.router.test_run_read_router.AnalysisService") as mock_svc:
        mock_svc.return_value.find_by_id.return_value = analysis
        response = client.get(
            "/api/v1/test-runs/run-1/analyses/1", headers={"if-none-match": '"1"'}
        )

    assert response.status_code == 304


def test_get_analysis_by_id_404_when_missing(client):
    with patch("testframework.api.router.test_run_read_router.AnalysisService") as mock_svc:
        mock_svc.return_value.find_by_id.return_value = None
        response = client.get("/api/v1/test-runs/run-1/analyses/999")

    assert response.status_code == 404


def test_get_analysis_by_id_404_when_belongs_to_different_run(client):
    analysis = _make_analysis(True)  # run_id="run-1"
    with patch("testframework.api.router.test_run_read_router.AnalysisService") as mock_svc:
        mock_svc.return_value.find_by_id.return_value = analysis
        response = client.get("/api/v1/test-runs/other-run/analyses/1")

    assert response.status_code == 404


def test_export_route_is_not_shadowed_by_analysis_id_route(client):
    """Registration-order regression guard: "/analyses/export" must not be captured
    by the parameterized "/analyses/{analysis_id}" route.
    """
    analyses = [_make_analysis(True)]
    with (
        patch("testframework.api.dependencies.TestRunService") as mock_run_svc,
        patch("testframework.api.router.test_run_read_router.AnalysisService") as mock_analysis_svc,
    ):
        mock_run_svc.return_value.exists.return_value = True
        mock_analysis_svc.return_value.find_by_run_id.return_value = analyses
        response = client.get("/api/v1/test-runs/run-1/analyses/export")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"


def test_list_runs_paginated(client):
    runs = [
        TestRunStatusResult(
            run_id=f"run-{i}", status="completed", status_error=None,
            start_ts=_NOW, end_ts=_NOW, version=1,
        )
        for i in range(3)
    ]
    with patch("testframework.api.router.test_run_read_router.TestRunService") as mock_svc:
        mock_svc.return_value.list_runs.return_value = (runs[:2], 3)
        response = client.get("/api/v1/test-runs?page=0&size=2")

    assert response.status_code == 200
    body = response.json()
    assert len(body["content"]) == 2
    assert body["page"] == {"size": 2, "number": 0, "total_elements": 3, "total_pages": 2}
    _, kwargs = mock_svc.return_value.list_runs.call_args
    assert kwargs["offset"] == 0
    assert kwargs["limit"] == 2


def test_list_runs_passes_status_and_date_filters(client):
    with patch("testframework.api.router.test_run_read_router.TestRunService") as mock_svc:
        mock_svc.return_value.list_runs.return_value = ([], 0)
        response = client.get(
            "/api/v1/test-runs?status=completed&start_after=2026-01-01T00:00:00"
            "&start_before=2026-12-31T00:00:00"
        )

    assert response.status_code == 200
    _, kwargs = mock_svc.return_value.list_runs.call_args
    assert kwargs["run_status"] == "completed"
    assert kwargs["start_after"] == datetime(2026, 1, 1)
    assert kwargs["start_before"] == datetime(2026, 12, 31)


def test_list_runs_ignores_invalid_date_filter(client):
    with patch("testframework.api.router.test_run_read_router.TestRunService") as mock_svc:
        mock_svc.return_value.list_runs.return_value = ([], 0)
        response = client.get("/api/v1/test-runs?start_after=not-a-date")

    assert response.status_code == 200
    _, kwargs = mock_svc.return_value.list_runs.call_args
    assert kwargs["start_after"] is None
