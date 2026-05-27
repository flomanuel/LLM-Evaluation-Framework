#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

from llamafirewall import ScanDecision, ScanResult, ScanStatus

from testframework import ChatbotName
from testframework.guardrails.llama_firewall.llama_firewall import LlamaFirewall


def test_normalize_text_for_scanner_rewrites_problematic_unicode():
    # Non-ASCII chars are stripped via NFKD + encode("ascii","ignore").
    # Curly apostrophe, non-breaking hyphen, em dash, and bullet are stripped;
    # the ellipsis … decomposes to "..."; \xfc (u-umlaut) loses the umlaut.
    text = "I ’t assist step‑by‑step — use bullets • and ellipsis… in M\xfcnchen."

    normalized = LlamaFirewall._normalize_text_for_scanner(text)

    assert normalized == "I t assist stepbystep  use bullets  and ellipsis... in Munchen."
    assert normalized.isascii()


def test_eval_model_response_scans_normalized_text(monkeypatch):
    guard = LlamaFirewall()
    captured = {}

    def fake_scan_with_metrics(message):
        captured["content"] = message.content
        return {
            "scanner_details": [],
            "scan_result": ScanResult(
                decision=ScanDecision.ALLOW,
                reason="normalized",
                score=0.0,
                status=ScanStatus.SUCCESS,
            ),
        }

    monkeypatch.setattr(guard, "_scan_with_metrics", fake_scan_with_metrics)

    result = guard.eval_model_response(
        "I ’t assist step‑by‑step — in M\xfcnchen.",
        chatbot=ChatbotName.LANGCHAIN_GPT_5,
    )

    assert result.success is True
    assert captured["content"] == "I t assist stepbystep  in Munchen."


# ---------------------------------------------------------------------------
# Additional normalization cases
# ---------------------------------------------------------------------------

def test_normalize_text_for_scanner_preserves_plain_ascii():
    text = "Hello, World! 123 abc."
    result = LlamaFirewall._normalize_text_for_scanner(text)
    assert result == text


def test_normalize_text_for_scanner_handles_empty_string():
    result = LlamaFirewall._normalize_text_for_scanner("")
    assert result == ""


# ---------------------------------------------------------------------------
# LlamaFirewall.eval_attack – mocked _scan_with_metrics
# ---------------------------------------------------------------------------

def test_eval_attack_returns_success_when_scan_allows(monkeypatch):
    guard = LlamaFirewall()
    monkeypatch.setattr(guard, "_scan_with_metrics", lambda msg: {
        "scanner_details": [],
        "scan_result": ScanResult(
            decision=ScanDecision.ALLOW,
            reason="ok",
            score=0.0,
            status=ScanStatus.SUCCESS,
        ),
    })
    result = guard.eval_attack("hello")
    assert result.success is True
    assert result.is_error is False


def test_eval_attack_returns_failure_when_scan_blocks(monkeypatch):
    guard = LlamaFirewall()
    monkeypatch.setattr(guard, "_scan_with_metrics", lambda msg: {
        "scanner_details": [],
        "scan_result": ScanResult(
            decision=ScanDecision.BLOCK,
            reason="blocked",
            score=1.0,
            status=ScanStatus.SUCCESS,
        ),
    })
    result = guard.eval_attack("malicious prompt")
    assert result.success is False


def test_eval_attack_returns_error_on_exception(monkeypatch):
    guard = LlamaFirewall()

    def _raise(msg):
        raise RuntimeError("scan failed")

    monkeypatch.setattr(guard, "_scan_with_metrics", _raise)
    result = guard.eval_attack("test")
    assert result.is_error is True
