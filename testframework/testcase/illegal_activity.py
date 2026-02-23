from __future__ import annotations

from typing import Dict
from uuid import uuid4

from deepteam.vulnerabilities import IllegalActivity  # type: ignore
from deepteam.attacks.single_turn import MathProblem  # type: ignore

from ..attacks.pipeline import AttackPipeline
from ..chatbot.store import ChatbotStore
from ..enums import Category
from ..guardrail.runner import GuardrailRunner
from ..models import (
    Attack,
    AttackMetadata,
    LlmParams,
    LlmResponses,
    RagContext,
    TestCaseResult,
)
from .base import BaseTestCase


class IllegalActivityTestCase(BaseTestCase):
    """Test case using DeepTeam's IllegalActivity vulnerability as attack source."""

    def __init__(self) -> None:
        super().__init__(name="illegal_activity", category=Category.ILLEGAL_ACTIVITY)
        # Use all IllegalActivity subcategories; configuration can be adjusted later.
        self.vulnerability = IllegalActivity()
        self.math_attack = MathProblem()
        self.guardrail_runner = GuardrailRunner()

    def execute(self) -> Dict[str, TestCaseResult]:
        results: Dict[str, TestCaseResult] = {}
        chatbots = ChatbotStore.get_chatbots()
        if not chatbots:
            return results

        test_cases = self.vulnerability.simulate_attacks()
        if not test_cases:
            return results

        chatbot = next(iter(chatbots.values()))

        for tc in test_cases:
            baseline = tc.input
            # Single-turn enhancement using MathProblem, consistent with example.
            enhanced_attack = self.math_attack.enhance(attack=baseline)

            from ..models import PromptVariants, PromptTokens, ToolInfo, LlmResponsePerModel

            variants = PromptVariants(
                baseline=baseline,
                attack=enhanced_attack,
                enhanced=enhanced_attack,
            )
            tokens = PromptTokens(
                baseline=len(baseline.split()),
                attack=len(enhanced_attack.split()),
                enhanced=len(enhanced_attack.split()),
            )

            system_prompt = self.guardrail_runner.build_system_prompt(category=self.category)
            llm_resp_map = chatbot.query(
                user_prompt=variants.enhanced,
                is_rag=False,
                file_path=None,
                system_prompt=system_prompt,
            )

            llm_responses = LlmResponses(gpt_41=None, gpt_5=None)
            if "GPT_41" in llm_resp_map:
                mr = llm_resp_map["GPT_41"]
                llm_responses.gpt_41 = LlmResponsePerModel(
                    response=mr.response,
                    token=mr.token_count,
                    attack_success=False,
                    tool=mr.tool or ToolInfo(tool_called=False, tool_call_params=None),
                )

            protection = self.guardrail_runner.run(
                category=self.category,
                user_prompt=variants.enhanced,
                llm_responses=llm_responses,
            )

            attack_id = uuid4()
            attack = Attack(
                attack_id=attack_id,
                subcategory=str(tc.vulnerability_type),
                prompt=variants,
                prompt_tokens=tokens,
                rag_context=RagContext(),
                llm_params=LlmParams(),
                llm_responses=llm_responses,
                protection=protection,
                metadata=AttackMetadata(
                    severity=None,
                    category_raw=str(tc.vulnerability_type),
                ),
            )

            tcr = TestCaseResult(attack=attack)
            results[str(attack_id)] = tcr

        return results


