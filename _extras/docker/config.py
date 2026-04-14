#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

from typing import Any, Callable, Dict, List, Optional, Union
from guardrails import Guard, OnFailAction
from guardrails.hub import (
    BiasCheck,
    DetectJailbreak,
    GuardrailsPII,
    LlamaGuard7B,
    ShieldGemma2B,
    ToxicLanguage,
    RestrictToTopic
)
from guardrails.validator_base import (
    FailResult,
    PassResult,
    ValidationResult,
    register_validator,
)


# bsed on: https://github.com/guardrails-ai/sensitive_topics/blob/main/validator/main.py
# manual re-implementation due to a bug in the original scanner (uses old version of another scanner which changed its API)
@register_validator(name="guardrails/sensitive_topics", data_type="string")
class SensitiveTopic(RestrictToTopic):  # type: ignore
    def __init__(
            self,
            sensitive_topics: Optional[List[str]] = [],
            device: Optional[int] = -1,
            model: Optional[str] = "facebook/bart-large-mnli",
            llm_callable: Union[str, Callable, None] = None,
            disable_classifier: Optional[bool] = False,
            classifier_api_endpoint: Optional[str] = None,
            disable_llm: Optional[bool] = False,
            on_fail: Optional[Callable[..., Any]] = None,
            zero_shot_threshold: Optional[float] = 0.5,
            llm_threshold: Optional[int] = 3,
    ):
        if sensitive_topics is None:
            sensitive_topics = SENSITIVE_TOPICS
        super().__init__(
            [],
            invalid_topics=sensitive_topics,
            device=device,
            model=model,
            disable_classifier=disable_classifier,
            classifier_api_endpoint=classifier_api_endpoint,
            disable_llm=disable_llm,
            llm_callable=llm_callable,
            on_fail=on_fail,
            zero_shot_threshold=zero_shot_threshold,
            llm_threshold=llm_threshold,
        )

    def get_args(self) -> Dict[str, Any]:
        # Overriding grandparent's get_args to avoid unnecessary arguments
        return {
            "sensitive_topics": self._kwargs.get("invalid_topics", None),
            "device": self._kwargs.get("device", -1),
            "model": self._kwargs.get("model", "facebook/bart-large-mnli"),
            "llm_callable": self._kwargs.get("llm_callable", None),
            "disable_classifier": self._kwargs.get("disable_classifier", False),
            "disable_llm": self._kwargs.get("disable_llm", False),
            "model_threshold": self._kwargs.get("model_threshold", 0.5),
        }

    def validate(
            self, value: str, metadata: Optional[Dict[str, Any]] = {}
    ) -> ValidationResult:
        invalid_topics = list(set(self._invalid_topics))
        if not invalid_topics:
            raise ValueError("A set of invalid topics must be provided.")

        # LLM Classifier Only
        elif self._disable_classifier and not self._disable_llm:
            found_topics = self.get_topics_llm(value, invalid_topics)
        # Zero Shot Classifier Only
        elif not self._disable_classifier and self._disable_llm:
            found_topics = self.get_topics_ensemble(value, invalid_topics)
        else:
            raise ValueError("Either classifier or llm must be enabled.")
        invalid_topics_found = [
            topic for topic in found_topics if topic in self._invalid_topics
        ]
        if invalid_topics_found:
            return FailResult(
                error_message=f"Invalid topics found: {invalid_topics_found}"
            )

        return PassResult()


SENSITIVE_TOPICS = [
    "violence",
    "sexual harassment or unwanted touching",
    "sensitive information like maternity leaves or layoffs",
    "role changes",
    "authority changes",
    "request for or change of system instructions",
    "weapons",
    "illegal activities",
    "employee information",
    "fraud",
    "crime",
    "drugs",
    "drug production",
    "cybercrime",
]

PII_ENTITIES_MAP = {
    "CREDIT_CARD",
    "CRYPTO",
    "IBAN_CODE",
    "US_BANK_NUMBER",
    "US_ITIN",
    "US_SSN",
    "EMAIL_ADDRESS",
    "IP_ADDRESS",
    "LOCATION",
    "PERSON",
    "PHONE_NUMBER",
}

sensitive_topic_validator = SensitiveTopic(
    sensitive_topics=SENSITIVE_TOPICS,
    # model="dslim/bert-base-NER",
    disable_classifier=False,
    disable_llm=True,
    on_fail=OnFailAction.EXCEPTION,
)

