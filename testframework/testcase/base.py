from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List

from deepteam.metrics import BaseRedTeamingMetric
from deepteam.test_case import RTTestCase
from deepteam.vulnerabilities import BaseVulnerability
from loguru import logger
from testframework.chatbot.base import BaseChatbot
from testframework.chatbot.store import ChatbotStore
from testframework.enums import Category, ChatbotName, TestCaseName, Subcategory, Severity
from testframework.guardrail.runner import GuardrailRunner
from testframework.models import TestCaseResult, Attack, DetectionResult, PromptVariants, ChatbotResponseEvaluation, \
    TestErrorInfo
from testframework.storage import save_test_case_result


class BaseTestCase(ABC):
    """Abstract base for all test cases."""

    results: TestCaseResult
    run_folder: Path | None = None

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
        attack_results: dict[str, Attack] = {}
        generation_error: TestErrorInfo | None = None

        if self.attack_builder:
            attacks: List[RTTestCase] = []
            try:
                attacks = self.attack_builder.simulate_attacks()
                logger.info(f"Generated {len(attacks)} attacks for {self.name}")
            except Exception as e:
                generation_error = TestErrorInfo.from_exception(e)
                logger.error(
                    f"Attack generation failed for {self.name} "
                    f"({generation_error.error_type.value}): {generation_error.message}"
                )

            chatbots: Dict[ChatbotName, BaseChatbot] = ChatbotStore.get_chatbots()
            for attack in attacks:
                attack_result = self._execute_single_attack(attack, chatbots)
                attack_results[str(uuid.uuid4())] = attack_result

        tc_result = TestCaseResult(
            self.name, self.category, attack_results, generation_error
        )
        self.results = tc_result
        self.store_results()
        return tc_result

    def _execute_single_attack(
            self,
            attack: RTTestCase,
            chatbots: Dict[ChatbotName, BaseChatbot]
    ) -> Attack:
        """Execute a single attack against all chatbots.

        Args:
            attack: The RTTestCase attack to execute.
            chatbots: Dictionary of chatbots to test against.

        Returns:
            Attack results with responses and evaluations.
        """
        base_attack: str = str(attack.input)
        attack.input = self.enhance_base_attack(attack.input)
        bot_responses: dict[ChatbotName, str] = {}
        bot_responses_eval: dict[ChatbotName, ChatbotResponseEvaluation] = {}

        query_kwargs = self._build_query_kwargs(attack)

        for name, chatbot in chatbots.items():
            bot_responses_eval[name] = self._query_and_evaluate(
                chatbot, name, attack, query_kwargs, bot_responses
            )

        protection: Dict[str, Dict[ChatbotName, DetectionResult]] = self.guardrail_runner.run(
            attack.input,
            bot_responses
        )

        return Attack(
            self.category, self.sub_category, self.severity,
            PromptVariants(base_attack, attack.input),
            bot_responses_eval, protection
        )

    def _query_and_evaluate(
            self,
            chatbot: BaseChatbot,
            name: ChatbotName,
            attack: RTTestCase,
            query_kwargs: dict,
            llm_responses: dict[ChatbotName, str],
    ) -> ChatbotResponseEvaluation:
        """Query a chatbot and evaluate the response.

        Args:
            chatbot: The chatbot to query.
            name: The chatbot's name identifier.
            attack: The attack test case.
            query_kwargs: Additional query parameters.
            llm_responses: Dictionary to store raw responses for guardrail checks.

        Returns:
            ChatbotResponseEvaluation with score and reason.
        """
        model_resp = chatbot.query(attack.input, **query_kwargs)
        llm_responses[name] = str(model_resp.response)

        if model_resp.is_error:
            logger.warning(
                f"Chatbot {name} query failed: {model_resp.error.error_type.value}"
            )
            return ChatbotResponseEvaluation.from_error(model_resp)

        attack.actual_output = model_resp.response
        try:
            metric = self._get_metric(attack)
            metric.measure(attack)
            return ChatbotResponseEvaluation(
                model_resp,
                float(metric.score),
                str(metric.reason)
            )
        except Exception as e:
            eval_error = TestErrorInfo.from_exception(e)
            logger.warning(
                f"Metric evaluation failed for {name} "
                f"({eval_error.error_type.value}): {eval_error.message}"
            )
            return ChatbotResponseEvaluation.from_error(model_resp, eval_error)

    @abstractmethod
    def _get_metric(self, attack: RTTestCase = None) -> BaseRedTeamingMetric:
        """Return the metric to evaluate the attack."""
        raise NotImplementedError

    def store_results(self) -> Path | None:
        """Store the test case results as a backup to the run folder.

        Returns:
            The path to the saved JSON file, or None if run_folder is not set.
        """
        if self.run_folder is None:
            return None
        return save_test_case_result(self.results, self.run_folder)

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
