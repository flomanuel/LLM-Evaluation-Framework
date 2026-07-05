#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

from fastapi import FastAPI, Request, Response, status

__all__ = ["NotFoundError", "RunAlreadyRunningError", "register_exception_handlers"]


class NotFoundError(Exception):
    """Raised when a requested test run (or a resource scoped to one) does not exist."""

    def __init__(self, run_id: str) -> None:
        super().__init__(f"TestRun not found: {run_id}")
        self.run_id = run_id


class RunAlreadyRunningError(Exception):
    """Raised when starting a run while another one is still pending/running."""

    def __init__(self) -> None:
        super().__init__("A test run is already pending or running")


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(NotFoundError)
    def _not_found_error_handler(_request: Request, _err: NotFoundError) -> Response:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    @app.exception_handler(RunAlreadyRunningError)
    def _run_already_running_error_handler(
        _request: Request, _err: RunAlreadyRunningError
    ) -> Response:
        return Response(status_code=status.HTTP_409_CONFLICT)