detect_jailbreak_validator = DetectJailbreak(
    on_fail=OnFailAction.EXCEPTION,
)

toxic_language_validator = ToxicLanguage(
    validation_method="full",
    on_fail=OnFailAction.EXCEPTION,
)

bias_check_validator = BiasCheck(
    on_fail=OnFailAction.EXCEPTION,
)

pii_validator = GuardrailsPII(
    entities=PII_ENTITIES_MAP,
    model_name="urchade/gliner_small-v2.1",
    on_fail=OnFailAction.EXCEPTION,
)

shieldgemma_2b_no_dangerous_content_validator = ShieldGemma2B(
    # only one policy supported at a time, according to https://guardrailsai.com/hub/validator/guardrails/shieldgemma_2b
    policies=[ShieldGemma2B.POLICY__NO_DANGEROUS_CONTENT],
    on_fail=OnFailAction.EXCEPTION,
)

shieldgemma_2b_no_harassment_validator = ShieldGemma2B(
    policies=[ShieldGemma2B.POLICY__NO_HARASSMENT],
    on_fail=OnFailAction.EXCEPTION,
)

shieldgemma_2b_no_hate_speech_validator = ShieldGemma2B(
    policies=[ShieldGemma2B.POLICY__NO_HATE_SPEECH],
    on_fail=OnFailAction.EXCEPTION,
)

shieldgemma_2b_no_sexual_content_validator = ShieldGemma2B(
    policies=[ShieldGemma2B.POLICY__NO_SEXUAL_CONTENT],
    on_fail=OnFailAction.EXCEPTION,
)

llamaguard_7b_validator = LlamaGuard7B(
    policies=[
        LlamaGuard7B.POLICY__NO_VIOLENCE_HATE,
        LlamaGuard7B.POLICY__NO_SEXUAL_CONTENT,
        LlamaGuard7B.POLICY__NO_CRIMINAL_PLANNING,
        LlamaGuard7B.POLICY__NO_GUNS_AND_ILLEGAL_WEAPONS,
        LlamaGuard7B.POLICY__NO_ILLEGAL_DRUGS,
        LlamaGuard7B.POLICY__NO_ENOURAGE_SELF_HARM,
    ],
    on_fail=OnFailAction.EXCEPTION,
)

thesis_guard_sensitive_topic = Guard(name="thesis_guard_sensitive_topic")
thesis_guard_sensitive_topic.use(validators=[sensitive_topic_validator])

thesis_guard_detect_jailbreak = Guard(name="thesis_guard_detect_jailbreak")
thesis_guard_detect_jailbreak.use(validators=[detect_jailbreak_validator])

thesis_guard_toxic_language = Guard(name="thesis_guard_toxic_language")
thesis_guard_toxic_language.use(validators=[toxic_language_validator])

thesis_guard_bias_check = Guard(name="thesis_guard_bias_check")
thesis_guard_bias_check.use(validators=[bias_check_validator])

thesis_guard_pii = Guard(name="thesis_guard_pii")
thesis_guard_pii.use(validators=[pii_validator])

thesis_guard_shieldgemma_2b_no_dangerous_content = Guard(
    name="thesis_guard_shieldgemma_2b_no_dangerous_content"
)
thesis_guard_shieldgemma_2b_no_dangerous_content.use(
    validators=[shieldgemma_2b_no_dangerous_content_validator]
)

thesis_guard_shieldgemma_2b_no_harassment = Guard(
    name="thesis_guard_shieldgemma_2b_no_harassment"
)
thesis_guard_shieldgemma_2b_no_harassment.use(
    validators=[shieldgemma_2b_no_harassment_validator]
)

thesis_guard_shieldgemma_2b_no_hate_speech = Guard(
    name="thesis_guard_shieldgemma_2b_no_hate_speech"
)
thesis_guard_shieldgemma_2b_no_hate_speech.use(
    validators=[shieldgemma_2b_no_hate_speech_validator]
)

thesis_guard_shieldgemma_2b_no_sexual_content = Guard(
    name="thesis_guard_shieldgemma_2b_no_sexual_content"
)
thesis_guard_shieldgemma_2b_no_sexual_content.use(
    validators=[shieldgemma_2b_no_sexual_content_validator]
)

thesis_guard_llamaguard_7b = Guard(name="thesis_guard_llamaguard_7b")
thesis_guard_llamaguard_7b.use(validators=[llamaguard_7b_validator])
