#  Copyright (c) 2026.
#  Florian Emanuel Sauer

from __future__ import annotations
from time import perf_counter
from typing import Dict

from deepteam.metrics import BaseRedTeamingMetric
from deepteam.test_case import RTTestCase
from loguru import logger
from testframework import ChatbotName
from testframework.models import DetectionResult, DetectionElement, TestErrorInfo, ChatbotResponseEvaluation, RagContext
from testframework.metrics import ToolCallCodeInjectionMetric
from testframework.guardrails.llm_guard import LLMGuard
from testframework.guardrails.prompt_hardening import PromptHardeningGuardrail


class GuardrailRunner:
    """Runs configured guardrails over custom_attacks and model responses."""

    def __init__(self) -> None:
        self.guardrails = [
            LLMGuard(),
            PromptHardeningGuardrail(),
        ]

    def run(
            self,
            attack: RTTestCase,
            chatbot_responses_eval: dict[ChatbotName, ChatbotResponseEvaluation],
            metric: BaseRedTeamingMetric,
            attack_description: str,
    ) -> Dict[str, Dict[ChatbotName, DetectionResult]]:
        """
        Analyzes a given attack string against the chatbot's responses by iterating over the guardrails.
        """
        result: Dict[str, Dict[ChatbotName, DetectionResult]] = {}
        logger.info(
            f"Running {len(self.guardrails)} guardrail(s) "
            f"for {len(chatbot_responses_eval)} chatbot response(s)"
        )
        for guardrail in self.guardrails:
            key: str = guardrail.name
            result[key] = {}
            guardrail_started = perf_counter()
            logger.info(f"Starting guardrail '{guardrail.name}'")

            use_tool_trace = isinstance(metric, ToolCallCodeInjectionMetric)

            for bot_name, bot_response_eval in chatbot_responses_eval.items():
                full_attack = bot_response_eval.chatbot_response.raw_prompt
                tool_info = bot_response_eval.chatbot_response.tool if use_tool_trace else None
                enhanced_attack_evaluation = self._safe_eval_attack(
                    guardrail,
                    # todo: decide whether to use `enhanced_attack` (attack + technique) or full_attack (attack + technique + RAG/Documents -> no system prompt)
                    # `full_attack` is exactly the prompt that the chatbot got (except for the system prompt, but that one can't be controlled by the user so this is fine)
                    # So it makes sense to also use this prompt on the guardrails, e.g. because of indirect prompt injections.
                    full_attack,
                    attack_description,
                    tool_info=tool_info,
                )
                if isinstance(guardrail, PromptHardeningGuardrail):
                    file_path: str | None = bot_response_eval.chatbot_response.file_path or None
                    # Build the prompt with the same RAG context to keep all conditions the same. If a file path is set, then no RAG will be used in the chatbot and since the file is
                    # always the same, the conditions stay the same for file paths, as opposed to RAG.
                    rag_context: RagContext | None = bot_response_eval.chatbot_response.rag_context
                    response_evaluation = self._safe_eval_response(guardrail,
                                                                   attack.input,
                                                                   bot_name,
                                                                   attack_description,
                                                                   file_path=file_path,
                                                                   rag_context=rag_context,
                                                                   metric=metric)
                else:
                    response_evaluation = self._safe_eval_response(guardrail,
                                                                   bot_response_eval.chatbot_response.response,
                                                                   bot_name,
                                                                   attack_description,
                                                                   prompt=full_attack,
                                                                   tool_info=tool_info)
                result[key][bot_name] = DetectionResult(
                    enhanced_attack_evaluation, response_evaluation
                )
            logger.info(
                f"Completed guardrail '{guardrail.name}' "
                f"(duration={perf_counter() - guardrail_started:.2f}s)"
            )
        logger.info("Guardrail evaluation completed")
        return result

    def _safe_eval_attack(self, guardrail, attack: str, attack_description, **kwargs) -> DetectionElement:
        """Evaluate an attack, catching any errors.
        """
        try:
            return guardrail.eval_attack(attack, attack_description, **kwargs)
        except Exception as e:
            error = TestErrorInfo.from_exception(e)
            logger.error(
                f"Guardrail '{guardrail.name}' attack evaluation failed "
                f"({error.error_type.value}): {error.message}"
            )
            return DetectionElement.from_error(error)

    def _safe_eval_response(self, guardrail, response: str, chatbot: ChatbotName, attack_description: str,
                            **kwargs) -> DetectionElement:
        # file_path: st`r | None, rag: RagContext | None) -> DetectionElement:
        """Evaluate a response, catching any errors.
        """
        try:
            return guardrail.eval_model_response(response, chatbot, attack_description, **kwargs)
        except Exception as e:
            error = TestErrorInfo.from_exception(e)
            logger.error(
                f"Guardrail '{guardrail.name}' response evaluation failed "
                f"({error.error_type.value}): {error.message}"
            )
            return DetectionElement.from_error(error)
