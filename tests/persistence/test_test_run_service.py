#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

"""Integration tests for TestRunService using the test Postgres container."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest

import testframework.persistence.session as _session_module
from sqlalchemy.orm import sessionmaker

from testframework.enums import Category, ChatbotName, Severity
from testframework.models import (
    Attack,
    ChatbotResponse,
    ChatbotResponseEvaluation,
    DetectionElement,
    DetectionResult,
    LLMErrorType,
    PromptVariants,
    RagContext,
    ScannerDetail,
    TestCaseResult,
    TestErrorInfo,
    TestRunResult,
    TestRunTimestamp,
    ToolInfo,
)
from testframework.persistence.service.test_run_service import TestRunService

_NOW = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def wire_session(db_engine):
    """Point the module-level Session at the test engine for each test."""
    _session_module.engine = db_engine
    _session_module.Session = sessionmaker(db_engine, autoflush=False)


def _make_minimal_run() -> TestRunResult:
    run_id = str(uuid4())
    return TestRunResult(
        run_id=run_id,
        timestamp=TestRunTimestamp(start=_NOW, end=_NOW),
        attack_categories=[
            TestCaseResult(
                category=Category.ILLEGAL_ACTIVITY,
                subcategories=[],
                model=TestCaseResult.ModelInfo(attack_and_vulnerability_generation="gpt-4"),
                attacks={
                    str(uuid4()): Attack(
                        category=Category.ILLEGAL_ACTIVITY.value,
                        subcategory=None,
                        techniques=["TechA"],
                        severity=Severity.UNSAFE,
                        prompt=PromptVariants(baseline="base", enhanced="enhanced"),
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
                                success=True,
                                metric="MyMetric",
                            )
                        },
                        protection={
                            "llm_guard": {
                                ChatbotName.DUMMY: DetectionResult(
                                    input_detection=DetectionElement(
                                        success=True,
                                        detected_type=None,
                                        score=0.9,
                                        judge_raw_response="raw",
                                        latency=0.1,
                                        scanner_details=[
                                            ScannerDetail(
                                                name="s",
                                                score=0.5,
                                                reason="r",
                                                is_valid=True,
                                                sanitized_input="",
                                            )
                                        ],
                                    ),
                                    output_detection=DetectionElement(
                                        success=True,
                                        detected_type=None,
                                        score=0.9,
                                        judge_raw_response="raw",
                                        latency=0.1,
                                        scanner_details=[],
                                    ),
                                )
                            }
                        },
                    )
                },
            )
        ],
    )


def test_persist_full_run_and_retrieve():
    svc = TestRunService()
    run = _make_minimal_run()

    svc.persist_full_run(run)

    fetched = svc.get_run(run.run_id)
    assert fetched is not None
    assert fetched.run_id == run.run_id
    assert len(fetched.attack_categories) == 1
    tc = fetched.attack_categories[0]
    assert tc.category == Category.ILLEGAL_ACTIVITY
    assert len(tc.attacks) == 1


def test_exists_returns_true_after_persist():
    svc = TestRunService()
    run = _make_minimal_run()
    svc.persist_full_run(run)
    assert svc.exists(run.run_id) is True


def test_exists_returns_false_for_unknown():
    svc = TestRunService()
    assert svc.exists(str(uuid4())) is False


def test_delete_removes_run():
    svc = TestRunService()
    run = _make_minimal_run()
    svc.persist_full_run(run)
    svc.delete(run.run_id)
    assert svc.exists(run.run_id) is False


def test_incremental_persist_start_case_finalize():
    svc = TestRunService()
    run = _make_minimal_run()
    run_id = run.run_id
    tc = run.attack_categories[0]

    svc.start_run(run_id, _NOW)
    assert svc.exists(run_id)

    svc.persist_test_case(run_id, tc)
    svc.finalize_run(run_id, _NOW)

    fetched = svc.get_run(run_id)
    assert fetched is not None
    assert fetched.timestamp.end == _NOW
    assert len(fetched.attack_categories) == 1
