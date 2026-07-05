#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

import json
from dataclasses import asdict
from datetime import datetime
from typing import Any, Final

from fastapi import APIRouter, Request, Response, status
from fastapi.responses import JSONResponse
from loguru import logger

from testframework.api.constants import ETAG, IF_NONE_MATCH
from testframework.api.dependencies import ExistingRun, ExistingRunId
from testframework.api.errors import NotFoundError
from testframework.api.page import Page, Pageable
from testframework.models import AnalysisRunResult, TestCaseResult, TestRunResult, TestRunStatusResult
from testframework.persistence.service.analysis_service import AnalysisService
from testframework.persistence.service.test_run_service import TestRunService
from testframework.reporting.analysis_csv import build_analyses_zip

__all__ = ["router"]

router: Final = APIRouter(tags=["Runs"])


def _to_dict(dto: Any) -> dict[str, Any]:
    """Serialize a DTO dataclass the same way storage.py does: asdict + default=str."""
    return json.loads(json.dumps(asdict(dto), default=str))


def _run_to_dict(run: TestRunResult) -> dict[str, Any]:
    run_dict = _to_dict(run)
    run_dict.pop("version", None)
    return run_dict


def _not_modified(request: Request, current_version: int | None) -> Response | None:
    """Return a 304 Response if If-None-Match matches current_version, else None.

    Shared by every strong-ETag GET (R2, R7) — same quote-strip + int-compare logic.
    """
    if_none_match: Final = request.headers.get(IF_NONE_MATCH)
    if (
        if_none_match is not None
        and len(if_none_match) >= 3  # noqa: PLR2004  -> '"<n>"'
        and if_none_match.startswith('"')
        and if_none_match.endswith('"')
    ):
        version = if_none_match[1:-1]
        try:
            if current_version is not None and int(version) == current_version:
                return Response(status_code=status.HTTP_304_NOT_MODIFIED)
        except ValueError:
            logger.debug("invalid version={}", version)
    return None


def _parse_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


@router.get("", response_model=Page)
def list_runs(request: Request) -> JSONResponse:
    """R1 — paginated, newest-first index of runs; filter by status and start date range."""
    query_params: Final = request.query_params
    pageable: Final = Pageable.create(number=query_params.get("page"), size=query_params.get("size"))

    runs, total = TestRunService().list_runs(
        run_status=query_params.get("status"),
        start_after=_parse_datetime(query_params.get("start_after")),
        start_before=_parse_datetime(query_params.get("start_before")),
        offset=pageable.number * pageable.size,
        limit=pageable.size,
    )
    page = Page.create(content=[_to_dict(r) for r in runs], pageable=pageable, total_elements=total)
    return JSONResponse(content=asdict(page))


@router.get("/{run_id}", response_model=TestRunResult)
def get_by_id(request: Request, run: ExistingRun) -> Response:
    """R2 — read a whole test run. Strong ETag from run.version; 304 on If-None-Match."""
    not_modified = _not_modified(request, run.version)
    if not_modified is not None:
        return not_modified

    return JSONResponse(
        content=_run_to_dict(run),
        headers={ETAG: f'"{run.version}"'},
    )


@router.get("/{run_id}/status", response_model=TestRunStatusResult)
def get_status(run_id: str) -> JSONResponse:
    """R3 — lightweight lifecycle status, used to poll a W1-started run."""
    status_dto = TestRunService().get_status(run_id)
    if status_dto is None:
        raise NotFoundError(run_id)
    return JSONResponse(content=_to_dict(status_dto))


@router.get("/{run_id}/test-cases", response_model=Page)
def get_test_cases(request: Request, run: ExistingRun) -> JSONResponse:
    """R4 — paginated test-case data of a run."""
    query_params: Final = request.query_params
    pageable: Final = Pageable.create(number=query_params.get("page"), size=query_params.get("size"))

    all_cases: Final = run.attack_categories
    start: Final = pageable.number * pageable.size
    end: Final = start + pageable.size
    page_content = [_to_dict(tc) for tc in all_cases[start:end]]

    page = Page.create(content=page_content, pageable=pageable, total_elements=len(all_cases))
    return JSONResponse(content=asdict(page))


@router.get("/{run_id}/test-cases/{test_case_id}", response_model=TestCaseResult)
def get_test_case_by_id(test_case_id: int, run: ExistingRun) -> JSONResponse:
    """R5 — a single test case of a run."""
    test_case = next((tc for tc in run.attack_categories if tc.id == test_case_id), None)
    if test_case is None:
        raise NotFoundError(run.run_id)
    return JSONResponse(content=_to_dict(test_case))


@router.get("/{run_id}/analyses", response_model=list[AnalysisRunResult])
def get_analyses(run_id: ExistingRunId) -> JSONResponse:
    """R6 — all stored analyses of a run, each with its own version for R7 lookups."""
    analyses = AnalysisService().find_by_run_id(run_id)
    return JSONResponse(content=[_to_dict(a) for a in analyses])


@router.get("/{run_id}/analyses/export")
def export_analyses(
    run_id: ExistingRunId,
    consider_chatbot_success: bool | None = None,
    exclude_scanners: bool = True,
) -> Response:
    """R8 — download the stored analyses as the historical per-model summary.csv files, zipped.

    Both variant folders are included unless ``consider_chatbot_success`` narrows it to one.
    ``exclude_scanners`` is accepted for completeness; only ``True`` has stored data (§7.1),
    so any other value yields no analyses and a 404.
    """
    analyses = [
        a
        for a in AnalysisService().find_by_run_id(run_id)
        if a.exclude_scanners == exclude_scanners
        and (consider_chatbot_success is None or a.consider_chatbot_success == consider_chatbot_success)
    ]
    if not analyses:
        raise NotFoundError(run_id)

    zip_bytes = build_analyses_zip(analyses)
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="analyses_{run_id}.zip"'},
    )


@router.get("/{run_id}/analyses/{analysis_id}", response_model=AnalysisRunResult)
def get_analysis_by_id(run_id: str, analysis_id: int, request: Request) -> Response:
    """R7 — a single analysis by id. Strong, stable ETag (analyses are never updated).

    Registered after the literal "/analyses/export" route so that path is matched first —
    Starlette tries routes in registration order and "export" would otherwise also satisfy
    the `{analysis_id}` placeholder.
    """
    analysis = AnalysisService().find_by_id(analysis_id)
    if analysis is None or analysis.run_id != run_id:
        raise NotFoundError(run_id)

    not_modified = _not_modified(request, analysis.version)
    if not_modified is not None:
        return not_modified

    analysis_dict = _to_dict(analysis)
    analysis_dict.pop("version", None)
    return JSONResponse(content=analysis_dict, headers={ETAG: f'"{analysis.version}"'})
