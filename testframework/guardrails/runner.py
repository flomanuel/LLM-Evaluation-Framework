#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.


from time import perf_counter

from loguru import logger
from testframework import ChatbotName
from testframework.guardrails.gcp_model_armor.gcp_model_armor import GcpModelArmor
from testframework.guardrails.llama_firewall.llama_firewall import LlamaFirewall
from testframework.models import DetectionResult, DetectionElement, TestErrorInfo, ChatbotResponseEvaluation, RagContext
from testframework.metrics import ToolCallCodeInjectionMetric
from testframework.guardrails.llm_guard import LLMGuard
from testframework.guardrails.lakera_guard import LakeraGuard
from testframework.guardrails.prompt_hardening import PromptHardeningGuardrail
from testframework.redteam.metric_protocol import RedTeamingMetric
from testframework.redteam.test_case import RTTestCase


class GuardrailRunner:
    """Runs configured guardrails over custom_attacks and model responses."""

    def __init__(self) -> None:
        self.guardrails = [
            PromptHardeningGuardrail(),
            LLMGuard(),
            LlamaFirewall(),
            LakeraGuard(),
            GcpModelArmor(),
        ]

    def run(
            self,
            attack: RTTestCase,
            chatbot_responses_eval: dict[ChatbotName, ChatbotResponseEvaluation],
            metric: RedTeamingMetric,
    ) -> dict[str, dict[ChatbotName, DetectionResult]]:
        """Analyzes a given attack string against the chatbot's responses by iterating over the guardrails."""
        result: dict[str, dict[ChatbotName, DetectionResult]] = {}
        logger.info(
            "Running {} guardrail(s) for {} chatbot response(s)",
            len(self.guardrails),
            len(chatbot_responses_eval),
        )
        for guardrail in self.guardrails:
            key: str = guardrail.name
            result[key] = {}
            guardrail_started = perf_counter()
            logger.info("Starting guardrail '{}'", guardrail.name)

            use_tool_trace = isinstance(metric, ToolCallCodeInjectionMetric)

            for bot_name, bot_response_eval in chatbot_responses_eval.items():
                if bot_response_eval.chatbot_response.is_error:
                    logger.info(
                        "Skipping guardrail '{}' for chatbot '{}' because the chatbot query failed",
                        guardrail.name,
                        bot_name.value,
                    )
                    result[key][bot_name] = self._skipped_detection_result(bot_response_eval)
                    continue

                full_attack = bot_response_eval.chatbot_response.raw_prompt
                tool_info = bot_response_eval.chatbot_response.tool if use_tool_trace else None
                enhanced_attack_evaluation = self._safe_eval_attack(
                    guardrail,
                    # todo: decide whether to use `enhanced_attack` (attack + technique) or full_attack (attack + technique + RAG/Documents -> no system prompt)
                    # `full_attack` is exactly the prompt that the chatbot got (except for the system prompt, but that one can't be controlled by the user so this is fine)
                    # Thus, it makes sense to also use this prompt on the guardrails, e.g. because of indirect prompt injections.
                    full_attack,
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
                                                                   file_path=file_path,
                                                                   rag_context=rag_context,
                                                                   metric=metric)
                else:
                    response_evaluation = self._safe_eval_response(guardrail,
                                                                   bot_response_eval.chatbot_response.response,
                                                                   bot_name,
                                                                   prompt=full_attack,
                                                                   tool_info=tool_info)
                result[key][bot_name] = DetectionResult(
                    input_detection=enhanced_attack_evaluation,
                    output_detection=response_evaluation,
                )
            logger.opt(lazy=True).info(
                "Completed guardrail '{}' (duration={:.2f}s)",
                lambda guardrail_name=guardrail.name: guardrail_name,
                lambda started=guardrail_started: perf_counter() - started,
            )
        logger.info("Guardrail evaluation completed")
        return result

    @staticmethod
    def _skipped_detection_result(
            bot_response_eval: ChatbotResponseEvaluation,
    ) -> DetectionResult:
        """Return an error detection result when the chatbot query failed."""
        res_error = bot_response_eval.chatbot_response.error or bot_response_eval.error
        if res_error is None:
            res_error = TestErrorInfo.from_exception(
                RuntimeError("Chatbot query failed without error details")
            )

        error = TestErrorInfo(
            error_type=res_error.error_type,
            message=f"Skipped guardrail evaluation because chatbot query failed: {res_error.message}",
        )
        skipped_detection = DetectionElement.from_error(error)
        return DetectionResult(
            input_detection=skipped_detection,
            output_detection=skipped_detection,
        )

    def _safe_eval_attack(self, guardrail, attack: str, **kwargs) -> DetectionElement:
        """Evaluate an attack, catching any errors."""
        try:
            return guardrail.eval_attack(attack, **kwargs)
        except Exception as e:
            error = TestErrorInfo.from_exception(e)
            logger.error(
                "Guardrail '{}' attack evaluation failed ({}): {}",
                guardrail.name,
                error.error_type.value,
                error.message,
            )
            return DetectionElement.from_error(error)

    def _safe_eval_response(self, guardrail, response: str, chatbot: ChatbotName, **kwargs) -> DetectionElement:
        """Evaluate a response, catching any errors."""
        try:
            return guardrail.eval_model_response(response, chatbot, **kwargs)
        except Exception as e:
            error = TestErrorInfo.from_exception(e)
            logger.error(
                "Guardrail '{}' response evaluation failed ({}): {}",
                guardrail.name,
                error.error_type.value,
                error.message,
            )
            return DetectionElement.from_error(error)
