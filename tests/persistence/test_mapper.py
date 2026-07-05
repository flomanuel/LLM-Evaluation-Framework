#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

"""Pure (no DB) round-trip tests for the DTO ↔ entity mapper."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest

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
from testframework.persistence.entity.analysis import AnalysisRunEntity, SummaryErrorEntity, SummaryRowEntity
from testframework.persistence.repository.mapper import (
    analysis_run_from_entity,
    attack_from_entity,
    attack_to_entity,
    case_result_from_entity,
    case_result_to_entity,
    chatbot_response_from_entity,
    chatbot_response_to_entity,
    detection_element_from_entity,
    detection_element_to_entity,
    detection_result_from_entity,
    detection_result_to_entities,
    evaluation_from_entity,
    evaluation_to_entity,
    run_result_from_entity,
    run_result_to_entity,
    run_status_from_entity,
    scanner_detail_from_entity,
    scanner_detail_to_entity,
)


_NOW = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


def _make_scanner_detail():
    return ScannerDetail(
        name="test_scanner",
        score=0.9,
        reason="detected",
        is_valid=False,
        sanitized_input="sanitized",
    )


def _make_detection_element(with_error=False):
    err = TestErrorInfo(error_type=LLMErrorType.TIMEOUT, message="timed out", timestamp=_NOW) if with_error else None
    return DetectionElement(
        success=True,
        detected_type=Category.ILLEGAL_ACTIVITY,
        score=0.8,
        judge_raw_response="raw",
        latency=0.5,
        scanner_details=[_make_scanner_detail()],
        error=err,
    )


def _make_chatbot_response(with_rag=True, with_tool=True, with_error=False):
    err = TestErrorInfo(error_type=LLMErrorType.UNKNOWN, message="fail", timestamp=_NOW) if with_error else None
    return ChatbotResponse(
        prompt="test prompt",
        raw_prompt="raw prompt",
        response="response",
        system_prompt="system",
        tool=ToolInfo(
            tool_called=with_tool,
            tool_name="my_tool" if with_tool else None,
            tool_args={"key": "val"} if with_tool else None,
        ),
        prompt_tokens=10,
        response_tokens=20,
        rag_context=RagContext(embedding_model="text-embedding", nodes=["node1"]) if with_rag else None,
        document_content=DocumentContext(document="doc text") if not with_rag else None,
        file_path="/some/path.pdf",
        error=err,
    )


def _make_evaluation():
    return ChatbotResponseEvaluation(
        chatbot_response=_make_chatbot_response(),
        score=0.7,
        reason="looks good",
        success=True,
        metric="MyMetric",
    )


def _make_detection_result():
    return DetectionResult(
        input_detection=_make_detection_element(),
        output_detection=_make_detection_element(),
    )


def _make_attack():
    return Attack(
        category=Category.ILLEGAL_ACTIVITY.value,
        subcategory=None,
        techniques=["TechA", "TechB"],
        severity=Severity.UNSAFE,
        prompt=PromptVariants(baseline="base", enhanced="enhanced"),
        llm_responses={ChatbotName.DUMMY: _make_evaluation()},
        protection={"llm_guard": {ChatbotName.DUMMY: _make_detection_result()}},
    )


def _make_test_case():
    return TestCaseResult(
        category=Category.ILLEGAL_ACTIVITY,
        subcategories=["sub1"],
        model=TestCaseResult.ModelInfo(attack_and_vulnerability_generation="gpt-4"),
        attacks={str(uuid4()): _make_attack()},
    )


def _make_test_run():
    run_id = str(uuid4())
    return TestRunResult(
        run_id=run_id,
        timestamp=TestRunTimestamp(start=_NOW, end=_NOW),
        attack_categories=[_make_test_case()],
    )


# ---------------------------------------------------------------------------
# ScannerDetail round-trip
# ---------------------------------------------------------------------------


def test_scanner_detail_roundtrip():
    orig = _make_scanner_detail()
    entity = scanner_detail_to_entity(orig)
    back = scanner_detail_from_entity(entity)
    assert back.name == orig.name
    assert back.score == orig.score
    assert back.reason == orig.reason
    assert back.is_valid == orig.is_valid
    assert back.sanitized_input == orig.sanitized_input


# ---------------------------------------------------------------------------
# DetectionElement round-trip
# ---------------------------------------------------------------------------


def test_detection_element_roundtrip_no_error():
    orig = _make_detection_element()
    entity = detection_element_to_entity(orig, "input")
    assert entity.stage == "input"
    back = detection_element_from_entity(entity)
    assert back.success == orig.success
    assert back.score == orig.score
    assert back.latency == orig.latency
    assert back.detected_type == orig.detected_type
    assert len(back.scanner_details) == len(orig.scanner_details)


def test_detection_element_roundtrip_with_error():
    orig = _make_detection_element(with_error=True)
    entity = detection_element_to_entity(orig, "output")
    back = detection_element_from_entity(entity)
    assert back.error is not None
    assert back.error.error_type == LLMErrorType.TIMEOUT


# ---------------------------------------------------------------------------
# ChatbotResponse round-trip
# ---------------------------------------------------------------------------


def test_chatbot_response_roundtrip_with_rag():
    orig = _make_chatbot_response(with_rag=True, with_tool=False)
    entity = chatbot_response_to_entity(orig)
    back = chatbot_response_from_entity(entity)
    assert back.prompt == orig.prompt
    assert back.rag_context is not None
    assert back.rag_context.nodes == orig.rag_context.nodes
    assert back.document_content is None


def test_chatbot_response_roundtrip_with_tool():
    orig = _make_chatbot_response(with_rag=False, with_tool=True)
    entity = chatbot_response_to_entity(orig)
    back = chatbot_response_from_entity(entity)
    assert back.tool.tool_called is True
    assert back.tool.tool_name == "my_tool"
    assert back.tool.tool_args == {"key": "val"}


def test_chatbot_response_roundtrip_with_error():
    orig = _make_chatbot_response(with_error=True)
    entity = chatbot_response_to_entity(orig)
    back = chatbot_response_from_entity(entity)
    assert back.error is not None
    assert back.error.error_type == LLMErrorType.UNKNOWN


# ---------------------------------------------------------------------------
# Evaluation round-trip
# ---------------------------------------------------------------------------


def test_evaluation_roundtrip():
    orig = _make_evaluation()
    entity = evaluation_to_entity(ChatbotName.DUMMY, orig)
    assert entity.chatbot_name == ChatbotName.DUMMY.value
    back = evaluation_from_entity(entity)
    assert back.score == orig.score
    assert back.reason == orig.reason
    assert back.success == orig.success
    assert back.metric == orig.metric


# ---------------------------------------------------------------------------
# DetectionResult round-trip
# ---------------------------------------------------------------------------


def test_detection_result_roundtrip():
    orig = _make_detection_result()
    entity = detection_result_to_entities("llm_guard", ChatbotName.DUMMY, orig)
    assert entity.guardrail_name == "llm_guard"
    assert entity.chatbot_name == ChatbotName.DUMMY.value
    assert len(entity.detection_elements) == 2

    resp_by_id: dict = {}
    _, _, back = detection_result_from_entity(entity, resp_by_id)
    assert back.input_detection.success == orig.input_detection.success
    assert back.output_detection.success == orig.output_detection.success


# ---------------------------------------------------------------------------
# Attack round-trip
# ---------------------------------------------------------------------------


def test_attack_roundtrip():
    orig = _make_attack()
    entity = attack_to_entity("key1", orig)
    _, back = attack_from_entity(entity)

    assert back.category == orig.category
    assert back.severity == orig.severity
    assert back.techniques == orig.techniques
    assert back.prompt.baseline == orig.prompt.baseline
    assert back.prompt.enhanced == orig.prompt.enhanced
    assert len(back.llm_responses) == len(orig.llm_responses)
    assert len(back.protection) == len(orig.protection)


def test_attack_with_error_roundtrip():
    err = TestErrorInfo(error_type=LLMErrorType.GENERATION_ERROR, message="gen failed", timestamp=_NOW)
    orig = Attack.from_generation_error(
        category=Category.ETHICS.value,
        subcategories=[],
        severity=Severity.UNSAFE,
        error=err,
    )
    entity = attack_to_entity("key2", orig)
    _, back = attack_from_entity(entity)
    assert back.error is not None
    assert back.error.error_type == LLMErrorType.GENERATION_ERROR


# ---------------------------------------------------------------------------
# TestCase round-trip
# ---------------------------------------------------------------------------


def test_case_result_roundtrip():
    orig = _make_test_case()
    entity = case_result_to_entity(orig, "some-run-id")
    assert entity.category == orig.category.value
    assert entity.subcategories == orig.subcategories
    assert entity.model_attack_generation == orig.model.attack_and_vulnerability_generation

    back = case_result_from_entity(entity)
    assert back.category == orig.category
    assert back.subcategories == orig.subcategories
    assert len(back.attacks) == len(orig.attacks)


# ---------------------------------------------------------------------------
# TestRun round-trip
# ---------------------------------------------------------------------------


def test_run_result_roundtrip():
    orig = _make_test_run()
    entity = run_result_to_entity(orig)
    assert entity.run_id == orig.run_id
    assert entity.start_ts == orig.timestamp.start
    assert entity.end_ts == orig.timestamp.end
    assert len(entity.test_cases) == len(orig.attack_categories)

    back = run_result_from_entity(entity)
    assert back.run_id == orig.run_id
    assert back.timestamp.start == orig.timestamp.start
    assert len(back.attack_categories) == len(orig.attack_categories)


def test_run_result_from_entity_carries_status_and_version():
    entity = run_result_to_entity(_make_test_run())
    entity.status = "completed"
    entity.status_error = None
    entity.version = 3

    back = run_result_from_entity(entity)
    assert back.status == "completed"
    assert back.status_error is None
    assert back.version == 3


def test_run_result_to_entity_defaults_to_completed_status():
    """A fully-assembled TestRunResult (importer, persist_full_run) represents a
    finished run, so it must not fall back to the entity's normal PENDING default.
    """
    entity = run_result_to_entity(_make_test_run())
    assert entity.status == "completed"
    assert entity.status_error is None


def test_run_status_from_entity_maps_lightweight_fields():
    entity = run_result_to_entity(_make_test_run())
    entity.status = "failed"
    entity.status_error = "boom"
    entity.version = 2

    status_dto = run_status_from_entity(entity)
    assert status_dto.run_id == entity.run_id
    assert status_dto.status == "failed"
    assert status_dto.status_error == "boom"
    assert status_dto.start_ts == entity.start_ts
    assert status_dto.end_ts == entity.end_ts
    assert status_dto.version == 2


def test_analysis_run_from_entity_maps_summary_rows_and_errors():
    entity = AnalysisRunEntity(
        run_id="run-1",
        exclude_scanners=True,
        consider_chatbot_success=False,
        created_at=_NOW,
    )
    entity.id = 42
    entity.summary_rows = [
        SummaryRowEntity(
            analysis_run_id=42,
            node="gpt-4/baseline",
            scope="overall",
            attack_category="",
            technique="",
            count=10,
            tp=5,
            fp=1,
            tn=3,
            fn=1,
        )
    ]
    entity.summary_errors = [
        SummaryErrorEntity(analysis_run_id=42, node="gpt-4", attack_category="ethics", count=2)
    ]

    dto = analysis_run_from_entity(entity)
    assert dto.id == 42
    assert dto.run_id == "run-1"
    assert dto.exclude_scanners is True
    assert dto.consider_chatbot_success is False
    assert dto.version == 1
    assert len(dto.summary_rows) == 1
    assert dto.summary_rows[0].node == "gpt-4/baseline"
    assert len(dto.summary_errors) == 1
    assert dto.summary_errors[0].attack_category == "ethics"


def test_prompt_hardening_detection_element_carries_chatbot_response():
    ph_de = PromptHardeningDetectionElement(
        success=False,
        detected_type=None,
        score=0.1,
        judge_raw_response="raw",
        latency=None,
        scanner_details=[],
        chatbot_response=_make_chatbot_response(with_rag=False, with_tool=False),
    )
    dr = DetectionResult(
        input_detection=_make_detection_element(),
        output_detection=ph_de,
    )
    entity = detection_result_to_entities("prompt_hardening", ChatbotName.DUMMY, dr)
    output_el = next(e for e in entity.detection_elements if e.stage == "output")
    assert output_el.chatbot_response_id is None

    input_el = next(e for e in entity.detection_elements if e.stage == "input")
    _, _, back = detection_result_from_entity(entity, {})
    assert isinstance(back.output_detection, PromptHardeningDetectionElement)
