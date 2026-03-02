#  Copyright (c) 2026.
#  Florian Emanuel Sauer

from __future__ import annotations

import os
import uuid
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from time import perf_counter
from typing import Dict, List
from deepeval.models import DeepEvalBaseLLM
from deepteam.metrics import BaseRedTeamingMetric
from deepteam.test_case import RTTestCase
from deepteam.vulnerabilities import BaseVulnerability
from loguru import logger
from testframework.chatbots.base import BaseChatbot
from testframework.chatbots.store import ChatbotStore
from testframework.custom_attack_techniques import AttackListEnhancer
from testframework.enums import Category, ChatbotName, Severity
from testframework.guardrails.runner import GuardrailRunner
from testframework.metrics import ToolCallCodeInjectionMetric
from testframework.models import TestCaseResult, Attack, DetectionResult, PromptVariants, ChatbotResponseEvaluation, \
    TestErrorInfo, EnhancedAttack, ChatbotResponse, AttackEnhancementResult, LLMErrorType
from testframework.storage import save_test_case_result


class BaseTestCase(ABC):
    """Abstract base for all test cases."""

    results: TestCaseResult
    run_folder: Path | None = None
    simulator_model: DeepEvalBaseLLM | None | str = None  # = "gpt-3.5-turbo-0125"
    evaluation_model: DeepEvalBaseLLM | None | str = None  # "gpt-4o"

    def __init__(self,
                 category: Category,
                 subcategories: List[Enum],
                 severity: Severity = Severity.UNSAFE,
                 ) -> None:
        self.category = category
        self.subcategories = subcategories
        self.guardrail_runner = GuardrailRunner()
        self.attack_builder: BaseVulnerability | None = None
        self.severity = severity

    @abstractmethod
    def simulate_attacks(self, attacks_per_vulnerability_type: int = 1) -> List[RTTestCase]:
        """Simulate attacks for the test case."""
        raise NotImplementedError

    def execute(self) -> TestCaseResult:
        """Run the test case and return a mapping from attack_id to TestCaseResult.
            Build the attacks and add the techniques. Then execute the attacks on the guardrails.
        """
        test_case_id = self._test_case_identifier()
        attack_results: dict[str, Attack] = {}
        generation_error: TestErrorInfo | None = None
        enhancement_error: TestErrorInfo | None = None
        attack_list_enhancer: AttackListEnhancer = AttackListEnhancer(self.simulator_model)

        if self.attack_builder:
            attacks_per_vulnerability_type = int(os.environ.get("ATTACKS_PER_VULNERABILITY_TYPE", 1))
            enhanced_attacks: List[EnhancedAttack] = []
            enhancement_result: AttackEnhancementResult | None = None
            try:
                logger.info(f"Generating attacks for test case '{test_case_id}'")
                generation_started = perf_counter()
                attacks: List[RTTestCase] = self.simulate_attacks(
                    attacks_per_vulnerability_type=attacks_per_vulnerability_type)
                logger.info(
                    f"Generated {len(attacks)} attack(s) for '{test_case_id}' "
                    f"(duration={perf_counter() - generation_started:.2f}s)"
                )
                logger.info(f"Enhancing attacks for test case '{test_case_id}'")
                enhancement_started = perf_counter()
                enhancement_result = attack_list_enhancer.enhance(attacks)
                enhanced_attacks = enhancement_result.enhanced_attacks
                logger.info(
                    f"Prepared {len(enhanced_attacks)} enhanced attack(s) from {len(attacks)} "
                    f"base attack(s) for '{test_case_id}' "
                    f"(duration={perf_counter() - enhancement_started:.2f}s)"
                )
            except Exception as e:
                generation_error = TestErrorInfo.from_exception(e)
                logger.error(
                    f"Attack generation failed for {test_case_id} "
                    f"({generation_error.error_type.value}): {generation_error.message}"
                )

            executable_attacks = sum(1 for attack in enhanced_attacks if not attack.is_error)
            skipped_attacks = len(enhanced_attacks) - executable_attacks
            if not enhanced_attacks:
                logger.warning(f"No executable attacks generated for '{test_case_id}'")
            elif skipped_attacks:
                logger.warning(
                    f"Skipping {skipped_attacks} attack(s) for '{test_case_id}' "
                    f"because prompt enhancement failed"
                )

            skip_chatbot_execution = (
                    enhancement_result is not None
                    and enhancement_result.threshold_exceeded
            )
            if skip_chatbot_execution and enhancement_result is not None:
                enhancement_error = TestErrorInfo(
                    error_type=LLMErrorType.THRESHOLD_EXCEEDED,
                    message=(
                        "Skipped chatbot execution because the failed enhancement "
                        f"rate ({enhancement_result.invalid_percentage:.2f}%) exceeded "
                        f"the configured threshold "
                        f"({enhancement_result.error_threshold_percent:.2f}%)."
                    ),
                )
                logger.warning(
                    f"Stopping test case '{test_case_id}' before chatbot execution "
                    f"because the failed enhancement rate exceeded the configured "
                    f"threshold (failed={enhancement_result.failed_attack_count}, "
                    f"planned={enhancement_result.planned_attack_count}, "
                    f"error_rate={enhancement_result.invalid_percentage:.2f}%, "
                    f"threshold={enhancement_result.error_threshold_percent:.2f}%)"
                )
                if executable_attacks:
                    logger.warning(
                        f"Skipping {executable_attacks} otherwise executable attack(s) "
                        f"for '{test_case_id}' because the enhancement error threshold "
                        f"was exceeded"
                    )
            else:
                chatbots = ChatbotStore.get_chatbots()
                logger.info(
                    f"Executing {executable_attacks} attack(s) against {len(chatbots)} chatbot(s) "
                    f"for '{test_case_id}'"
                )

            total_attacks = len(enhanced_attacks)
            for counter, attack in enumerate(enhanced_attacks, start=1):
                techniques = ",".join(attack.techniques) if attack.techniques else "none"
                if attack.is_error:
                    attack_error = attack.error or TestErrorInfo.from_exception(
                        RuntimeError("Attack enhancement failed without error details")
                    )
                    logger.warning(
                        f"Skipping attack {counter}/{total_attacks} for '{test_case_id}' "
                        f"(techniques={techniques}, error_type={attack_error.error_type.value})"
                    )
                    attack_results[str(uuid.uuid4())] = Attack.from_enhancement_error(
                        self.category,
                        self.subcategories if self.subcategories else [],
                        self.severity,
                        attack.baseline_input,
                        attack.enhanced_input,
                        attack.techniques,
                        attack_error,
                    )
                    continue
                if skip_chatbot_execution:
                    continue

                logger.info(
                    f"Starting attack {counter}/{total_attacks} for '{test_case_id}' "
                    f"(techniques={techniques})"
                )
                attack_started = perf_counter()
                attack_result = self._execute_single_attack(attack, chatbots)
                attack_results[str(uuid.uuid4())] = attack_result
                logger.info(
                    f"Completed attack {counter}/{total_attacks} for '{test_case_id}' "
                    f"(duration={perf_counter() - attack_started:.2f}s)"
                )
        else:
            logger.warning(f"No attack builder configured for test case '{test_case_id}'")

        tc_result = TestCaseResult(
            category=self.category,
            subcategories=self.subcategories if self.subcategories else [],
            attacks=attack_results,
            generation_error=generation_error,
            enhancement_error=enhancement_error,
        )
        self.results = tc_result
        self.store_results()
        logger.info(
            f"Finished test case execution: {test_case_id} "
            f"(stored_attacks={len(attack_results)})"
        )
        return tc_result

    def _execute_single_attack(
            self,
            attack: EnhancedAttack,
            chatbots: Dict[ChatbotName, BaseChatbot]
    ) -> Attack:
        """Execute a single attack against all chatbots."""
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

        logger.info(
            f"Running guardrails for '{self._test_case_identifier()}' "
            f"(chatbots={len(bot_responses)})"
        )
        guardrails_started = perf_counter()
        protection: Dict[str, Dict[ChatbotName, DetectionResult]] = self.guardrail_runner.run(
            attack_case.input,
            bot_responses
        )
        logger.info(
            f"Completed guardrails for '{self._test_case_identifier()}' "
            f"(duration={perf_counter() - guardrails_started:.2f}s)"
        )

        return Attack(
            self.category, attack.attack_case.vulnerability_type, self.severity,
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
        """Query a chatbot and evaluate the response."""
        test_case_id = self._test_case_identifier()
        logger.info(f"Querying chatbot '{name.value}' for test case '{test_case_id}'")
        query_started = perf_counter()
        model_resp: ChatbotResponse = chatbot.query(attack.input, **query_kwargs)
        query_duration = perf_counter() - query_started
        llm_responses[name] = str(model_resp.response)

        if model_resp.is_error:
            logger.warning(
                f"Chatbot '{name.value}' query failed for '{test_case_id}' "
                f"(duration={query_duration:.2f}s, error_type={model_resp.error.error_type.value})"
            )
            return ChatbotResponseEvaluation.from_error(model_resp)

        logger.info(
            f"Chatbot '{name.value}' returned a response for '{test_case_id}' "
            f"(duration={query_duration:.2f}s)"
        )

        attack.actual_output = model_resp.response
        try:
            logger.info(
                f"Evaluating response from chatbot '{name.value}' for '{test_case_id}'"
            )
            evaluation_started = perf_counter()
            metric = self._find_metric(attack)
            if isinstance(metric, ToolCallCodeInjectionMetric):
                metric.measure(attack, model_resp.tool)
            else:
                metric.measure(attack)
            # todo: in the final evaluation, consider response evaluations with a score of -1 due to an error
            score = float(metric.score if not metric.error else -1)
            logger.info(
                f"Completed evaluation for chatbot '{name.value}' in '{test_case_id}' "
                f"(score={score}, duration={perf_counter() - evaluation_started:.2f}s)"
            )
            return ChatbotResponseEvaluation(
                model_resp,
                score,
                str(metric.reason),
                metric.is_successful(),
            )
        except Exception as e:
            eval_error = TestErrorInfo.from_exception(e)
            logger.error(
                f"Metric evaluation failed for '{name.value}' in '{test_case_id}' "
                f"({eval_error.error_type.value}): {eval_error.message}"
            )
            return ChatbotResponseEvaluation.from_error(model_resp, eval_error)

    def _find_metric(self, attack: RTTestCase) -> BaseRedTeamingMetric:
        metadata = getattr(attack, "metadata", None)
        if isinstance(metadata, dict) and metadata.get("tool_check") is True:
            return ToolCallCodeInjectionMetric(model=self.evaluation_model)
        return self._get_metric(attack)

    @abstractmethod
    def _get_metric(self, attack: RTTestCase) -> BaseRedTeamingMetric:
        """Return the metric to evaluate the attack."""
        raise NotImplementedError

    def store_results(self) -> Path | None:
        """Store the test case results as a backup to the run folder."""
        if self.run_folder is None:
            return None
        return save_test_case_result(self.results, self.run_folder)

    @staticmethod
    def _build_query_kwargs(attack: RTTestCase) -> dict:
        """Build additional args for custom attack scenarios."""

        query_kwargs = {}
        if attack.metadata is not None:
            if "file_path" in attack.metadata:
                query_kwargs["file_path"] = attack.metadata.get("file_path")
            if "is_rag" in attack.metadata:
                query_kwargs["is_rag"] = attack.metadata.get("is_rag")

        return query_kwargs

    def _test_case_identifier(self) -> str:
        """Build a readable identifier for the current test case."""
        if not self.subcategories:
            return self.category.value

        subcategories = ";".join(str(subcat.value) for subcat in self.subcategories)
        return f"{self.category.value}_{subcategories}"
