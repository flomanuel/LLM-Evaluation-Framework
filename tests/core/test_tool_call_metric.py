#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

from types import SimpleNamespace

from testframework.metrics.tool_call_code_injection import ToolCallCodeInjectionMetric
from testframework.models import ToolInfo


# ---------------------------------------------------------------------------
# _normalize_tool_info
# ---------------------------------------------------------------------------

def test_normalize_tool_info_none_returns_false_dict():
    result = ToolCallCodeInjectionMetric._normalize_tool_info(None)
    assert result == {"tool_called": False, "tool_name": None, "tool_args": None}


def test_normalize_tool_info_tool_info_object():
    info = ToolInfo(tool_called=True, tool_name="search", tool_args={"q": "x"})
    result = ToolCallCodeInjectionMetric._normalize_tool_info(info)
    assert result == {"tool_called": True, "tool_name": "search", "tool_args": {"q": "x"}}


# ---------------------------------------------------------------------------
# measure
# ---------------------------------------------------------------------------

def test_measure_no_tool_call_returns_score_one():
    metric = ToolCallCodeInjectionMetric()
    fake_case = SimpleNamespace(input="test")
    score = metric.measure(fake_case, tool_info=ToolInfo(tool_called=False))
    assert score == 1.0
    assert metric.success is True


def test_measure_tool_call_delegates_to_geval(monkeypatch):
    metric = ToolCallCodeInjectionMetric()
    fake_case = SimpleNamespace(input="test")

    def _fake_geval_measure(test_case):
        metric._g_eval.score = 0.0
        metric._g_eval.reason = "flagged"
        metric._g_eval.success = False
        metric._g_eval.error = None
        metric._g_eval.evaluation_cost = 0
        metric._g_eval.verbose_logs = "flagged"
        return 0.0

    monkeypatch.setattr(metric._g_eval, "measure", _fake_geval_measure)

    result = metric.measure(
        fake_case,
        tool_info=ToolInfo(tool_called=True, tool_name="exec", tool_args="rm -rf /"),
    )
    assert result == 0.0


# ---------------------------------------------------------------------------
# is_successful
# ---------------------------------------------------------------------------

def test_is_successful_true_when_score_above_threshold():
    metric = ToolCallCodeInjectionMetric()
    metric.score = 0.9
    metric.threshold = 0.5
    assert metric.is_successful() is True


def test_is_successful_false_when_score_below_threshold():
    metric = ToolCallCodeInjectionMetric()
    metric.score = 0.1
    metric.threshold = 0.5
    assert metric.is_successful() is False
