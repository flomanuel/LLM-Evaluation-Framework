#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

"""
Integration tests for AnalysisService.

The parity tests verify that the DB-backed AnalysisService produces identical
confusion-matrix numbers to the golden RunSummary.build_from_testcases() path.
"""

import json
from dataclasses import asdict
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy.orm import sessionmaker

import testframework.persistence.session as _session_module
from testframework.enums import Category, ChatbotName, Severity
from testframework.models import (
    Attack,
    ChatbotResponse,
    ChatbotResponseEvaluation,
    DetectionElement,
    DetectionResult,
    PromptVariants,
    ScannerDetail,
    TestCaseResult,
    TestRunResult,
    TestRunTimestamp,
    ToolInfo,
)
from testframework.persistence.service.analysis_service import AnalysisService
from testframework.persistence.service.test_run_service import TestRunService
from testframework.reporting.run_summary import RunSummary

_NOW = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def wire_session(db_engine):
    _session_module.engine = db_engine
    _session_module.Session = sessionmaker(db_engine, autoflush=False)


def _det(*, success: bool, scanner_details: list | None = None) -> DetectionElement:
    return DetectionElement(
        success=success,
        detected_type=None,
        score=0.0 if success else 1.0,
        judge_raw_response="",
        latency=0.0,
        scanner_details=scanner_details or [],
    )


def _make_run(attacks: dict) -> TestRunResult:
    """Build a minimal TestRunResult with the given attack dict keyed by str UUID."""
    return TestRunResult(
        run_id=str(uuid4()),
        timestamp=TestRunTimestamp(start=_NOW, end=_NOW),
        attack_categories=[
            TestCaseResult(
                category=Category.ILLEGAL_ACTIVITY,
                subcategories=[],
                model=TestCaseResult.ModelInfo(attack_and_vulnerability_generation="gpt-4"),
                attacks=attacks,
            )
        ],
    )


def _make_attack(*, severity: Severity, chatbot_success: bool, guard_success: bool) -> Attack:
    return Attack(
        category=Category.ILLEGAL_ACTIVITY.value,
        subcategory=None,
        techniques=["TechA"],
        severity=severity,
        prompt=PromptVariants(baseline="base", enhanced="enh"),
        llm_responses={
            ChatbotName.DUMMY: ChatbotResponseEvaluation(
                chatbot_response=ChatbotResponse(
                    prompt="p",
                    raw_prompt="rp",
                    response="r",
                    system_prompt="sys",
                    tool=ToolInfo(tool_called=False),
                    prompt_tokens=1,
                    response_tokens=1,
                    rag_context=None,
                    document_content=None,
                ),
                score=0.5,
                reason="ok",
                success=chatbot_success,
                metric="M",
            )
        },
        protection={
            "llm_guard": {
                ChatbotName.DUMMY: DetectionResult(
                    input_detection=_det(success=guard_success, scanner_details=[
                        ScannerDetail(name="Scan1", score=0.0, reason="r", is_valid=guard_success, sanitized_input="")
                    ]),
                    output_detection=_det(success=guard_success),
                )
            }
        },
    )


def _expected_summary(run: TestRunResult, exclude_scanners: bool = False, consider_chatbot_success: bool = False) -> dict:
    """Compute the golden summary using the direct RunSummary path."""
    run_dict = json.loads(json.dumps(asdict(run), default=str))
    return RunSummary._build_from_dict(run_dict, exclude_scanners=exclude_scanners, consider_chatbot_success=consider_chatbot_success)


def test_analysis_service_parity_unsafe_detected():
    """AnalysisService numbers match RunSummary for an unsafe attack that was correctly detected (TP)."""
    attack = _make_attack(severity=Severity.UNSAFE, chatbot_success=True, guard_success=False)
    run = _make_run({str(uuid4()): attack})
    TestRunService().persist_full_run(run)

    expected = _expected_summary(run)
    result = AnalysisService().summarize_and_store(run.run_id)
    assert result == expected


def test_analysis_service_parity_safe_not_flagged():
    """AnalysisService numbers match RunSummary for a safe prompt correctly not flagged."""
    attack = _make_attack(severity=Severity.SAFE, chatbot_success=True, guard_success=True)
    run = _make_run({str(uuid4()): attack})

    TestRunService().persist_full_run(run)

    expected = _expected_summary(run)
    result = AnalysisService().summarize_and_store(run.run_id)
    assert result == expected


def test_analysis_service_parity_mixed_attacks():
    """AnalysisService numbers match RunSummary for a mix of safe and unsafe attacks."""
    attacks = {
        str(uuid4()): _make_attack(severity=Severity.UNSAFE, chatbot_success=True, guard_success=False),
        str(uuid4()): _make_attack(severity=Severity.UNSAFE, chatbot_success=False, guard_success=True),
        str(uuid4()): _make_attack(severity=Severity.SAFE, chatbot_success=True, guard_success=True),
        str(uuid4()): _make_attack(severity=Severity.SAFE, chatbot_success=False, guard_success=False),
    }
    run = _make_run(attacks)
    TestRunService().persist_full_run(run)

    expected = _expected_summary(run)
    result = AnalysisService().summarize_and_store(run.run_id)
    assert result == expected


def test_analysis_service_unknown_run_raises():
    """summarize_and_store raises ValueError for a non-existent run_id."""
    with pytest.raises(ValueError, match="not found"):
        AnalysisService().summarize_and_store(str(uuid4()))
