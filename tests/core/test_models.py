#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

from types import SimpleNamespace

from testframework.enums import Category, Severity
from testframework.models import (
    Attack,
    AttackEnhancementResult,
    ChatbotResponse,
    ChatbotResponseEvaluation,
    DetectionElement,
    EnhancedAttack,
    LLMErrorType,
    PromptVariants,
    TestCaseResult,
    TestErrorInfo,
    TestRunResult,
    ToolInfo,
)


# ---------------------------------------------------------------------------
# ChatbotResponse
# ---------------------------------------------------------------------------

def _make_response(error=None) -> ChatbotResponse:
    return ChatbotResponse(
        prompt="p",
        raw_prompt="p",
        response="r",
        system_prompt="s",
        tool=ToolInfo(tool_called=False),
        prompt_tokens=1,
        response_tokens=1,
        rag_context=None,
        document_content=None,
        error=error,
    )


def test_chatbot_response_is_error_false_when_no_error():
    assert _make_response().is_error is False


def test_chatbot_response_is_error_true_when_error_set():
    error = TestErrorInfo(error_type=LLMErrorType.TIMEOUT, message="timed out")
    assert _make_response(error=error).is_error is True


def test_chatbot_response_from_error_creates_error_response():
    error = TestErrorInfo(error_type=LLMErrorType.TIMEOUT, message="timed out")
    response = ChatbotResponse.from_error(error)
    assert response.is_error is True
    assert response.prompt_tokens == -1
    assert response.response_tokens == -1
    assert response.tool.tool_called is False


def test_chatbot_response_from_error_preserves_prompt():
    error = TestErrorInfo(error_type=LLMErrorType.TIMEOUT, message="t")
    response = ChatbotResponse.from_error(error, prompt="hello")
    assert response.prompt == "hello"


# ---------------------------------------------------------------------------
# ChatbotResponseEvaluation
# ---------------------------------------------------------------------------

def _make_evaluation(response_error=None, eval_error=None) -> ChatbotResponseEvaluation:
    return ChatbotResponseEvaluation(
        chatbot_response=_make_response(error=response_error),
        score=1.0,
        reason="ok",
        success=True,
        metric="m",
        error=eval_error,
    )


def test_evaluation_is_error_false_when_no_error_and_response_ok():
    assert _make_evaluation().is_error is False


def test_evaluation_is_error_true_when_own_error():
    eval_error = TestErrorInfo(error_type=LLMErrorType.UNKNOWN, message="err")
    assert _make_evaluation(eval_error=eval_error).is_error is True


def test_evaluation_is_error_true_when_chatbot_response_has_error():
    resp_error = TestErrorInfo(error_type=LLMErrorType.CONNECTION_ERROR, message="conn")
    assert _make_evaluation(response_error=resp_error).is_error is True


def test_evaluation_from_error_sets_score_minus_one():
    response = _make_response()
    evaluation = ChatbotResponseEvaluation.from_error(response)
    assert evaluation.score == -1.0
    assert evaluation.success is False


def test_evaluation_from_error_uses_chatbot_error_when_no_eval_error():
    resp_error = TestErrorInfo(error_type=LLMErrorType.TIMEOUT, message="t")
    response = _make_response(error=resp_error)
    evaluation = ChatbotResponseEvaluation.from_error(response)
    assert evaluation.error is resp_error


# ---------------------------------------------------------------------------
# DetectionElement
# ---------------------------------------------------------------------------

def test_detection_element_is_error_false_when_no_error():
    element = DetectionElement(
        success=True,
        detected_type=None,
        score=0.5,
        judge_raw_response="ok",
        latency=0.1,
        scanner_details=[],
    )
    assert element.is_error is False


def test_detection_element_is_error_true_when_error_set():
    error = TestErrorInfo(error_type=LLMErrorType.UNKNOWN, message="e")
    element = DetectionElement(
        success=False,
        detected_type=None,
        score=0.0,
        judge_raw_response="",
        latency=None,
        scanner_details=[],
        error=error,
    )
    assert element.is_error is True


def test_detection_element_from_error_fields():
    error = TestErrorInfo(error_type=LLMErrorType.TIMEOUT, message="t")
    element = DetectionElement.from_error(error)
    assert element.success is False
    assert element.score == 0.0
    assert element.scanner_details == []
    assert element.latency is None
    assert element.detected_type is None


# ---------------------------------------------------------------------------
# EnhancedAttack
# ---------------------------------------------------------------------------

