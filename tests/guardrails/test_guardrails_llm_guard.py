#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

import pytest

from testframework.guardrails.llm_guard.llm_guard import LLMGuard

_LLM_GUARD_MODULE = "testframework.guardrails.llm_guard.llm_guard"

_INPUT_SCANNER_NAMES = [
    "InputAnonymize",
    "InputBanCode",
    "InputBanTopics",
    "InputPromptInjection",
    "InputToxicity",
]

_OUTPUT_SCANNER_NAMES = [
    "OutputBanTopics",
    "OutputBias",
    "OutputBanCode",
    "FactualConsistency",
    "Sensitive",
    "OutputToxicity",
]


class _PassScanner:
    def __init__(self, **kwargs):
        pass

    def scan(self, *args, **kwargs):
        prompt = args[0] if args else ""
        return prompt, True, -1.0  # is_valid=True, risk_score=-1 → normalized=0


class _FailScanner:
    def __init__(self, **kwargs):
        pass

    def scan(self, *args, **kwargs):
        prompt = args[0] if args else ""
        return prompt, False, 1.0  # is_valid=False, risk_score=1 → normalized=1


def _patch_input_scanners(monkeypatch, scanner_cls):
    for name in _INPUT_SCANNER_NAMES:
        monkeypatch.setattr(f"{_LLM_GUARD_MODULE}.{name}", scanner_cls)
    monkeypatch.setattr(f"{_LLM_GUARD_MODULE}.Vault", lambda: None)


def _patch_output_scanners(monkeypatch, scanner_cls):
    for name in _OUTPUT_SCANNER_NAMES:
        monkeypatch.setattr(f"{_LLM_GUARD_MODULE}.{name}", scanner_cls)


# ---------------------------------------------------------------------------
# eval_attack
# ---------------------------------------------------------------------------

def test_eval_attack_success_when_all_scanners_pass(monkeypatch):
    _patch_input_scanners(monkeypatch, _PassScanner)
    result = LLMGuard().eval_attack("hello world")
    assert result.success is True


def test_eval_attack_failure_when_one_scanner_fails(monkeypatch):
    _patch_input_scanners(monkeypatch, _FailScanner)
    result = LLMGuard().eval_attack("malicious input")
    assert result.success is False


def test_eval_attack_scanner_details_populated(monkeypatch):
    _patch_input_scanners(monkeypatch, _PassScanner)
    result = LLMGuard().eval_attack("hello")
    assert len(result.scanner_details) > 0
    assert all(d.name for d in result.scanner_details)


def test_eval_attack_returns_error_on_exception(monkeypatch):
    def _broken(**kwargs):
        raise RuntimeError("scanner init failed")

    _patch_input_scanners(monkeypatch, _broken)
    with pytest.raises((RuntimeError, TypeError)):
        LLMGuard().eval_attack("hello")


# ---------------------------------------------------------------------------
# eval_model_response
# ---------------------------------------------------------------------------

def test_eval_model_response_success_when_all_pass(monkeypatch):
    _patch_output_scanners(monkeypatch, _PassScanner)
    result = LLMGuard().eval_model_response("Safe response.", chatbot=None)
    assert result.success is True


def test_eval_model_response_failure_when_flagged(monkeypatch):
    _patch_output_scanners(monkeypatch, _FailScanner)
    result = LLMGuard().eval_model_response("Harmful output.", chatbot=None)
    assert result.success is False
