from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Dict, List

from deepeval.models import DeepEvalBaseLLM, OllamaModel
from deepteam.metrics import BaseRedTeamingMetric  # type: ignore
from deepteam.test_case import RTTestCase
from deepteam.vulnerabilities import BaseVulnerability
from loguru import logger
from testframework.chatbots.base import BaseChatbot
from testframework.chatbots.store import ChatbotStore
from testframework.custom_attack_techniques import AttackListEnhancer
from testframework.enums import Category, ChatbotName, Severity
from testframework.guardrails.runner import GuardrailRunner
from testframework.models import TestCaseResult, Attack, DetectionResult, PromptVariants, ChatbotResponseEvaluation, \
    TestErrorInfo, EnhancedAttack
from testframework.storage import save_test_case_result


class BaseTestCase(ABC):
    """Abstract base for all test cases."""

    results: TestCaseResult
    run_folder: Path | None = None
    simulator_model: DeepEvalBaseLLM | str
    evaluation_model: DeepEvalBaseLLM | str

    def __init__(self,
                 category: Category,
                 subcategories: List[Enum],
                 severity: Severity = Severity.UNSAFE,
                 timeout: float = 120.0
                 ) -> None:
        self.category = category
        self.subcategories = subcategories
        self.guardrail_runner = GuardrailRunner()
        self.attack_builder: BaseVulnerability | None = None
        self.severity = severity

        # ollama run llama2-uncensored
        # ollama run ollama run aqualaguna/gemma-3-27b-it-abliterated-GGUF:q2_k
        effective_timeout = timeout
        self.simulator_model = OllamaModel(
            model="aqualaguna/gemma-3-27b-it-abliterated-GGUF:q2_k",
            generation_kwargs={
                "timeout": effective_timeout,
            }
        )
        self.evaluation_model = "gpt-4o"

    def execute(self) -> TestCaseResult:
        """Run the test case and return a mapping from attack_id to TestCaseResult.
            Build the attacks and add the techniques. Then execute the attacks on the guardrails.
        """
        attack_results: dict[str, Attack] = {}
        generation_error: TestErrorInfo | None = None
        attack_list_enhancer: AttackListEnhancer = AttackListEnhancer(self.simulator_model)

        if self.attack_builder:
            enhanced_attacks: List[EnhancedAttack] = []
            try:
                attacks: List[RTTestCase] = self.attack_builder.simulate_attacks()
                logger.info(f"Generated {len(attacks)} attacks for {self.category.value}")
                enhanced_attacks = attack_list_enhancer.enhance(attacks)
                logger.info(
                    f"Generated {len(enhanced_attacks)} enhanced attacks from {len(attacks)} attacks for {self.category.value}")
            except Exception as e:
                generation_error = TestErrorInfo.from_exception(e)
                logger.error(
                    f"Attack generation failed for {self.category.value} "
                    f"({generation_error.error_type.value}): {generation_error.message}"
                )

            chatbots: Dict[ChatbotName, BaseChatbot] = ChatbotStore.get_chatbots()
            for attack in enhanced_attacks:
                attack_result = self._execute_single_attack(attack, chatbots)
                attack_results[str(uuid.uuid4())] = attack_result

        tc_result = TestCaseResult(
            self.category,
            self.subcategories if self.subcategories else [],
            attack_results,
            generation_error
        )
        self.results = tc_result
        self.store_results()
        return tc_result

    def _execute_single_attack(
            self,
            attack: EnhancedAttack,
            chatbots: Dict[ChatbotName, BaseChatbot]
    ) -> Attack:
        """Execute a single attack against all chatbots.

        Args:
            attack: Enhanced attack descriptor.
            chatbots: Dictionary of chatbots to test against.

        Returns:
            Attack results with responses and evaluations.
        """
        base_attack = attack.baseline_input
        techniques = attack.techniques
        attack_case = attack.attack_case
        attack_case.input = attack.enhanced_input
        bot_responses: dict[ChatbotName, str] = {}
        bot_responses_eval: dict[ChatbotName, ChatbotResponseEvaluation] = {}

        query_kwargs = self._build_query_kwargs(attack_case)

        for name, chatbot in chatbots.items():
            bot_responses_eval[name] = self._query_and_evaluate(
                chatbot, name, attack_case, query_kwargs, bot_responses
            )

        protection: Dict[str, Dict[ChatbotName, DetectionResult]] = self.guardrail_runner.run(
            attack_case.input,
            bot_responses
        )

        return Attack(
            self.category, self.subcategories, self.severity,
            PromptVariants(base_attack, attack_case.input),
            bot_responses_eval, protection, techniques
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
    def _get_metric(self, attack: RTTestCase) -> BaseRedTeamingMetric:
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

    @staticmethod
    def _build_query_kwargs(attack: RTTestCase) -> dict:
        """Build additional args for custom attack scenarios."""

        query_kwargs = {}
        if hasattr(attack, "is_rag") and attack.is_rag is not None:
            query_kwargs["is_rag"] = attack.is_rag
        if hasattr(attack, "file_path") and attack.file_path is not None:
            query_kwargs["file_path"] = attack.file_path
        if hasattr(attack, "system_prompt") and attack.system_prompt is not None:
            query_kwargs["system_prompt"] = attack.system_prompt
        return query_kwargs
