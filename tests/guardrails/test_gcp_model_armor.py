import pytest

from testframework import ChatbotName, LLMErrorType
from testframework.guardrails.gcp_model_armor.gcp_model_armor import GcpModelArmor
from google.cloud.modelarmor_v1 import FilterMatchState, InvocationResult


class _FailIfCalledClient:
    def sanitize_model_response(self, request):
        raise AssertionError(f"sanitize_model_response should not be called: {request}")


class _TestGcpModelArmor(GcpModelArmor):
    @property
    def _model_armor_client(self):
        return _FailIfCalledClient()


def test_eval_model_response_returns_local_error_for_empty_payload():
    guard = _TestGcpModelArmor()

    result = guard.eval_model_response("   ", ChatbotName.LANGCHAIN_GPT_5)

    assert result.is_error is True
    assert result.error is not None
    assert result.error.error_type == LLMErrorType.UNKNOWN
    assert "model response is empty" in result.error.message.lower()


# ---------------------------------------------------------------------------
# Helpers for mocking GCP responses
# ---------------------------------------------------------------------------

class _FakeClient:
    """Returns a fake sanitization response without a real GCP call."""

    def __init__(self, match_state=FilterMatchState.NO_MATCH_FOUND, raise_exc=None):
        self._match_state = match_state
        self._raise_exc = raise_exc

    def _response(self):
        from unittest.mock import MagicMock
        resp = MagicMock()
        resp.sanitization_result.filter_match_state = self._match_state
        resp.sanitization_result.filter_results.items.return_value = []
        resp.sanitization_result.invocation_result = InvocationResult.SUCCESS
        return resp

    def sanitize_user_prompt(self, request):
        if self._raise_exc:
            raise self._raise_exc
        return self._response()

    def sanitize_model_response(self, request):
        if self._raise_exc:
            raise self._raise_exc
        return self._response()


class _FakeArmor(GcpModelArmor):
    def __init__(self, client):
        super().__init__()
        self._fake_client = client

    @property
    def _model_armor_client(self):
        return self._fake_client


# ---------------------------------------------------------------------------
# eval_attack
# ---------------------------------------------------------------------------

def test_eval_attack_success_when_no_match(monkeypatch):
    monkeypatch.setattr(
        "testframework.guardrails.gcp_model_armor.gcp_model_armor.proto.Message.to_dict",
        lambda r: {},
    )
    guard = _FakeArmor(_FakeClient(match_state=FilterMatchState.NO_MATCH_FOUND))
    result = guard.eval_attack("hello")
    assert result.success is True


def test_eval_attack_failure_when_match_found(monkeypatch):
    monkeypatch.setattr(
        "testframework.guardrails.gcp_model_armor.gcp_model_armor.proto.Message.to_dict",
        lambda r: {},
    )
    guard = _FakeArmor(_FakeClient(match_state=FilterMatchState.MATCH_FOUND))
    result = guard.eval_attack("malicious prompt")
    assert result.success is False


def test_eval_attack_returns_error_on_exception():
    guard = _FakeArmor(_FakeClient(raise_exc=RuntimeError("GCP error")))
    with pytest.raises(RuntimeError, match="GCP error"):
        guard.eval_attack("hello")


# ---------------------------------------------------------------------------
# eval_model_response
# ---------------------------------------------------------------------------

def test_eval_model_response_success_when_clean(monkeypatch):
    monkeypatch.setattr(
        "testframework.guardrails.gcp_model_armor.gcp_model_armor.proto.Message.to_dict",
        lambda r: {},
    )
    guard = _FakeArmor(_FakeClient(match_state=FilterMatchState.NO_MATCH_FOUND))
    result = guard.eval_model_response("Safe response.", ChatbotName.LANGCHAIN_GPT_5)
    assert result.success is True


def test_eval_model_response_failure_when_flagged(monkeypatch):
    monkeypatch.setattr(
        "testframework.guardrails.gcp_model_armor.gcp_model_armor.proto.Message.to_dict",
        lambda r: {},
    )
    guard = _FakeArmor(_FakeClient(match_state=FilterMatchState.MATCH_FOUND))
    result = guard.eval_model_response("Harmful response.", ChatbotName.LANGCHAIN_GPT_5)
    assert result.success is False
