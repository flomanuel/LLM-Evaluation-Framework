from __future__ import annotations

from typing import Dict
from .. import Chatbot
from ..models import DetectionResult, DetectionElement
from .prompt_hardening import PromptHardeningGuardrail


class GuardrailRunner:
    """Runs configured guardrails over custom_attacks and model responses."""

    def __init__(self) -> None:
        self.guardrails = [
            PromptHardeningGuardrail()
        ]

    def run(
            self,
            enhanced_attack: str,
            chatbot_responses: Dict[Chatbot, str]
    ) -> Dict[str, Dict[Chatbot, DetectionResult]]:
        """
        Analyzes a given attack string against the chatbot's responses by iterating over the guardrails.

        :param chatbot_responses: The responses for each chatbot in the test case (Chatbot-ID -> Response).
        :param enhanced_attack: The adversarial attack (RAG + attack + attack technique)
        :return: A `DetectionResult` object encapsulating the details of detected
            vulnerabilities and relevant metadata of the analysis.
        """
        result: Dict[str, Dict[Chatbot, DetectionResult]] = {}
        for guardrail in self.guardrails:
            key: str = guardrail.name
            enhanced_attack_evaluation: DetectionElement = guardrail.eval_attack(enhanced_attack)
            for chatbot, response in chatbot_responses.items():
                response_evaluation: DetectionElement = guardrail.eval_model_response(response)
                result[key][chatbot] = DetectionResult(enhanced_attack_evaluation, response_evaluation)
        return result
