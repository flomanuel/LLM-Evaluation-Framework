#  Copyright (c) 2026.
#  Florian Emanuel Sauer

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from time import perf_counter
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
    TestErrorInfo, EnhancedAttack, ChatbotResponse
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
            # todo: das große modell verwenden
            model="llama2-uncensored",
            generation_kwargs={
                "timeout": effective_timeout,
            }
        )
        self.evaluation_model = "gpt-4o"

    def execute(self) -> TestCaseResult:
        """Run the test case and return a mapping from attack_id to TestCaseResult.
            Build the attacks and add the techniques. Then execute the attacks on the guardrails.
        """
        test_case_id = self._test_case_identifier()
        attack_results: dict[str, Attack] = {}
        generation_error: TestErrorInfo | None = None
        attack_list_enhancer: AttackListEnhancer = AttackListEnhancer(self.simulator_model)
        logger.info(f"Starting test case execution: {test_case_id}")

        if self.attack_builder:
            enhanced_attacks: List[EnhancedAttack] = []
            try:
                logger.info(f"Generating attacks for test case '{test_case_id}'")
                generation_started = perf_counter()
                attacks: List[RTTestCase] = self.attack_builder.simulate_attacks()
                logger.info(
                    f"Generated {len(attacks)} attack(s) for '{test_case_id}' "
                    f"(duration={perf_counter() - generation_started:.2f}s)"
                )
                logger.info(f"Enhancing attacks for test case '{test_case_id}'")
                enhancement_started = perf_counter()
                enhanced_attacks = attack_list_enhancer.enhance(attacks)
                logger.info(
                    f"Prepared {len(enhanced_attacks)} executable attack(s) from {len(attacks)} "
                    f"base attack(s) for '{test_case_id}' "
                    f"(duration={perf_counter() - enhancement_started:.2f}s)"
                )
            except Exception as e:
                generation_error = TestErrorInfo.from_exception(e)
                logger.exception(
                    f"Attack generation failed for {test_case_id} "
                    f"({generation_error.error_type.value}): {generation_error.message}"
                )

            chatbots: Dict[ChatbotName, BaseChatbot] = ChatbotStore.get_chatbots()
            executable_attacks = sum(1 for attack in enhanced_attacks if not attack.is_error)
            skipped_attacks = len(enhanced_attacks) - executable_attacks
            logger.info(
                f"Executing {executable_attacks} attack(s) against {len(chatbots)} chatbot(s) "
                f"for '{test_case_id}'"
            )
            if not enhanced_attacks:
                logger.warning(f"No executable attacks generated for '{test_case_id}'")
            elif skipped_attacks:
                logger.warning(
                    f"Skipping {skipped_attacks} attack(s) for '{test_case_id}' "
                    f"because prompt enhancement failed"
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
            self.category,
            self.subcategories if self.subcategories else [],
            attack_results,
            generation_error
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
            metric = self._get_metric(attack)
            metric.measure(attack)
            score = float(metric.score if metric.is_successful() else -1)
            logger.info(
                f"Completed evaluation for chatbot '{name.value}' in '{test_case_id}' "
                f"(score={score}, duration={perf_counter() - evaluation_started:.2f}s)"
            )
            return ChatbotResponseEvaluation(
                model_resp,
                # todo: in the final evaluation, consider response evaluations with a score of -1 due to an error
                score,
                str(metric.reason)
            )
        except Exception as e:
            eval_error = TestErrorInfo.from_exception(e)
            logger.exception(
                f"Metric evaluation failed for '{name.value}' in '{test_case_id}' "
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

    def _test_case_identifier(self) -> str:
        """Build a readable identifier for the current test case."""
        if not self.subcategories:
            return self.category.value

        subcategories = ";".join(str(subcat.value) for subcat in self.subcategories)
        return f"{self.category.value}_{subcategories}"
