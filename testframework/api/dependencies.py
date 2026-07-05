#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

from typing import Annotated

from fastapi import Depends

from testframework.api.errors import NotFoundError
from testframework.models import TestRunResult
from testframework.persistence.service.test_run_service import TestRunService

__all__ = ["ExistingRun", "ExistingRunId", "get_existing_run", "require_run_exists"]


def get_existing_run(run_id: str) -> TestRunResult:
    """Load a run or raise NotFoundError — for handlers that need the full aggregate."""
    run = TestRunService().get_run(run_id)
    if run is None:
        raise NotFoundError(run_id)
    return run


def require_run_exists(run_id: str) -> str:
    """Cheaply verify a run exists (no aggregate load) and return its run_id."""
    if not TestRunService().exists(run_id):
        raise NotFoundError(run_id)
    return run_id


ExistingRun = Annotated[TestRunResult, Depends(get_existing_run)]
ExistingRunId = Annotated[str, Depends(require_run_exists)]
