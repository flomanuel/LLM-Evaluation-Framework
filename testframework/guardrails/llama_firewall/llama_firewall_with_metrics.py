#  Copyright (c) 2026 Florian Emanuel Sauer
#  Copyright (c) Meta Platforms, Inc. and affiliates.
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

from typing import override, Dict, List
from llamafirewall import LlamaFirewall
from llamafirewall.llamafirewall import create_scanner, LOG
from llamafirewall.llamafirewall_data_types import (
    Message,
    ScanDecision,
    ScanResult,
    ScanStatus,
    Trace,
)
from testframework.models import ScannerDetail


class LlamaFirewallWithMetrics(LlamaFirewall):
    """
    Cstom LlamaFirewall with metrics instance.
    Change 1: async scan behavior (since by default the async loop sometimes gets closed before all scanners have finished).
    Change 2: return dict instead of ScanResult to enhance the logging details for the statistical evaluation.
    """

    @override
    async def scan(self, input_msg: Message, trace: Trace | None = None) -> Dict[
        str, List[ScannerDetail] | ScanResult]:
        """Scan the input with the scanners."""
        scanners = self.scanners.get(input_msg.role, [])
        reasons = []
        decisions = {}
        last_reason = ""
        scanner_details: List[ScannerDetail] = []
        for scanner_type in scanners:
            scanner_instance = create_scanner(scanner_type)
            LOG.debug(
                f"[LlamaFirewall] Scanning with {scanner_instance.name}, for the input {str(input_msg.content)[:20]}"
            )
            scanner_result = await scanner_instance.scan(input_msg, trace)
            reasons.append(
                f"{scanner_type}: {scanner_result.reason.strip()} - score: {scanner_result.score}"
            )
            scanner_details.append(ScannerDetail(
                name=scanner_type,
                score=scanner_result.score,
                reason=scanner_result.reason.strip(),
                is_valid=scanner_result.decision == ScanDecision.ALLOW,
                sanitized_input="",
            ))
            last_reason = scanner_result.reason.strip()

            # Record the highest score for each found ScanDecision
            decisions[scanner_result.decision] = max(
                scanner_result.score,
                decisions.get(scanner_result.decision, scanner_result.score),
            )

        if len(scanners) == 1:
            scan_result = ScanResult(decision=list(decisions.keys())[0], reason=last_reason,
                                     score=list(decisions.values())[0], status=ScanStatus.SUCCESS, )
            res = {
                "scanner_details": scanner_details,
                "scan_result": scan_result
            }
            return res

        formatted_reasons = "; ".join(set(reasons))
        # Select BLOCK as the final decision if present in the list,
        # otherwise select the decision with the highest score
        final_decision = (
            ScanDecision.BLOCK
            if ScanDecision.BLOCK in decisions.keys()
            else max(decisions, key=decisions.get)
            if decisions
            else ScanDecision.ALLOW
        )
        final_score = (
            decisions[ScanDecision.BLOCK]
            if ScanDecision.BLOCK in decisions.keys()
            else max(list(decisions.values()) + [0.0])
        )

        scan_result: ScanResult = ScanResult(decision=final_decision,
                                             reason=formatted_reasons if formatted_reasons else "default",
                                             score=final_score,
                                             status=ScanStatus.SUCCESS,
                                             )
        res = {
            "scanner_details": scanner_details,
            "scan_result": scan_result
        }

        return res
