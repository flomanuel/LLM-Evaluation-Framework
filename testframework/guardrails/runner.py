from __future__ import annotations
from typing import Dict
from loguru import logger
from testframework import ChatbotName
from testframework.models import DetectionResult, DetectionElement, TestErrorInfo
from testframework.guardrails.prompt_hardening import PromptHardeningGuardrail


class GuardrailRunner:
    """Runs configured guardrails over custom_attacks and model responses."""

    def __init__(self) -> None:
        self.guardrails = [
            PromptHardeningGuardrail()
        ]

    def run(
            self,
            enhanced_attack: str,
            chatbot_responses: Dict[ChatbotName, str]
    ) -> Dict[str, Dict[ChatbotName, DetectionResult]]:
        """
        Analyzes a given attack string against the chatbot's responses by iterating over the guardrails.

        :param chatbot_responses: The responses for each chatbot in the test case (Chatbot-ID -> Response).
        :param enhanced_attack: The adversarial attack (attack and attack technique)
        :return: A `DetectionResult` object encapsulating the details of detected
            vulnerabilities and relevant metadata of the analysis.
        """
        result: Dict[str, Dict[ChatbotName, DetectionResult]] = {}
        for guardrail in self.guardrails:
            key: str = guardrail.name
            result[key] = {}

            enhanced_attack_evaluation = self._safe_eval_attack(guardrail, enhanced_attack)

            for chatbot, response in chatbot_responses.items():
                if isinstance(guardrail, PromptHardeningGuardrail):
                    response_evaluation = self._safe_eval_response(guardrail, enhanced_attack, chatbot)
                else:
                    response_evaluation = self._safe_eval_response(guardrail, response, chatbot)
                result[key][chatbot] = DetectionResult(
                    enhanced_attack_evaluation, response_evaluation
                )
        return result

    def _safe_eval_attack(self, guardrail, attack: str) -> DetectionElement:
        """Evaluate an attack, catching any errors.

        Args:
            guardrail: The guardrail to use for evaluation.
            attack: The attack string to evaluate.

        Returns:
            DetectionElement with results or error info.
        """
        try:
            return guardrail.eval_attack(attack)
        except Exception as e:
            error = TestErrorInfo.from_exception(e)
            logger.exception(
                f"Guardrail '{guardrail.name}' attack evaluation failed "
                f"({error.error_type.value}): {error.message}"
            )
            return DetectionElement.from_error(error)

    def _safe_eval_response(self, guardrail, response: str, chatbot: ChatbotName) -> DetectionElement:
        """Evaluate a response, catching any errors.

        Args:
            guardrail: The guardrail to use for evaluation.
            response: The response string to evaluate.

        Returns:
            DetectionElement with results or error info.
        """
        try:
            return guardrail.eval_model_response(response, chatbot)
        except Exception as e:
            error = TestErrorInfo.from_exception(e)
            logger.exception(
                f"Guardrail '{guardrail.name}' response evaluation failed "
                f"({error.error_type.value}): {error.message}"
            )
            return DetectionElement.from_error(error)
