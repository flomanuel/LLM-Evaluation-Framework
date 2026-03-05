#  Copyright (c) 2026.
#  Florian Emanuel Sauer
from __future__ import annotations

from typing import Dict

from testframework import ChatbotName
from testframework.guardrails.base import BaseGuardrail
from testframework.models import DetectionElement
from guardrails import Guard


class GuardrailsAI(BaseGuardrail):
    """Guardrail for GuardrailsAI from [GuardrailsAI](https://guardrailsai.com/).
    Use the REST-API provided by the GuardrailsAI docker container. Swagger documentation: http://localhost:8000/docs
    """

    GUARD_NAMES = [
        "thesis_guard_sensitive_topic",
        "thesis_guard_detect_jailbreak",
        "thesis_guard_toxic_language",
        "thesis_guard_bias_check",
        "thesis_guard_pii",
        "thesis_guard_shieldgemma_2b",
        "thesis_guard_llamaguard_7b",
    ]

    def __init__(self) -> None:
        super().__init__("Guardrails AI")
        self._guards: Dict[str, Guard] = {}

    def eval_attack(self, user_prompt: str, attack_description: str, **kwargs) -> DetectionElement:
        self._load_all_guards()
        res = {}
        for guard_name in self.GUARD_NAMES:
            guard = self._get_guards(guard_name)
            try:
                res[guard_name] = guard.parse(user_prompt)
            except Exception as e:
                red[guard_name] = f"Error: {e}"

        return DetectionElement(
            success=False,
            detected_type=None,
            score=0.0,
            judge_raw_response="GuardrailsAI eval_attack is not implemented yet.",
            latency=None,
            scanner_details=[],
        )

    def eval_model_response(self, model_response: str, chatbot: ChatbotName, attack_description: str,
                            **kwargs) -> DetectionElement:
        self._load_all_guards()
        res = {}
        for guard_name in self.GUARD_NAMES:
            guard = self._get_guards(guard_name)
            try:
                res[guard_name] = guard.parse(user_prompt)
            except Exception as e:
                red[guard_name] = f"Error: {e}"
        return DetectionElement(
            success=False,
            detected_type=None,
            score=0.0,
            judge_raw_response="GuardrailsAI eval_model_response is not implemented yet.",
            latency=None,
            scanner_details=[],
        )

    def _load_all_guards(self) -> None:
        for guard_name in self.GUARD_NAMES:
            self._get_guards(guard_name)

    def _get_guards(self, guard_name: str) -> Guard:
        if guard_name not in self._guards:
            guard = Guard(history_max_length=0).load(
                name=guard_name,
                base_url="http://localhost:8000",
                history_max_length=0,
            )
            if guard is None:
                raise ValueError(f"Failed to load Guardrails guard '{guard_name}'.")
            self._guards[guard_name] = guard
        return self._guards[guard_name]
