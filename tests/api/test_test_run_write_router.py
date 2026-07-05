#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

"""API tests for the write router (W1/W2) and R3 status — services are mocked."""

from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from testframework.api import app
from testframework.enums import RunStatus
from testframework.models import TestRunStatusResult

_NOW = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def client():
    return TestClient(app)


def test_start_run_returns_202_with_location_and_etag(client):
    with (
        patch("testframework.api.router.test_run_write_router.TestRunService") as mock_svc,
        patch("testframework.api.router.test_run_write_router.DefaultTest") as mock_test,
    ):
        mock_svc.return_value.has_active_run.return_value = False
        mock_svc.return_value.start_run.return_value = 1
        mock_test.return_value.run.return_value = None

        response = client.post("/api/v1/test-runs")

    assert response.status_code == 202
    assert response.headers["etag"] == '"1"'
    location = response.headers["location"]
    assert location.rsplit("/", 1)[0].endswith("/api/v1/test-runs")
    assert len(location.rsplit("/", 1)[1]) > 0  # a run_id was appended
    mock_svc.return_value.start_run.assert_called_once()
    mock_test.assert_called_once()


def test_start_run_accepts_empty_body(client):
    with (
        patch("testframework.api.router.test_run_write_router.TestRunService") as mock_svc,
        patch("testframework.api.router.test_run_write_router.DefaultTest") as mock_test,
    ):
        mock_svc.return_value.has_active_run.return_value = False
        mock_svc.return_value.start_run.return_value = 1
        mock_test.return_value.run.return_value = None

        response = client.post("/api/v1/test-runs")

    assert response.status_code == 202


def test_start_run_honors_results_dir_override(client):
    with (
        patch("testframework.api.router.test_run_write_router.TestRunService") as mock_svc,
        patch("testframework.api.router.test_run_write_router.DefaultTest") as mock_test,
    ):
        mock_svc.return_value.has_active_run.return_value = False
        mock_svc.return_value.start_run.return_value = 1
        mock_test.return_value.run.return_value = None

        response = client.post("/api/v1/test-runs", json={"results_dir": "_custom_runs"})

    assert response.status_code == 202
    _, kwargs = mock_test.call_args
    assert str(kwargs["results_dir"]) == "_custom_runs"


def test_start_run_409_when_already_active(client):
    with patch("testframework.api.router.test_run_write_router.TestRunService") as mock_svc:
        mock_svc.return_value.has_active_run.return_value = True
        response = client.post("/api/v1/test-runs")

    assert response.status_code == 409


def test_start_run_background_failure_marks_run_failed(client):
    """If DefaultTest.run() raises in the background job, the run is finalized as FAILED."""
    with (
        patch("testframework.api.router.test_run_write_router.TestRunService") as mock_svc,
        patch("testframework.api.router.test_run_write_router.DefaultTest") as mock_test,
    ):
        mock_svc.return_value.has_active_run.return_value = False
        mock_svc.return_value.start_run.return_value = 1
        mock_test.return_value.run.side_effect = RuntimeError("boom")

        response = client.post("/api/v1/test-runs")

    assert response.status_code == 202
    finalize_call = mock_svc.return_value.finalize_run.call_args
    assert finalize_call.kwargs["status"] == RunStatus.FAILED
    assert finalize_call.kwargs["status_error"] == "boom"


def test_delete_run_returns_204(client):
    with patch("testframework.api.dependencies.TestRunService") as mock_dep_svc, \
         patch("testframework.api.router.test_run_write_router.TestRunService") as mock_svc:
        mock_dep_svc.return_value.exists.return_value = True
        response = client.delete("/api/v1/test-runs/run-1")

    assert response.status_code == 204
    mock_svc.return_value.delete.assert_called_once_with("run-1")


def test_delete_run_404_when_missing(client):
    with patch("testframework.api.dependencies.TestRunService") as mock_dep_svc:
        mock_dep_svc.return_value.exists.return_value = False
        response = client.delete("/api/v1/test-runs/unknown")

    assert response.status_code == 404


def test_get_status_returns_status_dto(client):
    status_dto = TestRunStatusResult(
        run_id="run-1",
        status="running",
        status_error=None,
        start_ts=_NOW,
        end_ts=None,
        version=2,
    )
    with patch("testframework.api.router.test_run_read_router.TestRunService") as mock_svc:
        mock_svc.return_value.get_status.return_value = status_dto
        response = client.get("/api/v1/test-runs/run-1/status")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "running"
    assert body["version"] == 2


def test_get_status_404_when_missing(client):
    with patch("testframework.api.router.test_run_read_router.TestRunService") as mock_svc:
        mock_svc.return_value.get_status.return_value = None
        response = client.get("/api/v1/test-runs/unknown/status")

    assert response.status_code == 404
