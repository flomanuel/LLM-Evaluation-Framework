#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

from typing import Any, Final

from fastapi import APIRouter
from loguru import logger
from sqlalchemy import text

import testframework.persistence.session as _session_mod

__all__ = ["router"]

router: Final = APIRouter(tags=["Health"])


@router.get("/liveness")
def liveness() -> dict[str, Any]:
    """Liveness probe."""
    return {"status": "up"}


@router.get("/readiness")
def readiness() -> dict[str, Any]:
    """Readiness probe — checks connectivity to postgres_eval."""
    try:
        with _session_mod.engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        db_status = "up"
    except Exception as e:  # noqa: BLE001
        logger.warning("Readiness check failed: {}", e)
        db_status = "down"
    return {"db": db_status}
