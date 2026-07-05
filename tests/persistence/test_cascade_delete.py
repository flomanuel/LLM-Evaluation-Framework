#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

"""Verify that deleting a test_run wipes the entire subtree, including analyses."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import func, select
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
from testframework.persistence.entity.analysis import SummaryErrorEntity, SummaryRowEntity
from testframework.persistence.entity.attack import AttackEntity
from testframework.persistence.entity.chatbot_response import (
    ChatbotResponseEntity,
    ChatbotResponseEvaluationEntity,
)
from testframework.persistence.entity.detection import (
    DetectionElementEntity,
    DetectionResultEntity,
    ScannerDetailEntity,
)
from testframework.persistence.entity.test_case import TestCaseEntity
from testframework.persistence.repository.analysis_repository import AnalysisRepository
from testframework.persistence.repository.test_run_repository import TestRunRepository
from testframework.persistence.service.analysis_service import AnalysisService
from testframework.persistence.service.test_run_service import TestRunService

_NOW = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def wire_session(db_engine):
    _session_module.engine = db_engine
    _session_module.Session = sessionmaker(db_engine, autoflush=False)


def _make_run() -> TestRunResult:
    return TestRunResult(
        run_id=str(uuid4()),
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
                                success=True,
                                metric="M",
                            )
                        },
                        protection={
                            "llm_guard": {
                                ChatbotName.DUMMY: DetectionResult(
                                    input_detection=DetectionElement(
                                        success=False,
                                        detected_type=None,
                                        score=1.0,
                                        judge_raw_response="",
                                        latency=0.0,
                                        scanner_details=[
                                            ScannerDetail(
                                                name="Scan1", score=0.0, reason="r",
                                                is_valid=False, sanitized_input="",
                                            )
                                        ],
                                    ),
                                    output_detection=DetectionElement(
                                        success=False,
                                        detected_type=None,
                                        score=1.0,
                                        judge_raw_response="",
                                        latency=0.0,
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


def test_delete_run_cascades_to_entire_subtree(db_session):
    """Deleting a run must remove every descendant row it owns — cases, attacks,
    evaluations, chatbot responses, detections, scanner details, and both analyses
    with their summary rows/errors.
    """
    run = _make_run()
    TestRunService().persist_full_run(run)
    AnalysisService().summarize_and_store(run.run_id, exclude_scanners=True, consider_chatbot_success=True)
    AnalysisService().summarize_and_store(run.run_id, exclude_scanners=True, consider_chatbot_success=False)

    run_entity = TestRunRepository(db_session).find_by_id(run.run_id)
    assert run_entity is not None

    test_case_ids = [tc.id for tc in run_entity.test_cases]
    attack_ids = [a.id for tc in run_entity.test_cases for a in tc.attacks]
    evaluation_ids = [
        e.id for tc in run_entity.test_cases for a in tc.attacks for e in a.evaluations
    ]
    chatbot_response_ids = [
        e.chatbot_response.id
        for tc in run_entity.test_cases
        for a in tc.attacks
        for e in a.evaluations
        if e.chatbot_response is not None
    ]
    detection_result_ids = [
        dr.id for tc in run_entity.test_cases for a in tc.attacks for dr in a.detection_results
    ]
    detection_element_ids = [
        de.id
        for tc in run_entity.test_cases
        for a in tc.attacks
        for dr in a.detection_results
        for de in dr.detection_elements
    ]
    scanner_detail_ids = [
        sd.id
        for tc in run_entity.test_cases
        for a in tc.attacks
        for dr in a.detection_results
        for de in dr.detection_elements
        for sd in de.scanner_details
    ]

    analyses = AnalysisRepository(db_session).find_by_run_id(run.run_id)
    analysis_ids = [an.id for an in analyses]
    summary_row_ids = [r.id for an in analyses for r in an.summary_rows]
    summary_error_ids = [e.id for an in analyses for e in an.summary_errors]

    # Sanity check: the aggregate is non-trivial before delete.
    assert test_case_ids and attack_ids and evaluation_ids and chatbot_response_ids
    assert detection_result_ids and detection_element_ids and scanner_detail_ids
    assert len(analysis_ids) == 2
    assert summary_row_ids

    TestRunService().delete(run.run_id)

    def _count(entity_cls, ids: list[int]) -> int:
        if not ids:
            return 0
        return db_session.scalar(
            select(func.count()).select_from(entity_cls).where(entity_cls.id.in_(ids))
        )

    assert _count(TestCaseEntity, test_case_ids) == 0
    assert _count(AttackEntity, attack_ids) == 0
    assert _count(ChatbotResponseEvaluationEntity, evaluation_ids) == 0
    assert _count(ChatbotResponseEntity, chatbot_response_ids) == 0
    assert _count(DetectionResultEntity, detection_result_ids) == 0
    assert _count(DetectionElementEntity, detection_element_ids) == 0
    assert _count(ScannerDetailEntity, scanner_detail_ids) == 0
    assert _count(SummaryRowEntity, summary_row_ids) == 0
    assert _count(SummaryErrorEntity, summary_error_ids) == 0
    assert AnalysisRepository(db_session).find_by_run_id(run.run_id) == []
    assert TestRunService().get_run(run.run_id) is None
