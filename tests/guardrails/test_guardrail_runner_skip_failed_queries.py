from types import SimpleNamespace

from testframework import ChatbotName, LLMErrorType, TestErrorInfo
from testframework.guardrails.runner import GuardrailRunner
from testframework.models import (
    ChatbotResponse,
    ChatbotResponseEvaluation,
    DetectionElement,
    ToolInfo,
)


class _FakeGuardrail:
    def __init__(self) -> None:
        self.name = "fake_guardrail"
        self.attack_calls: list[tuple[str, dict]] = []
        self.response_calls: list[tuple[str, ChatbotName, dict]] = []

    def eval_attack(self, user_prompt: str, **kwargs) -> DetectionElement:
        self.attack_calls.append((user_prompt, kwargs))
        return DetectionElement(
            success=True,
            detected_type=None,
            score=0.0,
            judge_raw_response="ok",
            latency=0.01,
            scanner_details=[],
        )

    def eval_model_response(
            self,
            model_response: str,
            chatbot: ChatbotName,
            **kwargs,
    ) -> DetectionElement:
        self.response_calls.append((model_response, chatbot, kwargs))
        return DetectionElement(
            success=True,
            detected_type=None,
            score=0.0,
            judge_raw_response="ok",
            latency=0.01,
            scanner_details=[],
        )


def test_guardrail_runner_skips_failed_chatbot_queries():
    runner = GuardrailRunner()
    fake_guardrail = _FakeGuardrail()
    runner.guardrails = [fake_guardrail]

    failed_query_error = TestErrorInfo(
        error_type=LLMErrorType.TIMEOUT,
        message="Request timed out.",
    )
    failed_response = ChatbotResponse.from_error(
        error=failed_query_error,
        prompt="Attack prompt",
    )
    successful_response = ChatbotResponse(
        prompt="Attack prompt",
        raw_prompt="Attack prompt with context",
        response="Model answer",
        system_prompt="system",
        tool=ToolInfo(tool_called=False),
        prompt_tokens=10,
        response_tokens=4,
        rag_context=None,
        document_content=None,
    )

    chatbot_responses_eval = {
        ChatbotName.LANGCHAIN_GPT_5: ChatbotResponseEvaluation.from_error(failed_response),
        ChatbotName.OPENAI: ChatbotResponseEvaluation(
            chatbot_response=successful_response,
            score=0.0,
            reason="ok",
            success=True,
            metric="metric",
        ),
    }

    result = runner.run(
        attack=SimpleNamespace(input="Attack prompt"),
        chatbot_responses_eval=chatbot_responses_eval,
        metric=object(),
    )

    failed_detection = result["fake_guardrail"][ChatbotName.LANGCHAIN_GPT_5]
    assert failed_detection.input_detection.is_error is True
    assert failed_detection.output_detection.is_error is True
    assert failed_detection.input_detection.error is not None
    assert failed_detection.input_detection.error.error_type == LLMErrorType.TIMEOUT
    assert failed_detection.input_detection.error.message == (
        "Skipped guardrail evaluation because chatbot query failed: Request timed out."
    )

    successful_detection = result["fake_guardrail"][ChatbotName.OPENAI]
    assert successful_detection.input_detection.is_error is False
    assert successful_detection.output_detection.is_error is False

    assert fake_guardrail.attack_calls == [("Attack prompt with context", {"tool_info": None})]
    assert fake_guardrail.response_calls == [
        ("Model answer", ChatbotName.OPENAI, {"prompt": "Attack prompt with context", "tool_info": None})
    ]


# ---------------------------------------------------------------------------
# GuardrailRunner._skipped_detection_result
# ---------------------------------------------------------------------------

