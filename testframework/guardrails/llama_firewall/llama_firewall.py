#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.


import json
import os
import asyncio
import unicodedata
from time import perf_counter
from typing import List, Dict
from testframework import ChatbotName, LLMErrorType
from testframework.guardrails.base import BaseGuardrail
from testframework.models import DetectionElement, ToolInfo, TestErrorInfo, ScannerDetail
from llamafirewall import UserMessage, AssistantMessage, Role, ScannerType, \
    ScanResult, ScanStatus, ScanDecision
from testframework.guardrails.llama_firewall.llama_firewall_with_metrics import \
    LlamaFirewallWithMetrics as LlamaFirewallGuard


class LlamaFirewall(BaseGuardrail):
    """Guardrail for LlamaFirewall"""

    _firewall: LlamaFirewallGuard | None = None

    _scanners = {
        Role.TOOL: [ScannerType.CODE_SHIELD, ScannerType.PROMPT_GUARD],
        Role.USER: [ScannerType.CODE_SHIELD, ScannerType.PROMPT_GUARD, ScannerType.PII_DETECTION, ScannerType.REGEX],
        Role.ASSISTANT: [ScannerType.CODE_SHIELD, ScannerType.PROMPT_GUARD, ScannerType.PII_DETECTION,
                         ScannerType.REGEX],
    }

    def __init__(self):
        super().__init__("LlamaFirewall")
        # https://stackoverflow.com/questions/62691279/how-to-disable-tokenizers-parallelism-true-false-warning
        os.environ["TOKENIZERS_PARALLELISM"] = "false"

    @property
    def _llama_firewall(self):
        """Get the custom LlamaFirewallGuard instance."""
        if self._firewall is None:
            self._firewall = LlamaFirewallGuard(scanners=self._scanners)
        return self._firewall

    def _scan_with_metrics(self, message) -> Dict[str, List[ScannerDetail] | ScanResult]:
        """
        Scan a message with metrics.
        Use asyncio runner instance since LlamaFirewallGuard calls filters asynchronously. By default, they get handled
        by asyncio, which sometimes closes the async loop (?) before all scanners have finished. So it seems, at least.
        https://stackoverflow.com/a/45600858
        https://docs.python.org/3/library/asyncio-runner.html#asyncio.Runner.run
        https://docs.python.org/3/library/asyncio-eventloop.html#asyncio-event-loop
        """
        with asyncio.Runner() as runner:
            return runner.run(self._llama_firewall.scan(message))

    @staticmethod
    def _normalize_text_for_scanner(text: str) -> str:
        """
        Normalize scanner input since some scanner implementations seem to have problems handling UTF-8.
        https://stackoverflow.com/questions/16467479/normalizing-unicode
        https://stackoverflow.com/questions/43953293/how-to-convert-symbols-into-their-respective-unicode-representation-using-python
        """
        if not text:
            return ""

        normalized = unicodedata.normalize("NFKD", unicodedata.normalize("NFD", text))
        return normalized.encode("ascii", "ignore").decode("ascii")

    def eval_attack(self, user_prompt: str, **kwargs) -> DetectionElement:
        """Avaluate an attack."""
        user_msg = UserMessage(self._normalize_text_for_scanner(user_prompt))
        try:
            test_started = perf_counter()
            res: Dict[str, List[ScannerDetail] | ScanResult] = self._scan_with_metrics(user_msg)
            test_ended = perf_counter()

            return self._build_result(res, test_ended, test_started)
        except Exception as e:
            return DetectionElement.from_error(TestErrorInfo.from_exception(e))

    def eval_model_response(self, model_response: str, chatbot: ChatbotName, **kwargs) -> DetectionElement:
        """Evaluate the response from the attacked model."""
        t_info: ToolInfo = kwargs.get("tool_info", None)
        tool_info = [
            {
                "name": t_info.tool_name,
                "args": json.dumps(t_info.tool_args),
                "was_called": t_info.tool_called,
            }
        ] if t_info is not None else []
        assistant_msg = AssistantMessage(
            content=self._normalize_text_for_scanner(model_response),
            tool_calls=tool_info,
        )
        try:
            test_started = perf_counter()
            res: Dict[str, List[ScannerDetail] | ScanResult] = self._scan_with_metrics(assistant_msg)
            test_ended = perf_counter()
            return self._build_result(res, test_ended, test_started)
        except Exception as e:
            return DetectionElement.from_error(TestErrorInfo.from_exception(e))

    def _build_result(self, res: Dict[str, List[ScannerDetail] | ScanResult], test_ended: float,
                      test_started: float) -> DetectionElement:
        """Build the scan result."""
        orig_scan_result = res.get("scan_result", None)
        scanner_details = res.get("scanner_details", None)
        error = TestErrorInfo(LLMErrorType.UNKNOWN,
                              f"{orig_scan_result.status.name}=({orig_scan_result.status.value})") if orig_scan_result.status is ScanStatus.ERROR else None
        return DetectionElement(
            success=orig_scan_result.decision is ScanDecision.ALLOW,
            detected_type=None,
            score=orig_scan_result.score,  # 1: block / 0: allow
            judge_raw_response=orig_scan_result.reason,
            latency=test_ended - test_started,
            scanner_details=scanner_details,
            error=error,
        )
