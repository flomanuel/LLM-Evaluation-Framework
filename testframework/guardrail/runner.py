from __future__ import annotations

from typing import Dict, Iterable

from ..enums import Category
from ..models import (
    LlmResponses,
    PromptHardening,
    PromptHardeningPerModel,
    Protection,
)
from .prompt_hardening import PromptHardeningGuardrail


class GuardrailRunner:
    """Runs configured guardrails over attacks and model responses."""

    def __init__(self, prompt_hardening_guardrail: PromptHardeningGuardrail | None = None) -> None:
        self.prompt_hardening_guardrail = prompt_hardening_guardrail or PromptHardeningGuardrail()

    def build_system_prompt(self, category: Category | None = None) -> str:
        return self.prompt_hardening_guardrail.build_system_prompt(category=category)

    def run(
        self,
        category: Category | None,
        user_prompt: str,
        llm_responses: LlmResponses,
    ) -> Protection:
        ph = PromptHardening()

        if llm_responses.gpt_41 is not None:
            per_model: PromptHardeningPerModel = self.prompt_hardening_guardrail.evaluate_for_model(
                category=category,
                user_prompt=user_prompt,
                response=llm_responses.gpt_41.response,
            )
            ph.gpt_41 = per_model

        if llm_responses.gpt_5 is not None:
            per_model_5: PromptHardeningPerModel = self.prompt_hardening_guardrail.evaluate_for_model(
                category=category,
                user_prompt=user_prompt,
                response=llm_responses.gpt_5.response,
            )
            ph.gpt_5 = per_model_5

        return Protection(prompt_hardening=ph, llm_guard=None)


