from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict
from uuid import UUID

from deepteam.metrics import BaseRedTeamingMetric
from deepteam.vulnerabilities import BaseVulnerability

from ..chatbot import store
from ..chatbot.base import BaseChatbot
from ..chatbot.store import ChatbotStore
from ..enums import Category, Chatbot, TestCaseName, Subcategory, Severity
from ..guardrail.runner import GuardrailRunner
from ..models import TestCaseResult, Attack, DetectionResult, PromptVariants, ChatbotResponseEvaluation, ChatbotResponse


class BaseTestCase(ABC):
    """Abstract base for all test cases."""

    def __init__(self, name: TestCaseName, category: Category, sub_category: Subcategory,
                 vulnerability: BaseVulnerability,
                 vuln_metric: BaseRedTeamingMetric,
                 severity: Severity = Severity.UNSAFE,
                 is_rag: bool = True, document: str = None) -> None:
        self.name = name
        self.category = category
        self.sub_category = sub_category
        self.guardrail_runner = GuardrailRunner()
        self.is_rag = is_rag
        self.vulnerability: BaseVulnerability = vulnerability
        self.metric = vuln_metric
        self.severity = severity

    def execute(self) -> TestCaseResult:
        """Run the test case and return a mapping from attack_id to TestCaseResult.
            Build the attacks and add the techniques. Then execute the attacks on the guardrails.
        """
        attack_results: dict[UUID, Attack] = {}
        if self.vulnerability:
            chatbots: Dict[Chatbot, BaseChatbot] = ChatbotStore.get_chatbots()

            attacks = self.vulnerability.simulate_attacks()
            for attack in attacks:
                base_attack: str = str(attack.input)
                attack.input = self.enhance_base_attack(attack.input)
                llm_responses: dict[Chatbot, str] = {}
                bot_responses_eval: dict[Chatbot, ChatbotResponseEvaluation] = {}
                # run attack on each model
                for name, chatbot in chatbots.values():
                    model_resp = chatbot.query(attack.input, is_rag=self.is_rag)
                    llm_responses[name] = model_resp.response
                    attack.actual_output = model_resp.response
                    self.metric.measure(attack)
                    bot_responses_eval[name] = ChatbotResponseEvaluation(model_resp,
                                                                         float(self.metric.score),
                                                                         str(self.metric.reason)
                                                                         )
                protection: Dict[str, Dict[Chatbot, DetectionResult]] = self.guardrail_runner.run(
                    attack.input,
                    llm_responses
                )

                attack_results[UUID(version=4)] = Attack(
                    self.category, self.sub_category, self.severity,
                    PromptVariants(base_attack, attack.input),
                    bot_responses_eval, protection, self.document
                )
        return TestCaseResult(self.name, self.category, attack_results)

    @abstractmethod
    def store_results(self, results: TestCaseResult) -> str:
        """Store the results."""
        raise NotImplementedError

    @abstractmethod
    def enhance_base_attack(self, base_attack: str) -> str:
        """Store the results."""
        raise NotImplementedError
