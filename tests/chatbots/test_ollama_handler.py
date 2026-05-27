#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

import types

from testframework.util.ollama_handler import OllamaGenerator

_MODULE = "testframework.util.ollama_handler"


# ---------------------------------------------------------------------------
# _get_timeout
# ---------------------------------------------------------------------------

def test_get_timeout_returns_default_when_env_not_set(monkeypatch):
    monkeypatch.delenv("DEEPEVAL_PER_ATTEMPT_TIMEOUT_SECONDS_OVERRIDE", raising=False)
    assert OllamaGenerator._get_timeout() == 240.0


def test_get_timeout_reads_from_env(monkeypatch):
    monkeypatch.setenv("DEEPEVAL_PER_ATTEMPT_TIMEOUT_SECONDS_OVERRIDE", "60")
    assert OllamaGenerator._get_timeout() == 60.0


def test_get_timeout_returns_default_on_invalid_value(monkeypatch):
    monkeypatch.setenv("DEEPEVAL_PER_ATTEMPT_TIMEOUT_SECONDS_OVERRIDE", "abc")
    assert OllamaGenerator._get_timeout() == 240.0


def test_get_timeout_returns_default_on_non_positive_value(monkeypatch):
    monkeypatch.setenv("DEEPEVAL_PER_ATTEMPT_TIMEOUT_SECONDS_OVERRIDE", "-5")
    assert OllamaGenerator._get_timeout() == 240.0


# ---------------------------------------------------------------------------
# _list_running_models
# ---------------------------------------------------------------------------

def _fake_run_result(stdout: str):
    return types.SimpleNamespace(stdout=stdout, returncode=0)


def test_list_running_models_returns_empty_on_header_only(monkeypatch):
    monkeypatch.setattr(f"{_MODULE}.subprocess.run", lambda *a, **kw: _fake_run_result("NAME"))
    assert OllamaGenerator._list_running_models() == []


def test_list_running_models_parses_model_names(monkeypatch):
    output = "NAME\ngemma3:latest some info\nllama3:8b other info"
    monkeypatch.setattr(f"{_MODULE}.subprocess.run", lambda *a, **kw: _fake_run_result(output))
    result = OllamaGenerator._list_running_models()
    assert result == ["gemma3:latest", "llama3:8b"]


# ---------------------------------------------------------------------------
# start_model_by_name_if_not_running
# ---------------------------------------------------------------------------

def test_start_model_does_nothing_when_no_model_id(monkeypatch):
    calls: list = []
    monkeypatch.setattr(f"{_MODULE}.subprocess.Popen", lambda args, **kw: calls.append(args))
    monkeypatch.setattr("time.sleep", lambda s: None)
    OllamaGenerator.start_model_by_name_if_not_running(False)
    assert calls == []


def test_start_model_does_nothing_when_already_running(monkeypatch):
    calls: list = []
    monkeypatch.setattr(f"{_MODULE}.subprocess.Popen", lambda args, **kw: calls.append(args))
    monkeypatch.setattr("time.sleep", lambda s: None)
    monkeypatch.setattr(OllamaGenerator, "_is_model_running", staticmethod(lambda model_id: True))
    OllamaGenerator.start_model_by_name_if_not_running("gemma3:4b")
    assert calls == []


def test_start_model_calls_ollama_run_when_not_running(monkeypatch):
    calls: list = []
    monkeypatch.setattr(f"{_MODULE}.subprocess.Popen", lambda args, **kw: calls.append(args))
    monkeypatch.setattr("time.sleep", lambda s: None)
    monkeypatch.setattr(OllamaGenerator, "_is_model_running", staticmethod(lambda model_id: False))
    OllamaGenerator.start_model_by_name_if_not_running("gemma3:4b")
    assert any("ollama" in args and "run" in args for args in calls)


# ---------------------------------------------------------------------------
# stop_model_by_name
# ---------------------------------------------------------------------------

def test_stop_model_does_nothing_when_no_model_id(monkeypatch):
    calls: list = []
    monkeypatch.setattr(f"{_MODULE}.subprocess.run", lambda args, **kw: calls.append(args))
    monkeypatch.setattr("time.sleep", lambda s: None)
    OllamaGenerator.stop_model_by_name(None)
    assert calls == []


def test_stop_model_calls_ollama_stop(monkeypatch):
    calls: list = []
    monkeypatch.setattr(f"{_MODULE}.subprocess.run", lambda args, **kw: calls.append(args))
    monkeypatch.setattr("time.sleep", lambda s: None)
    OllamaGenerator.stop_model_by_name("my_model")
    assert any("ollama" in args and "stop" in args for args in calls)
