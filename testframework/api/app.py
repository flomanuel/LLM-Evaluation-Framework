#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

import os
from typing import Final

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from testframework.api.errors import register_exception_handlers
from testframework.api.router import health_router, test_run_read_router, test_run_write_router

API_PREFIX: Final = "/api/v1"


def _cors_allow_origins() -> list[str]:
    origins = os.environ.get("CORS_ALLOW_ORIGINS", "")
    return [origin.strip() for origin in origins.split(",") if origin.strip()]


def create_app() -> FastAPI:
    """Build the FastAPI application: routers, CORS, exception handlers."""
    app = FastAPI(title="LLM Test Framework API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_allow_origins(),
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["*"],
        expose_headers=["ETag", "Location", "Content-Disposition"],
    )

    app.include_router(health_router, prefix=f"{API_PREFIX}/health")
    app.include_router(test_run_read_router, prefix=f"{API_PREFIX}/test-runs")
    app.include_router(test_run_write_router, prefix=f"{API_PREFIX}/test-runs")

    register_exception_handlers(app)

    return app


app: Final = create_app()
