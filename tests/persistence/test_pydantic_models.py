#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

"""
Unit tests for Pydantic input models — validation happy/sad paths and to_entity().
These are pure unit tests: no DB or session needed.
"""

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from testframework.enums import ChatbotName, Severity
from testframework.persistence.entity.analysis import AnalysisRunEntity
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
from testframework.persistence.entity.enums import DetectionStage
from testframework.persistence.entity.test_case import TestCaseEntity
from testframework.persistence.entity.test_run import TestRunEntity
from testframework.persistence.model import (
    AnalysisRunInputModel,
    AttackInputModel,
    ChatbotResponseEvaluationInputModel,
    ChatbotResponseInputModel,
    DetectionElementInputModel,
    DetectionResultInputModel,
    ScannerDetailInputModel,
    TestCaseInputModel,
    TestRunInputModel,
)

_NOW = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
_UUID = uuid4()


# ---------------------------------------------------------------------------
# TestRunInputModel
# ---------------------------------------------------------------------------

class TestTestRunInputModel:
    def test_valid_minimal(self):
        m = TestRunInputModel(run_id=_UUID, start_ts=_NOW)
        assert m.run_id == _UUID
        assert m.end_ts is None

    def test_invalid_run_id_not_uuid(self):
        with pytest.raises(ValidationError):
            TestRunInputModel(run_id="not-a-uuid", start_ts=_NOW)

    def test_to_entity_produces_test_run_entity(self):
        m = TestRunInputModel(run_id=_UUID, start_ts=_NOW, end_ts=_NOW)
        e = m.to_entity()
        assert isinstance(e, TestRunEntity)
        assert e.run_id == str(_UUID)
        assert e.start_ts == _NOW
        assert e.end_ts == _NOW

    def test_to_entity_end_ts_none(self):
        m = TestRunInputModel(run_id=_UUID, start_ts=_NOW)
        e = m.to_entity()
        assert e.end_ts is None


# ---------------------------------------------------------------------------
# TestCaseInputModel
# ---------------------------------------------------------------------------

class TestTestCaseInputModel:
    def test_valid_minimal(self):
        m = TestCaseInputModel(category="ethics")
        assert m.subcategories == []
        assert m.model_attack_generation is None

    def test_invalid_empty_category(self):
        with pytest.raises(ValidationError):
            TestCaseInputModel(category="")

    def test_to_entity_produces_test_case_entity(self):
        m = TestCaseInputModel(
            category="ethics",
            model_attack_generation="gpt-4",
            subcategories=["A", "B"],
        )
        e = m.to_entity()
        assert isinstance(e, TestCaseEntity)
        assert e.category == "ethics"
        assert e.model_attack_generation == "gpt-4"
        assert e.subcategories == ["A", "B"]


# ---------------------------------------------------------------------------
# AttackInputModel
# ---------------------------------------------------------------------------

class TestAttackInputModel:
    def test_valid(self):
        m = AttackInputModel(
            category="privacy",
            severity=Severity.UNSAFE,
            prompt_baseline="base",
            prompt_enhanced="enh",
        )
        assert m.severity == Severity.UNSAFE
        assert m.techniques == []

    def test_severity_coerced_from_string(self):
        m = AttackInputModel(
            category="privacy",
            severity="unsafe",  # string → Severity enum
            prompt_baseline="base",
            prompt_enhanced="enh",
        )
        assert m.severity == Severity.UNSAFE

    def test_invalid_severity(self):
        with pytest.raises(ValidationError):
            AttackInputModel(
                category="privacy",
                severity="DANGER",
                prompt_baseline="base",
                prompt_enhanced="enh",
            )

    def test_invalid_empty_prompt(self):
        with pytest.raises(ValidationError):
            AttackInputModel(
                category="privacy",
                severity=Severity.UNSAFE,
                prompt_baseline="",
                prompt_enhanced="enh",
            )

    def test_to_entity(self):
        m = AttackInputModel(
            category="privacy",
            severity=Severity.UNSAFE,
            prompt_baseline="base",
            prompt_enhanced="enh",
            techniques=["T1"],
        )
        e = m.to_entity()
        assert isinstance(e, AttackEntity)
        assert e.severity == Severity.UNSAFE
        assert e.techniques == ["T1"]