def test_enhanced_attack_is_error_false_without_error():
    attack = EnhancedAttack(
        attack_case=SimpleNamespace(input="x"),
        baseline_input="x",
        enhanced_input="x_enhanced",
    )
    assert attack.is_error is False


def test_enhanced_attack_is_error_true_with_error():
    error = TestErrorInfo(error_type=LLMErrorType.UNKNOWN, message="e")
    attack = EnhancedAttack(
        attack_case=SimpleNamespace(input="x"),
        baseline_input="x",
        enhanced_input="x",
        error=error,
    )
    assert attack.is_error is True


# ---------------------------------------------------------------------------
# AttackEnhancementResult
# ---------------------------------------------------------------------------

def _enhancement_result(failed=0, planned=0, threshold=100.0) -> AttackEnhancementResult:
    return AttackEnhancementResult(
        enhanced_attacks=[],
        planned_attack_count=planned,
        failed_attack_count=failed,
        error_threshold_percent=threshold,
    )


def test_invalid_percentage_zero_when_no_planned_attacks():
    assert _enhancement_result(planned=0).invalid_percentage == 0.0


def test_invalid_percentage_correct_calculation():
    assert _enhancement_result(failed=2, planned=4).invalid_percentage == 50.0


def test_threshold_exceeded_false_when_planned_is_zero():
    assert _enhancement_result(planned=0).threshold_exceeded is False


def test_threshold_exceeded_false_when_within_threshold():
    assert _enhancement_result(failed=1, planned=4, threshold=50.0).threshold_exceeded is False


def test_threshold_exceeded_true_when_strictly_above_threshold():
    assert _enhancement_result(failed=3, planned=4, threshold=50.0).threshold_exceeded is True


def test_threshold_exceeded_false_when_exactly_at_threshold():
    assert _enhancement_result(failed=2, planned=4, threshold=50.0).threshold_exceeded is False


# ---------------------------------------------------------------------------
# TestCaseResult
# ---------------------------------------------------------------------------

def _make_test_case_result(**kwargs) -> TestCaseResult:
    defaults = dict(
        category=Category.ETHICS,
        subcategories=[],
        attacks={},
        generation_error=None,
        enhancement_error=None,
    )
    defaults.update(kwargs)
    return TestCaseResult(**defaults)


def test_identifier_without_subcategories():
    result = _make_test_case_result(subcategories=[])
    assert result.identifier == "ethics"


def test_identifier_with_single_subcategory():
    result = _make_test_case_result(subcategories=["foo"])
    assert result.identifier == "ethics_foo"


def test_identifier_with_multiple_subcategories():
    result = _make_test_case_result(subcategories=["a", "b"])
    assert result.identifier == "ethics_a;b"


def test_has_errors_false_when_no_errors():
    assert _make_test_case_result().has_errors is False


def test_has_errors_true_with_generation_error():
    error = TestErrorInfo(error_type=LLMErrorType.TIMEOUT, message="t")
    assert _make_test_case_result(generation_error=error).has_errors is True


def test_has_errors_true_with_enhancement_error():
    error = TestErrorInfo(error_type=LLMErrorType.UNKNOWN, message="e")
    assert _make_test_case_result(enhancement_error=error).has_errors is True


def test_has_errors_true_with_attack_error():
    error = TestErrorInfo(error_type=LLMErrorType.TIMEOUT, message="t")
    attack = Attack.from_generation_error(
        category="ethics",
        subcategories=None,
        severity=Severity.UNSAFE,
        error=error,
    )
    result = _make_test_case_result(attacks={"a": attack})
    assert result.has_errors is True


def test_error_count_sums_all_sources():
    error = TestErrorInfo(error_type=LLMErrorType.TIMEOUT, message="t")
    attack1 = Attack.from_generation_error("ethics", None, Severity.UNSAFE, error)
    attack2 = Attack.from_generation_error("ethics", None, Severity.UNSAFE, error)
    result = _make_test_case_result(
        generation_error=error,
        enhancement_error=error,
        attacks={"a": attack1, "b": attack2},
    )
    assert result.error_count == 4


# ---------------------------------------------------------------------------
# TestRunResult
# ---------------------------------------------------------------------------

def test_new_empty_creates_valid_run_id():
    run = TestRunResult.new_empty()
    assert isinstance(run.run_id, str)
    assert len(run.run_id) > 0


def test_new_empty_has_empty_attack_categories():
    run = TestRunResult.new_empty()
    assert run.attack_categories == []


def test_to_json_dict_returns_dict():
    run = TestRunResult.new_empty()
    assert isinstance(run.to_json_dict(), dict)
