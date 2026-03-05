#  Copyright (c) 2026.
#  Florian Emanuel Sauer
from typing import List

from guardrails_grhub_llamaguard_7b import LlamaGuard7B
from guardrails_grhub_shieldgemma_2b import ShieldGemma2B

from testframework import ChatbotName
from testframework.guardrails.base import BaseGuardrail
from testframework.models import DetectionElement
from guardrails import Guard, Validator, ValidationOutcome, install, OnFailAction


class GuardrailsAI(BaseGuardrail):
    """Guardrail for GuardrailsAI from [GuardrailsAI](https://guardrailsai.com/)."""

    def __init__(self) -> None:
        super().__init__("Guardrails AI")
        self._guard = Guard().use(validators=self.validators)

    sensitive_topic = install(
        "hub://guardrails/sensitive_topics",
        quiet=False
    ).SensitiveTopic

    detect_jailbreak = install(
        "hub://guardrails/detect_jailbreak",
        quiet=False
    ).DetectJailbreak

    toxic_language = install(
        "hub://guardrails/toxic_language",
        quiet=False
    ).ToxicLanguage

    bias_check = install(
        "hub://guardrails/bias_check",
        quiet=False
    ).BiasCheck

    guardrails_pii = install(
        "hub://guardrails/guardrails_pii",
        quiet=False
    ).GuardrailsPII

    shield_gemma_2b = install(
        "hub://guardrails/shieldgemma_2b",
        quiet=False
    ).ShieldGemma2B

    llama_guard_7b = install(
        "hub://guardrails/llamaguard_7b",
        quiet=False
    ).LlamaGuard7B

    def eval_attack(self, user_prompt: str, attack_description: str, **kwargs) -> DetectionElement:
        self._check_request_allowed()
        try:
            res: ValidationOutcome = self._guard.parse(user_prompt)
        except Exception as e:
            # todo: exception handling -> API might sometimes be flaky
            pass

        return None

    def eval_model_response(self, model_response: str, chatbot: ChatbotName, attack_description: str,
                            **kwargs) -> DetectionElement:
        self._check_request_allowed()
        try:
            res: ValidationOutcome = self._guard.parse(model_response)
        except Exception as e:
            # todo: exception handling -> API might sometimes be flaky
            pass
        return None

    @property
    def validators(self) -> List[Validator]:
        return [
            self.sensitive_topic(
                sensitive_topics=["TBD"],
                model="facebook/bart-large-mnli",
                disable_classifier=False,
                disable_llm=True,
                on_fail=OnFailAction.EXCEPTION,
            ),
            self.detect_jailbreak(
                device="mps",
                on_fail=OnFailAction.EXCEPTION,
            ),
            self.toxic_language(
                validation_method="full",
                on_fail=OnFailAction.EXCEPTION,
            ),
            self.bias_check(
                on_fail=OnFailAction.EXCEPTION,
            ),
            self.guardrails_pii(
                entities=["entities"],
                model_name="urchade/gliner_small-v2.1",
                on_fail=OnFailAction.EXCEPTION,
            ),
            self.shield_gemma_2b(
                # only one policy supported at a time, according to https://guardrailsai.com/hub/validator/guardrails/shieldgemma_2b
                policies=[ShieldGemma2B.POLICY__NO_DANGEROUS_CONTENT],
                on_fail=OnFailAction.EXCEPTION
            ),
            self.llama_guard_7b(
                # applies all given policies if not defined:
                policies=[LlamaGuard7B.POLICY__NO_VIOLENCE_HATE,
                          LlamaGuard7B.POLICY__NO_SEXUAL_CONTENT,
                          LlamaGuard7B.POLICY__NO_CRIMINAL_PLANNING,
                          LlamaGuard7B.POLICY__NO_GUNS_AND_ILLEGAL_WEAPONS,
                          LlamaGuard7B.POLICY__NO_ILLEGAL_DRUGS,
                          LlamaGuard7B.POLICY__NO_ENOURAGE_SELF_HARM],
                on_fail=OnFailAction.EXCEPTION
            )
        ]

    def _check_request_allowed(self):
        """Check if the guardrail is allowed to make a request due to rate limits."""
        # limits: 100 requests per minute, 500 in total for 5 minutes. Every scanner (e.g., bias_check counts as one request)
        pass
