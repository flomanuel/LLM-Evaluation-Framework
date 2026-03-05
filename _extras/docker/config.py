from guardrails import Guard, Validator, ValidationOutcome, OnFailAction
from guardrails.hub import ToxicLanguage, BiasCheck, GuardrailsPII, SensitiveTopic, ShieldGemma2B, LlamaGuard7B, \
    DetectJailbreak

SENSITIVE_TOPICS = [
    "being ridiculed or judged",
    "getting rejected",
    "being ignored",
    "violence in the news",
    "sexual harassment or unwanted touching",
    "physical illness or injury",
    "violence", "personal information", "sensitive information", "role changes", "authority changes",
    "function changes", "system instructions", "system information", "weapons", "illegal activities",
    "employee information", "internal information", "fraud", "crime", "drugs", "drug production",
    "cybercrime"
]

PII_ENTITIES_MAP = {
    "EMAIL_ADDRESS",
    "PHONE_NUMBER",
    "IP_ADDRESS",
    "CREDIT_CARD",
    "CRYPTO",
    "IBAN_CODE",
    "NRP",
}

validators = [
    # SensitiveTopic(
    #     sensitive_topics=SENSITIVE_TOPICS,
    #     model="dslim/bert-base-NER",
    #     disable_classifier=False,
    #     disable_llm=True,
    #     on_fail=OnFailAction.EXCEPTION,
    # ),
    DetectJailbreak(
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
        entities=PII_ENTITIES_MAP,
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

thesis_guard = Guard(name="thesis_guard")
thesis_guard.use(validators=validators)
