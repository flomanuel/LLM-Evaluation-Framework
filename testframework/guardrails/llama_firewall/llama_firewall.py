#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.


import json
import os
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
        if self._firewall is None:
            self._firewall = LlamaFirewallGuard(scanners=self._scanners)
        return self._firewall

    def eval_attack(self, user_prompt: str, attack_description: str, **kwargs) -> DetectionElement:
        user_msg = UserMessage(user_prompt)
        try:
            test_started = perf_counter()
            res: Dict[str, List[ScannerDetail] | ScanResult] = self._llama_firewall.scan(user_msg)
            test_ended = perf_counter()

            return self._build_result(res, test_ended, test_started)
        except Exception as e:
            return DetectionElement.from_error(TestErrorInfo.from_exception(e))

    def eval_model_response(self, model_response: str, chatbot: ChatbotName, attack_description: str,
                            **kwargs) -> DetectionElement:
        t_info: ToolInfo = kwargs.get("tool_info", None)
        tool_info = [
            {
                "name": t_info.tool_name,
                "args": json.dumps(t_info.tool_args),
                "was_called": t_info.tool_called,
            }
        ] if t_info is not None else []
        assistant_msg = AssistantMessage(content=model_response, tool_calls=tool_info)
        try:
            test_started = perf_counter()
            res: Dict[str, List[ScannerDetail] | ScanResult] = self._llama_firewall.scan(assistant_msg)
            test_ended = perf_counter()
            return self._build_result(res, test_ended, test_started)
        except Exception as e:
            return DetectionElement.from_error(TestErrorInfo.from_exception(e))

    def _build_result(self, res: Dict[str, List[ScannerDetail] | ScanResult], test_ended: float,
                      test_started: float) -> DetectionElement:
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

    def _scanner_details_from_reason(self, raw_reason) -> List[ScannerDetail]:
        scanner_details = []
        reasons = raw_reason.split(";")
        if len(reasons) > 0:
            for reason_x in reasons:
                type_reason, score_decision = reason_x.split("-")
                scanner_type, reason = type_reason.strip().split(":")
                score, decision = score_decision.strip().split("|")
                try:
                    score = float(score.replace("score: ", ""))
                except ValueError:
                    score = -1
                scanner_details.append(ScannerDetail(
                    name=scanner_type.strip(),
                    score=score,
                    reason=reason.strip(),
                    is_valid=decision.strip().lower() == ScanDecision.ALLOW.value,
                    sanitized_input="",
                ))
        return scanner_details