# ---------------------------------------------------------------------------
# ScannerDetailInputModel
# ---------------------------------------------------------------------------

class TestScannerDetailInputModel:
    def test_valid(self):
        m = ScannerDetailInputModel(name="Scan1", score=0.5, reason="ok")
        assert m.sanitized_input == ""
        assert m.is_valid is None

    def test_score_out_of_range(self):
        with pytest.raises(ValidationError):
            ScannerDetailInputModel(name="Scan1", score=1.5, reason="ok")

    def test_score_negative(self):
        with pytest.raises(ValidationError):
            ScannerDetailInputModel(name="Scan1", score=-0.1, reason="ok")

    def test_empty_name_rejected(self):
        with pytest.raises(ValidationError):
            ScannerDetailInputModel(name="", score=0.5, reason="ok")

    def test_to_entity(self):
        m = ScannerDetailInputModel(name="Scan1", score=0.7, reason="reason", is_valid=True)
        e = m.to_entity()
        assert isinstance(e, ScannerDetailEntity)
        assert e.name == "Scan1"
        assert e.is_valid is True


# ---------------------------------------------------------------------------
# DetectionElementInputModel
# ---------------------------------------------------------------------------

class TestDetectionElementInputModel:
    def test_valid(self):
        m = DetectionElementInputModel(
            stage=DetectionStage.INPUT,
            success=True,
            score=0.0,
            judge_raw_response="raw",
        )
        assert m.scanner_details == []

    def test_stage_coerced_from_string(self):
        m = DetectionElementInputModel(
            stage="input",
            success=True,
            score=0.0,
            judge_raw_response="raw",
        )
        assert m.stage == DetectionStage.INPUT

    def test_invalid_stage(self):
        with pytest.raises(ValidationError):
            DetectionElementInputModel(
                stage="UNKNOWN_STAGE",
                success=True,
                score=0.0,
                judge_raw_response="raw",
            )

    def test_to_entity_with_scanner_details(self):
        sd = ScannerDetailInputModel(name="S1", score=0.9, reason="r")
        m = DetectionElementInputModel(
            stage=DetectionStage.OUTPUT,
            success=False,
            score=1.0,
            judge_raw_response="raw",
            detected_type="injection",
            scanner_details=[sd],
        )
        e = m.to_entity()
        assert isinstance(e, DetectionElementEntity)
        assert e.stage == DetectionStage.OUTPUT
        assert len(e.scanner_details) == 1
        assert isinstance(e.scanner_details[0], ScannerDetailEntity)


# ---------------------------------------------------------------------------
# DetectionResultInputModel
# ---------------------------------------------------------------------------

class TestDetectionResultInputModel:
    def _el(self, stage: DetectionStage) -> DetectionElementInputModel:
        return DetectionElementInputModel(
            stage=stage, success=True, score=0.0, judge_raw_response=""
        )

    def test_valid(self):
        m = DetectionResultInputModel(
            guardrail_name="llm_guard",
            chatbot_name=ChatbotName.DUMMY,
            input_detection=self._el(DetectionStage.INPUT),
            output_detection=self._el(DetectionStage.OUTPUT),
        )
        assert m.guardrail_name == "llm_guard"

    def test_chatbot_name_coerced_from_string(self):
        m = DetectionResultInputModel(
            guardrail_name="llm_guard",
            chatbot_name="DUMMY",
            input_detection=self._el(DetectionStage.INPUT),
            output_detection=self._el(DetectionStage.OUTPUT),
        )
        assert m.chatbot_name == ChatbotName.DUMMY

    def test_empty_guardrail_name_rejected(self):
        with pytest.raises(ValidationError):
            DetectionResultInputModel(
                guardrail_name="",
                chatbot_name=ChatbotName.DUMMY,
                input_detection=self._el(DetectionStage.INPUT),
                output_detection=self._el(DetectionStage.OUTPUT),
            )

    def test_to_entity_links_detection_elements(self):
        m = DetectionResultInputModel(
            guardrail_name="llm_guard",
            chatbot_name=ChatbotName.DUMMY,
            input_detection=self._el(DetectionStage.INPUT),
            output_detection=self._el(DetectionStage.OUTPUT),
        )
        e = m.to_entity()
        assert isinstance(e, DetectionResultEntity)
        assert e.guardrail_name == "llm_guard"
        assert len(e.detection_elements) == 2


