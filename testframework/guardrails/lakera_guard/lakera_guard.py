#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.
from __future__ import annotations

import json
import os
from time import perf_counter
import requests
from testframework.guardrails.base import BaseGuardrail
from testframework.models import DetectionElement, ScannerDetail


class LakeraGuard(BaseGuardrail):
    """Guardrail implementation backed by the Lakera Guard API."""

    API_URL = "https://api.lakera.ai/v2/guard"
    FALLBACK_SCANNER_NAME = "lakera_guard"
    MAX_ATTEMPTS: int = 1

    def __init__(self, name: str = "lakera_guard") -> None:
        super().__init__(name=name)
        self._api_key = os.environ.get("LAKERA_GUARD_API_KEY", "").strip()
        self._project_id = os.environ.get("LAKERA_GUARD_PROJECT_ID", "").strip()
        timeout_raw = os.environ.get("LAKERA_GUARD_TIMEOUT_SECONDS", "60").strip()
        if not self._api_key:
            raise ValueError("LAKERA_GUARD_API_KEY must be set.")
        if not self._project_id:
            raise ValueError("LAKERA_GUARD_PROJECT_ID must be set.")
        try:
            self._timeout_seconds = float(timeout_raw)
        except ValueError as exc:
            raise ValueError("LAKERA_GUARD_TIMEOUT_SECONDS must be a positive number.") from exc
        if self._timeout_seconds <= 0:
            raise ValueError("LAKERA_GUARD_TIMEOUT_SECONDS must be a positive number.")

    def eval_attack(self, user_prompt: str, *args, **kwargs) -> DetectionElement:
        """Evaluate the attack."""
        messages = [{"role": "user", "content": user_prompt}]
        return self._evaluate_messages(messages)

    def eval_model_response(self, model_response: str, *args, **kwargs) -> DetectionElement:
        """Evaluate the response from the attacked model."""
        t_info = kwargs.get("tool_info", None)
        if t_info:
            name = t_info.tool_name if t_info.tool_name else 'N/A'
            called = t_info.tool_called if t_info.tool_called else 'N/A'
            args = t_info.tool_args if t_info.tool_args else 'N/A'
            resp_or_tool = f"=== Tool Call ===\nTool Name: {name} \n Tool Was Called: {called} \n Tool Call Args: {args}"
        else:
            resp_or_tool = model_response
        messages = [{"role": "assistant", "content": resp_or_tool}]
        return self._evaluate_messages(messages)

    def _evaluate_messages(self, messages: list[dict[str, str]]) -> DetectionElement:
        """Evaluate the messages (i.e. attack, response)."""
        test_started = perf_counter()
        resp = self._call_api(messages=messages)
        test_ended = perf_counter()
        flagged = bool(resp.get("flagged", False))
        breakdown = resp.get("breakdown")
        scanner_details = self._build_scanner_details(breakdown)
        if flagged:
            scanner_alerts = ", ".join((scanner.name for scanner in scanner_details)) if scanner_details else "flagged"
        else:
            scanner_alerts = None
        detection = DetectionElement(
            success=not flagged,
            detected_type=scanner_alerts,
            score=1.0 if flagged else 0.0,
            judge_raw_response=json.dumps(resp),
            latency=test_ended - test_started,
            scanner_details=scanner_details,
            error=None,
        )
        return detection

    def _call_api(self, messages: list[dict[str, str]]) -> dict:
        """Call the Lakera Guard API."""
        payload = {"messages": messages, "project_id": self._project_id, "breakdown": True}
        headers = {"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"}
        for attempt in range(1, self.MAX_ATTEMPTS + 1):
            try:
                body = requests.post(self.API_URL, json=payload, headers=headers, timeout=self._timeout_seconds).json()
                return body
            except requests.RequestException as exc:
                if attempt >= self.MAX_ATTEMPTS:
                    raise RuntimeError(f"Lakera Guard API request failed: {exc}") from exc
        raise RuntimeError("Unknown Lakera request failure.")

    def _build_scanner_details(
            self,
            breakdown,
    ) -> list[ScannerDetail]:
        """Build the scanner details from the breakdown in the response."""
        breakdown_entries = breakdown if isinstance(breakdown, list) else []
        details: list[ScannerDetail] = []
        for scanner_result in breakdown_entries:
            if not isinstance(scanner_result, dict):
                continue
            detected = bool(scanner_result.get("detected", False))
            detector_type: str | bool = scanner_result.get("detector_type", False)
            detector_id = scanner_result.get("detector_id", False)
            detector_name = detector_type if detector_type else detector_id
            reason = "Detector rejected message" if detected else "Detector accepted message"
            reason = f"{reason} ({detector_type})"
            details.append(
                ScannerDetail(
                    name=detector_name,
                    score=1.0 if detected else 0.0,
                    reason=reason,
                    is_valid=not detected,
                    sanitized_input="",
                )
            )
        return details
