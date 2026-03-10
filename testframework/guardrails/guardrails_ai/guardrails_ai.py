#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.


from __future__ import annotations

from time import perf_counter
from typing import Dict
from testframework import ChatbotName
from testframework.guardrails.base import BaseGuardrail
from testframework.guardrails.guardrails_ai.constants import GUARD_NAMES
from testframework.models import DetectionElement, ScannerDetail
from guardrails import Guard


class GuardrailsAI(BaseGuardrail):
    """Guardrail for GuardrailsAI from [GuardrailsAI](https://guardrailsai.com/).
    Use the REST-API provided by the GuardrailsAI docker container. Swagger documentation: http://localhost:8000/docs
    """

    SHIELDGEMMA2_IDENTIFIER = "thesis_guard_shieldgemma_2b_"
    SHIELDGEMMA2_AGGREGATED_GUARD_NAME = "thesis_guard_shieldgemma_2b"

    def __init__(self) -> None:
        super().__init__("Guardrails AI")
        self._guards: Dict[str, Guard] = {}

    def eval_attack(self, user_prompt: str, **kwargs) -> DetectionElement:
        return self._evaluate_input(user_prompt)

    def eval_model_response(self, model_response: str, chatbot: ChatbotName, **kwargs) -> DetectionElement:
        t_info = kwargs.get("tool_info", None)
        if t_info:
            tool_call = f"Tool Name: {t_info.tool_name if t_info.tool_name else 'N/A'} \n Tool Was Called: {t_info.tool_called if t_info.tool_called else 'N/A'} \n Tool Call Args: {t_info.tool_args if t_info.tool_args else 'N/A'}"
            current_output = f"=== Tool Call ===\n{tool_call}"
        else:
            current_output = model_response
        return self._evaluate_input(current_output)

    def _evaluate_input(self, text: str) -> DetectionElement:
        self._load_all_guards()
        scanner_details: list[ScannerDetail] = []
        shieldgemma_scanner_detail = ScannerDetail(
            name=self.SHIELDGEMMA2_AGGREGATED_GUARD_NAME,
            score=-1,
            reason="",
            is_valid=True,
            sanitized_input="",
        )

        test_started = perf_counter()
        for guard_name in GUARD_NAMES:
            guard = self._get_guards(guard_name)
            try:
                raw_result = guard.parse(text)
                is_valid = raw_result.validation_passed if (
                        raw_result.validation_passed not in [None, ""] and not raw_result.error) else False
                sanitized_text = raw_result.validated_output if raw_result.validated_output else ""
                reason = "" if not raw_result.error else raw_result.error
                score = -1
            except Exception as exc:
                is_valid = False
                sanitized_text = ""
                reason = exc.args[0] if len(exc.args) > 0 else "Unknown reason"
                if not isinstance(reason, str): reason = "Unknown reason"
                score = -1

            # streamline Gemma2 evaluation to be equal to LlamaGuard results which aggregates the results for all
            # defined policies into one policy.
            if guard_name.startswith(self.SHIELDGEMMA2_IDENTIFIER):
                shieldgemma_scanner_detail.is_valid = shieldgemma_scanner_detail.is_valid and is_valid
                if not is_valid and reason:
                    if shieldgemma_scanner_detail.reason:
                        shieldgemma_scanner_detail.reason = f"{shieldgemma_scanner_detail.reason} | {guard_name}: {reason}"
                    else:
                        shieldgemma_scanner_detail.reason = f"{guard_name}: {reason}"
                if not shieldgemma_scanner_detail.sanitized_input and sanitized_text:
                    shieldgemma_scanner_detail.sanitized_input = sanitized_text
            else:
                scanner_details.append(
                    ScannerDetail(
                        name=guard_name,
                        score=score,
                        reason=reason,
                        is_valid=is_valid,
                        sanitized_input=sanitized_text,
                    )
                )

        scanner_details.append(shieldgemma_scanner_detail)

        failing_guards = [detail.name for detail in scanner_details if not detail.is_valid]
        test_ended = perf_counter()

        success = len(failing_guards) == 0
        if success:
            judge_raw_response = "Text accepted by all Guardrails AI guards."
            detected_type = None
        else:
            judge_raw_response = f"Text rejected by: {', '.join(failing_guards)}."
            detected_type = ", ".join(failing_guards)

        return DetectionElement(
            success=success,
            detected_type=detected_type,
            score=-1,  # not possible to use score on this product since not all validators return a score
            judge_raw_response=judge_raw_response,
            latency=test_ended - test_started,
            scanner_details=scanner_details,
            error=None,
        )

    def _load_all_guards(self) -> None:
        for guard_name in GUARD_NAMES:
            self._get_guards(guard_name)

    def _get_guards(self, guard_name: str) -> Guard:
        if guard_name not in self._guards:
            guard = Guard(history_max_length=0, base_url="http://localhost:8000").load(
                name=guard_name,
                base_url="http://localhost:8000",
                history_max_length=0,
            )
            if guard is None:
                raise ValueError(f"Failed to load guard '{guard_name}'.")
            self._guards[guard_name] = guard
        return self._guards[guard_name]