# ---------------------------------------------------------------------------
# ChatbotResponseInputModel
# ---------------------------------------------------------------------------

class TestChatbotResponseInputModel:
    def test_valid_minimal(self):
        m = ChatbotResponseInputModel(
            prompt="p",
            raw_prompt="rp",
            response="r",
            system_prompt="sys",
            prompt_tokens=10,
            response_tokens=5,
            tool_called=False,
        )
        assert m.rag_nodes is None

    def test_negative_tokens_rejected(self):
        with pytest.raises(ValidationError):
            ChatbotResponseInputModel(
                prompt="p",
                raw_prompt="rp",
                response="r",
                system_prompt="sys",
                prompt_tokens=-1,
                response_tokens=5,
                tool_called=False,
            )

    def test_to_entity(self):
        m = ChatbotResponseInputModel(
            prompt="p",
            raw_prompt="rp",
            response="r",
            system_prompt="sys",
            prompt_tokens=10,
            response_tokens=5,
            tool_called=True,
            tool_name="my_tool",
        )
        e = m.to_entity()
        assert isinstance(e, ChatbotResponseEntity)
        assert e.tool_name == "my_tool"
        assert e.tool_called is True


# ---------------------------------------------------------------------------
# ChatbotResponseEvaluationInputModel
# ---------------------------------------------------------------------------

class TestChatbotResponseEvaluationInputModel:
    def _resp(self) -> ChatbotResponseInputModel:
        return ChatbotResponseInputModel(
            prompt="p", raw_prompt="rp", response="r",
            system_prompt="sys", prompt_tokens=1, response_tokens=1,
            tool_called=False,
        )

    def test_valid(self):
        m = ChatbotResponseEvaluationInputModel(
            chatbot_name=ChatbotName.DUMMY,
            score=0.8,
            reason="looks good",
            success=True,
            metric="MyMetric",
        )
        assert m.chatbot_response is None

    def test_score_out_of_range(self):
        with pytest.raises(ValidationError):
            ChatbotResponseEvaluationInputModel(
                chatbot_name=ChatbotName.DUMMY,
                score=1.5,
                reason="bad",
                success=True,
                metric="M",
            )

    def test_empty_metric_rejected(self):
        with pytest.raises(ValidationError):
            ChatbotResponseEvaluationInputModel(
                chatbot_name=ChatbotName.DUMMY,
                score=0.5,
                reason="ok",
                success=True,
                metric="",
            )

    def test_to_entity_with_response(self):
        m = ChatbotResponseEvaluationInputModel(
            chatbot_name=ChatbotName.DUMMY,
            score=0.5,
            reason="ok",
            success=True,
            metric="M",
            chatbot_response=self._resp(),
        )
        e = m.to_entity()
        assert isinstance(e, ChatbotResponseEvaluationEntity)
        assert e.chatbot_response is not None
        assert isinstance(e.chatbot_response, ChatbotResponseEntity)

    def test_to_entity_without_response(self):
        m = ChatbotResponseEvaluationInputModel(
            chatbot_name=ChatbotName.DUMMY,
            score=0.5,
            reason="ok",
            success=True,
            metric="M",
        )
        e = m.to_entity()
        assert e.chatbot_response is None


# ---------------------------------------------------------------------------
# AnalysisRunInputModel
# ---------------------------------------------------------------------------

class TestAnalysisRunInputModel:
    def test_valid(self):
        m = AnalysisRunInputModel(run_id=_UUID)
        assert m.exclude_scanners is False
        assert m.consider_chatbot_success is False

    def test_invalid_run_id(self):
        with pytest.raises(ValidationError):
            AnalysisRunInputModel(run_id="not-a-uuid")

    def test_to_entity(self):
        m = AnalysisRunInputModel(run_id=_UUID, exclude_scanners=True)
        e = m.to_entity()
        assert isinstance(e, AnalysisRunEntity)
        assert e.run_id == str(_UUID)
        assert e.exclude_scanners is True
        assert e.created_at is not None
