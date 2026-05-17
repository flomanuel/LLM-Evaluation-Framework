import pytest

from testframework.guardrails.lakera_guard.lakera_guard import LakeraGuard


def _make_guard(monkeypatch) -> LakeraGuard:
    monkeypatch.setenv("LAKERA_GUARD_API_KEY", "fake-key")
    monkeypatch.setenv("LAKERA_GUARD_PROJECT_ID", "fake-project")
    return LakeraGuard()


# ---------------------------------------------------------------------------
# eval_attack
# ---------------------------------------------------------------------------

def test_eval_attack_success_when_no_threat_detected(monkeypatch):
    guard = _make_guard(monkeypatch)
    monkeypatch.setattr(guard, "_call_api", lambda messages: {"flagged": False, "breakdown": []})

    result = guard.eval_attack("hello")

    assert result.success is True
    assert result.is_error is False


def test_eval_attack_failure_when_threat_detected(monkeypatch):
    guard = _make_guard(monkeypatch)
    monkeypatch.setattr(guard, "_call_api", lambda messages: {
        "flagged": True,
        "breakdown": [{"detected": True, "detector_type": "prompt_injection", "detector_id": "pi"}],
    })

    result = guard.eval_attack("malicious prompt")

    assert result.success is False


def test_eval_attack_returns_error_on_exception(monkeypatch):
    guard = _make_guard(monkeypatch)

    def _raise(messages):
        raise RuntimeError("API failure")

    monkeypatch.setattr(guard, "_call_api", _raise)

    with pytest.raises(RuntimeError, match="API failure"):
        guard.eval_attack("hello")


# ---------------------------------------------------------------------------
# eval_model_response
# ---------------------------------------------------------------------------

def test_eval_model_response_success_when_clean(monkeypatch):
    guard = _make_guard(monkeypatch)
    monkeypatch.setattr(guard, "_call_api", lambda messages: {"flagged": False, "breakdown": []})

    result = guard.eval_model_response("Safe response.", chatbot=None)

    assert result.success is True
    assert result.is_error is False


def test_eval_model_response_failure_when_flagged(monkeypatch):
    guard = _make_guard(monkeypatch)
    monkeypatch.setattr(guard, "_call_api", lambda messages: {
        "flagged": True,
        "breakdown": [{"detected": True, "detector_type": "toxicity", "detector_id": "tox"}],
    })

    result = guard.eval_model_response("Harmful response.", chatbot=None)

    assert result.success is False


def test_eval_model_response_returns_error_on_exception(monkeypatch):
    guard = _make_guard(monkeypatch)

    def _raise(messages):
        raise RuntimeError("network failure")

    monkeypatch.setattr(guard, "_call_api", _raise)

    with pytest.raises(RuntimeError, match="network failure"):
        guard.eval_model_response("response", chatbot=None)
