from __future__ import annotations

from pathlib import Path
from typing import Dict
from uuid import uuid4

from ..attacks.csv_vulnerability import CsvVulnerability
from ..attacks.pipeline import AttackPipeline
from ..chatbot.store import ChatbotStore
from ..enums import Category
from ..guardrail.runner import GuardrailRunner
from ..models import (
    Attack,
    AttackCategoryResult,
    AttackMetadata,
    LlmParams,
    LlmResponses,
    RagContext,
    TestCaseResult,
)
from .base import BaseTestCase


class IndirectPromptInjectionCsvTestCase(BaseTestCase):
    """Test case for indirect prompt injection using a CSV file as source."""

    def __init__(self, csv_path: str | Path = "2_schaedlich_manuell_erstellt_basic.csv") -> None:
        super().__init__(name="indirect_prompt_injection_csv", category=Category.PROMPT_INJECTION)
        self.csv_path = Path(csv_path)
        # Category column filter inside the CSV
        self.csv_category_key = "indirect-prompt-injection"
        self.vulnerability = CsvVulnerability(
            csv_path=self.csv_path,
            types=[self.csv_category_key],
        )
        self.pipeline = AttackPipeline()
        self.guardrail_runner = GuardrailRunner()

    def execute(self) -> Dict[str, TestCaseResult]:
        results: Dict[str, TestCaseResult] = {}
        chatbots = ChatbotStore.get_chatbots()
        if not chatbots:
            return results

        simulated_attacks = self.vulnerability.simulate_attacks()
        if not simulated_attacks:
            return results

        # For now, use the first registered chatbot
        chatbot = next(iter(chatbots.values()))

        for sa in simulated_attacks:
            baseline = sa.input
            variants, tokens = self.pipeline.build_variants(baseline)

            system_prompt = self.guardrail_runner.build_system_prompt(category=self.category)
            llm_resp_map = chatbot.query(
                user_prompt=variants.enhanced,
                is_rag=False,
                file_path=None,
                system_prompt=system_prompt,
            )

            llm_responses = LlmResponses(
                gpt_41=None,
                gpt_5=None,
            )
            # Map responses into LlmResponses; currently only GPT_41 is used.
            if "GPT_41" in llm_resp_map:
                mr = llm_resp_map["GPT_41"]
                # attack_success flag is computed later; for now default to False.
                from ..models import ToolInfo, LlmResponsePerModel

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
                subcategory=self.csv_category_key,
                prompt=variants,
                prompt_tokens=tokens,
                rag_context=RagContext(),
                llm_params=LlmParams(),
                llm_responses=llm_responses,
                protection=protection,
                metadata=AttackMetadata(
                    severity=None,
                    category_raw=self.csv_category_key,
                ),
            )

            tcr = TestCaseResult(attack=attack)
            results[str(attack_id)] = tcr

        return results


