from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict
from uuid import UUID

from deepteam.metrics import BaseRedTeamingMetric
from deepteam.test_case import RTTestCase
from deepteam.vulnerabilities import BaseVulnerability

from ..chatbot import store
from ..chatbot.base import BaseChatbot
from ..chatbot.store import ChatbotStore
from ..enums import Category, Chatbot, TestCaseName, Subcategory, Severity
from ..guardrail.runner import GuardrailRunner
from ..models import TestCaseResult, Attack, DetectionResult, PromptVariants, ChatbotResponseEvaluation, ChatbotResponse


class BaseTestCase(ABC):
    """Abstract base for all test cases."""

    def __init__(self, name: TestCaseName, category: Category, sub_category: Subcategory | None,
                 attack_builder: BaseVulnerability,
                 severity: Severity = Severity.UNSAFE,
                 ) -> None:
        self.name = name
        self.category = category
        self.sub_category = sub_category
        self.guardrail_runner = GuardrailRunner()
        self.attack_builder: BaseVulnerability = attack_builder
        self.severity = severity

    def execute(self) -> TestCaseResult:
        """Run the test case and return a mapping from attack_id to TestCaseResult.
            Build the attacks and add the techniques. Then execute the attacks on the guardrails.
        """
        attack_results: dict[UUID, Attack] = {}
        if self.attack_builder:
            chatbots: Dict[Chatbot, BaseChatbot] = ChatbotStore.get_chatbots()

            attacks = self.attack_builder.simulate_attacks()
            for attack in attacks:
                base_attack: str = str(attack.input)
                attack.input = self.enhance_base_attack(attack.input)
                llm_responses: dict[Chatbot, str] = {}
                bot_responses_eval: dict[Chatbot, ChatbotResponseEvaluation] = {}

                # Build optional kwargs from attack attributes
                query_kwargs = self._build_query_kwargs(attack)

                # run attack on each chatbot
                for name, chatbot in chatbots.values():
                    model_resp = chatbot.query(attack.input, **query_kwargs)
                    llm_responses[name] = str(model_resp.response)
                    attack.actual_output = model_resp.response
                    metric = self._get_metric(attack)
                    metric.measure(attack)
                    bot_responses_eval[name] = ChatbotResponseEvaluation(model_resp,
                                                                         float(metric.score),
                                                                         str(metric.reason)
                                                                         )
                protection: Dict[str, Dict[Chatbot, DetectionResult]] = self.guardrail_runner.run(
                    attack.input,
                    llm_responses
                )

                attack_results[UUID(version=4)] = Attack(
                    self.category, self.sub_category, self.severity,
                    PromptVariants(base_attack, attack.input),
                    bot_responses_eval, protection
                )
        return TestCaseResult(self.name, self.category, attack_results)

    @abstractmethod
    def _get_metric(self, attack: RTTestCase = None) -> BaseRedTeamingMetric:
        """Return the metric to evaluate the attack."""
        raise NotImplementedError

    @abstractmethod
    def store_results(self, results: TestCaseResult) -> str:
        """Store the results."""
        raise NotImplementedError

    @abstractmethod
    def enhance_base_attack(self, base_attack: str) -> str:
        """Store the results."""
        raise NotImplementedError

    @staticmethod
    def _build_query_kwargs(attack: Attack) -> dict:
        """Build additional args for custom attack scenarios."""

        query_kwargs = {}
        if hasattr(attack, "is_rag") and attack.is_rag is not None:
            query_kwargs["is_rag"] = attack.is_rag
        if hasattr(attack, "file_path") and attack.file_path is not None:
            query_kwargs["file_path"] = attack.file_path
        if hasattr(attack, "system_prompt") and attack.system_prompt is not None:
            query_kwargs["system_prompt"] = attack.system_prompt
        return query_kwargs