def test_skipped_detection_result_uses_existing_error():
    error = TestErrorInfo(error_type=LLMErrorType.TIMEOUT, message="timed out")
    failed_response = ChatbotResponse.from_error(error=error, prompt="Attack")
    evaluation = ChatbotResponseEvaluation.from_error(failed_response)

    result = GuardrailRunner._skipped_detection_result(evaluation)

    assert result.input_detection.is_error is True
    assert result.input_detection.error.error_type == LLMErrorType.TIMEOUT
    assert result.output_detection.is_error is True


def test_skipped_detection_result_creates_runtime_error_when_no_error_info():
    # Both evaluation.error and chatbot_response.error are None
    chatbot_response = ChatbotResponse(
        prompt="test",
        raw_prompt="test",
        response="",
        system_prompt="",
        tool=ToolInfo(tool_called=False),
        prompt_tokens=10,
        response_tokens=0,
        rag_context=None,
        document_content=None,
        error=None,
    )
    evaluation = ChatbotResponseEvaluation(
        chatbot_response=chatbot_response,
        score=0.0,
        reason="ok",
        success=True,
        metric="",
        error=None,
    )

    result = GuardrailRunner._skipped_detection_result(evaluation)

    assert result.input_detection.is_error is True
    assert result.input_detection.error is not None


# ---------------------------------------------------------------------------
# GuardrailRunner._safe_eval_attack / _safe_eval_response
# ---------------------------------------------------------------------------

class _FailingGuardrail(_FakeGuardrail):
    def eval_attack(self, user_prompt: str, **kwargs) -> DetectionElement:
        raise RuntimeError("boom")

    def eval_model_response(self, model_response: str, chatbot: ChatbotName, **kwargs) -> DetectionElement:
        raise RuntimeError("response boom")


def test_safe_eval_attack_returns_error_element_on_exception():
    runner = GuardrailRunner()
    runner.guardrails = []
    result = runner._safe_eval_attack(_FailingGuardrail(), "input")
    assert result.is_error is True


def test_safe_eval_response_returns_error_element_on_exception():
    runner = GuardrailRunner()
    result = runner._safe_eval_response(_FailingGuardrail(), "response", ChatbotName.OPENAI)
    assert result.is_error is True


# ---------------------------------------------------------------------------
# GuardrailRunner.run – PromptHardeningGuardrail uses attack.input
# ---------------------------------------------------------------------------

from testframework.guardrails.prompt_hardening import PromptHardeningGuardrail  # noqa: E402


class _TrackingPromptHardeningGuardrail(PromptHardeningGuardrail):
    """Records what text is passed to eval_model_response."""

    def __init__(self):
        super().__init__()
        self.response_eval_inputs: list[str] = []

    def eval_model_response(self, model_response: str, chatbot: ChatbotName, **kwargs) -> DetectionElement:
        self.response_eval_inputs.append(model_response)
        return DetectionElement(
            success=True,
            detected_type=None,
            score=0.0,
            judge_raw_response="ok",
            latency=0.01,
            scanner_details=[],
        )


def test_run_uses_attack_input_for_prompt_hardening_response_eval():
    runner = GuardrailRunner()
    tracking_ph = _TrackingPromptHardeningGuardrail()
    runner.guardrails = [tracking_ph]

    successful_response = ChatbotResponse(
        prompt="Attack prompt",
        raw_prompt="full prompt with context",
        response="Chatbot answer",
        system_prompt="system",
        tool=ToolInfo(tool_called=False),
        prompt_tokens=10,
        response_tokens=4,
        rag_context=None,
        document_content=None,
    )
    chatbot_responses_eval = {
        ChatbotName.OPENAI: ChatbotResponseEvaluation(
            chatbot_response=successful_response,
            score=0.0,
            reason="ok",
            success=True,
            metric="metric",
        )
    }

    runner.run(
        attack=SimpleNamespace(input="Attack prompt"),
        chatbot_responses_eval=chatbot_responses_eval,
        metric=object(),
    )

    # PromptHardeningGuardrail must receive attack.input, not the chatbot's response text
    assert tracking_ph.response_eval_inputs == ["Attack prompt"]
