#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

"""
Historical JSON importer.

Reads _runs/*/result.json files, deserializes them tolerantly (handling
legacy field names, enum-as-string values, and missing optional fields),
and persists them through the standard service pipeline so historical runs
get full DB coverage.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from loguru import logger

from testframework.enums import Category, ChatbotName, Severity
from testframework.models import (
    Attack,
    ChatbotResponse,
    ChatbotResponseEvaluation,
    DetectionElement,
    DetectionResult,
    DocumentContext,
    LLMErrorType,
    PromptHardeningDetectionElement,
    PromptVariants,
    RagContext,
    ScannerDetail,
    TestCaseResult,
    TestErrorInfo,
    TestRunResult,
    TestRunTimestamp,
    ToolInfo,
)
from testframework.persistence.service.analysis_service import AnalysisService
from testframework.persistence.service.test_run_service import TestRunService


@dataclass
class ImportStats:
    imported: int = 0
    skipped: int = 0
    failed: int = 0


def import_runs(
    runs_dir: Path | str = Path("_runs"),
    *,
    force: bool = False,
    reanalyze: bool = True,
) -> ImportStats:
    """
    Import all *runs_dir*/result.json files into the DB.

    Each run is imported idempotently: an existing run_id is skipped unless
    *force=True*, in which case the old record is deleted and re-imported.
    If *reanalyze* is True (default), an analysis_run is created for each
    imported run using the default parameter combination.
    """
    runs_dir = Path(runs_dir)
    stats = ImportStats()
    result_paths = sorted(runs_dir.glob("*/result.json"))

    if not result_paths:
        logger.warning("No result.json files found in {}", runs_dir)
        return stats

    logger.info("Importing {} run(s) from {}", len(result_paths), runs_dir)

    for path in result_paths:
        try:
            _import_single(path, force=force, reanalyze=reanalyze, stats=stats)
        except Exception as exc:
            logger.error("Failed to import {}: {}", path, exc)
            stats.failed += 1

    logger.info(
        "Import complete — imported={}, skipped={}, failed={}",
        stats.imported,
        stats.skipped,
        stats.failed,
    )
    return stats


def _import_single(path: Path, *, force: bool, reanalyze: bool, stats: ImportStats) -> None:
    with path.open("r", encoding="utf-8") as fh:
        raw = json.load(fh)

    run = deserialize_run(raw)
    svc = TestRunService()

    if svc.exists(run.run_id):
        if not force:
            logger.info("Skipping existing run_id={} ({})", run.run_id, path)
            stats.skipped += 1
            return
        logger.info("Force re-importing run_id={} ({})", run.run_id, path)
        svc.delete(run.run_id)

    svc.persist_full_run(run)
    logger.info("Imported run_id={}", run.run_id)

    if reanalyze:
        AnalysisService().summarize_and_store(run.run_id)
        logger.debug("Analysis persisted for run_id={}", run.run_id)

    stats.imported += 1


# ---------------------------------------------------------------------------
# Tolerant deserializer
# ---------------------------------------------------------------------------

def deserialize_run(data: dict[str, Any]) -> TestRunResult:
    """Deserialize a result.json dict into a TestRunResult DTO."""
    run_id = str(data["run_id"])
    ts = data.get("timestamp") or {}
    start_ts = _parse_dt(ts.get("start") or data.get("start_ts"))
    end_ts = _parse_dt(ts.get("end") or data.get("end_ts")) or start_ts

    attack_categories = [
        _deserialize_test_case(tc)
        for tc in (data.get("attack_categories") or [])
    ]

    return TestRunResult(
        run_id=run_id,
        timestamp=TestRunTimestamp(start=start_ts, end=end_ts),
        attack_categories=attack_categories,
    )


def _deserialize_test_case(tc: dict[str, Any]) -> TestCaseResult:
    category = _coerce_category(tc.get("category") or "ethics")
    subcategories = tc.get("subcategories") or []
    model_info_raw = tc.get("model") or {}
    model_info = TestCaseResult.ModelInfo(
        attack_and_vulnerability_generation=model_info_raw.get("attack_and_vulnerability_generation")
    )
    attacks = {
        k: _deserialize_attack(v)
        for k, v in (tc.get("attacks") or {}).items()
    }
    return TestCaseResult(
        category=category,
        subcategories=[str(s) for s in subcategories],
        model=model_info,
        attacks=attacks,
        generation_error=_deserialize_error(tc.get("generation_error")),
        enhancement_error=_deserialize_error(tc.get("enhancement_error")),
    )


def _deserialize_attack(a: dict[str, Any]) -> Attack:
    prompt_raw = a.get("prompt") or {}
    llm_responses = {
        _coerce_chatbot_name(k): _deserialize_evaluation(v)
        for k, v in (a.get("llm_responses") or {}).items()
    }
    protection = {
        guardrail: {
            _coerce_chatbot_name(k): _deserialize_detection_result(guardrail, v)
            for k, v in model_results.items()
        }
        for guardrail, model_results in (a.get("protection") or {}).items()
    }
    return Attack(
        category=str(a.get("category") or ""),
        subcategory=a.get("subcategory"),
        techniques=list(a.get("techniques") or []),
        severity=_coerce_severity(a.get("severity") or "safe"),
        prompt=PromptVariants(
            baseline=str(prompt_raw.get("baseline") or ""),
            enhanced=str(prompt_raw.get("enhanced") or ""),
        ),
        llm_responses=llm_responses,
        protection=protection,
        error=_deserialize_error(a.get("error")),
    )


def _deserialize_evaluation(ev: dict[str, Any]) -> ChatbotResponseEvaluation:
    return ChatbotResponseEvaluation(
        chatbot_response=_deserialize_chatbot_response(ev.get("chatbot_response") or {}),
        score=float(ev.get("score") or 0.0),
        reason=str(ev.get("reason") or ""),
        success=bool(ev.get("success")),
        metric=str(ev.get("metric") or ""),
        error=_deserialize_error(ev.get("error")),
    )


def _deserialize_chatbot_response(cr: dict[str, Any]) -> ChatbotResponse:
    tool_raw = cr.get("tool") or {}
    rag_raw = cr.get("rag_context")
    doc_raw = cr.get("document_content")
    return ChatbotResponse(
        prompt=str(cr.get("prompt") or ""),
        raw_prompt=str(cr.get("raw_prompt") or ""),
        response=str(cr.get("response") or ""),
        system_prompt=str(cr.get("system_prompt") or ""),
        tool=ToolInfo(
            tool_called=bool(tool_raw.get("tool_called")),
            tool_name=tool_raw.get("tool_name"),
            tool_args=tool_raw.get("tool_args"),
        ),
        prompt_tokens=int(cr.get("prompt_tokens") or 0),
        response_tokens=int(cr.get("response_tokens") or 0),
        rag_context=RagContext(
            embedding_model=rag_raw.get("embedding_model"),
            nodes=list(rag_raw.get("nodes") or []),
        ) if rag_raw else None,
        document_content=None if doc_raw is None else DocumentContext(document=str(doc_raw)),
        file_path=cr.get("file_path"),
        error=_deserialize_error(cr.get("error")),
    )


def _deserialize_detection_result(
    guardrail_name: str, dr: dict[str, Any]
) -> DetectionResult:
    input_det = _deserialize_detection_element(dr.get("input_detection") or {}, is_output=False)
    output_raw = dr.get("output_detection") or {}
    if guardrail_name == "prompt_hardening" and "chatbot_response" in output_raw:
        output_det = _deserialize_prompt_hardening_output(output_raw)
    else:
        output_det = _deserialize_detection_element(output_raw, is_output=True)
    return DetectionResult(input_detection=input_det, output_detection=output_det)


def _deserialize_detection_element(
    el: dict[str, Any], *, is_output: bool
) -> DetectionElement:
    return DetectionElement(
        success=bool(el.get("success")),
        detected_type=el.get("detected_type"),
        score=float(el.get("score") or 0.0),
        judge_raw_response=str(el.get("judge_raw_response") or ""),
        latency=float(el["latency"]) if el.get("latency") is not None else None,
        scanner_details=[_deserialize_scanner(s) for s in (el.get("scanner_details") or [])],
        error=_deserialize_error(el.get("error")),
    )


def _deserialize_prompt_hardening_output(el: dict[str, Any]) -> PromptHardeningDetectionElement:
    cr_raw = el.get("chatbot_response")
    return PromptHardeningDetectionElement(
        success=bool(el.get("success")),
        detected_type=el.get("detected_type"),
        score=float(el.get("score") or 0.0),
        judge_raw_response=str(el.get("judge_raw_response") or ""),
        latency=float(el["latency"]) if el.get("latency") is not None else None,
        scanner_details=[_deserialize_scanner(s) for s in (el.get("scanner_details") or [])],
        error=_deserialize_error(el.get("error")),
        chatbot_response=_deserialize_chatbot_response(cr_raw) if cr_raw else None,
    )


def _deserialize_scanner(s: dict[str, Any]) -> ScannerDetail:
    return ScannerDetail(
        name=str(s.get("name") or ""),
        score=float(s.get("score") or 0.0),
        reason=str(s.get("reason") or ""),
        is_valid=s.get("is_valid"),
        sanitized_input=str(s.get("sanitized_input") or ""),
    )


def _deserialize_error(err: dict[str, Any] | None) -> TestErrorInfo | None:
    if not err:
        return None
    raw_type = err.get("error_type") or err.get("type") or "UNKNOWN"
    # Handle "LLMErrorType.TIMEOUT" legacy format
    if "." in str(raw_type):
        raw_type = str(raw_type).rsplit(".", 1)[-1]
    try:
        error_type = LLMErrorType(raw_type)
    except ValueError:
        try:
            error_type = LLMErrorType[raw_type]
        except KeyError:
            error_type = LLMErrorType.UNKNOWN
    ts_raw = err.get("timestamp")
    return TestErrorInfo(
        error_type=error_type,
        message=str(err.get("message") or ""),
        timestamp=_parse_dt(ts_raw) or datetime.now(timezone.utc),
    )


# ---------------------------------------------------------------------------
# Enum coercion helpers
# ---------------------------------------------------------------------------

def _coerce_category(raw: str) -> Category:
    raw = str(raw)
    # Handle "Category.ILLEGAL_ACTIVITY" legacy format
    if "." in raw:
        raw = raw.rsplit(".", 1)[-1]
    try:
        return Category(raw)          # by value: "illegal-activity"
    except ValueError:
        pass
    try:
        return Category[raw.upper().replace("-", "_")]   # by name: "ILLEGAL_ACTIVITY"
    except KeyError:
        pass
    logger.warning("Unknown category '{}', falling back to ETHICS", raw)
    return Category.ETHICS


def _coerce_chatbot_name(raw: str) -> ChatbotName:
    raw = str(raw)
    if "." in raw:
        raw = raw.rsplit(".", 1)[-1]
    try:
        return ChatbotName(raw)
    except ValueError:
        try:
            return ChatbotName[raw]
        except KeyError:
            logger.warning("Unknown chatbot name '{}', using raw string as key", raw)
            # Dynamically extend enum is not possible; return a best-effort fallback
            # This keeps the importer from crashing on unknown chatbots
            raise ValueError(f"Unknown ChatbotName: {raw!r}")


def _coerce_severity(raw: str) -> Severity:
    raw = str(raw).lower()
    if "." in raw:
        raw = raw.rsplit(".", 1)[-1].lower()
    try:
        return Severity(raw)
    except ValueError:
        return Severity.SAFE


def _parse_dt(raw: str | None) -> datetime | None:
    if not raw:
        return None
    if isinstance(raw, datetime):
        return raw
    raw = str(raw)
    try:
        dt = datetime.fromisoformat(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        logger.warning("Could not parse datetime '{}', using now()", raw)
        return datetime.now(timezone.utc)
