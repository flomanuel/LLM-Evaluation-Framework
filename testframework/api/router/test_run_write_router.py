#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

from datetime import datetime, timezone
from pathlib import Path
from typing import Final
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Request, Response, status
from loguru import logger
from pydantic import BaseModel

from testframework.api.constants import ETAG
from testframework.api.dependencies import ExistingRunId
from testframework.api.errors import RunAlreadyRunningError
from testframework.enums import RunStatus
from testframework.persistence.service.test_run_service import TestRunService
from testframework.tests.default_test import DefaultTest

__all__ = ["router"]

router: Final = APIRouter(tags=["Runs"])


class StartRunModel(BaseModel):
    """Optional request body for W1 — override the default results directory."""

    results_dir: str | None = None


def _execute_run(run_id: str, results_dir: Path) -> None:
    """Background job: run the baseline suite and keep test_run.status in sync.

    On success, ``Test.run()`` itself finalizes the run as COMPLETED (base_test.py).
    On failure, we persist the FAILED status here since the exception otherwise
    only surfaces in the background-task log.
    """
    run_service = TestRunService()
    try:
        run_service.update_status(run_id, RunStatus.RUNNING)
        DefaultTest(results_dir=results_dir, run_id=run_id).run()
    except Exception as e:
        logger.error("Background test run failed (run_id={}): {}", run_id, e)
        try:
            run_service.finalize_run(
                run_id,
                datetime.now(timezone.utc),
                status=RunStatus.FAILED,
                status_error=str(e),
            )
        except Exception as inner:
            logger.error(
                "Could not persist failed status for run_id={}: {}", run_id, inner
            )


@router.post("", status_code=status.HTTP_202_ACCEPTED)
def start_run(
    request: Request,
    background_tasks: BackgroundTasks,
    body: StartRunModel | None = None,
) -> Response:
    """W1 — start a new baseline run asynchronously. 409 if one is already in flight."""
    run_service = TestRunService()
    if run_service.has_active_run():
        raise RunAlreadyRunningError()

    run_id = str(uuid4())
    results_dir = Path(body.results_dir) if body and body.results_dir else Path("_runs")
    version = run_service.start_run(run_id, datetime.now(timezone.utc))

    background_tasks.add_task(_execute_run, run_id, results_dir)

    return Response(
        status_code=status.HTTP_202_ACCEPTED,
        headers={
            "Location": f"{request.url}/{run_id}",
            ETAG: f'"{version}"',
        },
    )


@router.delete("/{run_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_run(run_id: ExistingRunId) -> Response:
    """W2 — delete a run and everything attached to it."""
    TestRunService().delete(run_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
