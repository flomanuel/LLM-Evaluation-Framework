from collections import deque
from time import monotonic, sleep
from typing import List
from loguru import logger
from testframework import ChatbotName
from testframework.guardrails.base import BaseGuardrail
from testframework.models import DetectionElement
from guardrails import Guard, Validator, ValidationOutcome, OnFailAction
from guardrails.hub import ToxicLanguage, BiasCheck, GuardrailsPII, SensitiveTopic, ShieldGemma2B, LlamaGuard7B, \
    DetectJailbreak
from topics import SENSITIVE_TOPICS


class GuardrailsAI():
    PII_ENTITIES_MAP = {
        "pii": [
            "EMAIL_ADDRESS",
            "PHONE_NUMBER",
            "IP_ADDRESS",
        ],
        "spi": [
            "CREDIT_CARD",
            "CRYPTO",
            "IBAN_CODE",
            "NRP",
        ],
    }

    def __init__(self) -> None:
        self._guard = None
        self.name = "DELETE ME"

    def eval_attack(self, user_prompt: str, attack_description: str, **kwargs) -> DetectionElement:
        guard = self._get_guard
        try:
            res: ValidationOutcome = self._get_guard.parse(user_prompt)
        except Exception as e:
            # todo: exception handling -> API might sometimes be flaky
            pass
        return DetectionElement.from_error()

    def eval_model_response(self, model_response: str, chatbot: ChatbotName, attack_description: str,
                            **kwargs) -> DetectionElement:
        try:
            res: ValidationOutcome = self._get_guard.parse(model_response)
        except Exception as e:
            # todo: exception handling -> API might sometimes be flaky
            pass
        return DetectionElement.from_error()

    @property
    def _get_guard(self) -> Guard:
        if self._guard is None:
            validators = self._validators
            self._guard = Guard().use(validators=validators)
        return self._guard

    @property
    def _validators(self) -> List[Validator]:
        return [
            SensitiveTopic(
                sensitive_topics=SENSITIVE_TOPICS,
                model="dslim/bert-base-NER",
                disable_classifier=False,
                disable_llm=True,
                on_fail=OnFailAction.EXCEPTION,
                device=1
            ),
            DetectJailbreak(
                device="mps",
                on_fail=OnFailAction.EXCEPTION,
            ),
            ToxicLanguage(
                validation_method="full",
                on_fail=OnFailAction.EXCEPTION,
            ),
            BiasCheck(
                on_fail=OnFailAction.EXCEPTION,
            ),
            GuardrailsPII(
                entities=self.PII_ENTITIES_MAP,
                model_name="urchade/gliner_small-v2.1",
                on_fail=OnFailAction.EXCEPTION,
            ),
            ShieldGemma2B(
                # only one policy supported at a time, according to https://guardrailsai.com/hub/validator/guardrails/shieldgemma_2b
                policies=[ShieldGemma2B.POLICY__NO_DANGEROUS_CONTENT],
                on_fail=OnFailAction.EXCEPTION
            ),
            LlamaGuard7B(
                policies=[LlamaGuard7B.POLICY__NO_VIOLENCE_HATE,
                          LlamaGuard7B.POLICY__NO_SEXUAL_CONTENT,
                          LlamaGuard7B.POLICY__NO_CRIMINAL_PLANNING,
                          LlamaGuard7B.POLICY__NO_GUNS_AND_ILLEGAL_WEAPONS,
                          LlamaGuard7B.POLICY__NO_ILLEGAL_DRUGS,
                          LlamaGuard7B.POLICY__NO_ENOURAGE_SELF_HARM],
                on_fail=OnFailAction.EXCEPTION
            )
        ]


def main():
    gai = GuardrailsAI()
    gai.eval_attack("I'm harmles!", "")
    gai.eval_attack("You suck! Bastard! Fuck you!", "")


if __name__ == "__main__":
    main()
