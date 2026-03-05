#  Copyright (c) 2026.
#  Florian Emanuel Sauer
from typing import List
from testframework import ChatbotName
from testframework.guardrails.base import BaseGuardrail
from testframework.models import DetectionElement
from guardrails import Guard, Validator, ValidationOutcome, install


class GuardrailsAI(BaseGuardrail):
    """Guardrail for GuardrailsAI from [GuardrailsAI](https://guardrailsai.com/)."""

    def __init__(self) -> None:
        super().__init__("Guardrails AI")
        self._guard = Guard().use(validators=self.validators)

    sensitive_topic = install(
        "hub://guardrails/sensitive_topics",
        install_local_models=False,  # use remote inferencing; easier on the local hardware
        quiet=False
    ).SensitiveTopic

    detect_jailbreak = install(
        "hub://guardrails/detect_jailbreak",
        install_local_models=False,  # use remote inferencing; easier on the local hardware
        quiet=False
    ).DetectJailbreak

    toxic_language = install(
        "hub://guardrails/toxic_language",
        install_local_models=False,  # use remote inferencing; easier on the local hardware
        quiet=False
    ).ToxicLanguage

    bias_check = install(
        "hub://guardrails/bias_check",
        install_local_models=False,  # use remote inferencing; easier on the local hardware
        quiet=False
    ).BiasCheck

    guardrails_pii = install(
        "hub://guardrails/guardrails_pii",
        install_local_models=False,  # use remote inferencing; easier on the local hardware
        quiet=False
    ).GuardrailsPII

    shield_gemma_2b = install(
        "hub://guardrails/shieldgemma_2b",
        install_local_models=False,  # use remote inferencing; easier on the local hardware
        quiet=False
    ).ShieldGemma2B

    llama_guard_7b = install(
        "hub://guardrails/llamaguard_7b",
        install_local_models=False,  # use remote inferencing; easier on the local hardware
        quiet=False
    ).LlamaGuard7B

    def eval_attack(self, user_prompt: str, attack_description: str, **kwargs) -> DetectionElement:
        self._check_request_allowed()
        res: ValidationOutcome = self._guard.parse(user_prompt)

        return None

    def eval_model_response(self, model_response: str, chatbot: ChatbotName, attack_description: str,
                            **kwargs) -> DetectionElement:
        self._check_request_allowed()
        res: ValidationOutcome = self._guard.parse(model_response)

        return None

    @property
    def validators(self) -> List[Validator]:
        return [
            self.sensitive_topic(
                sensitive_topics="",
                device=-1,
                model="facebook/bart-large-mnli",
                llm_callable="gpt-3.5-turbo",
                disable_classifier=["disable_classifier"],
                classifier_api_endpoint=["classifier_api_endpoint"],
                disable_llm=["disable_llm"],
                zero_shot_threshold=0.5,
                llm_threshold=3
            ),
            self.detect_jailbreak(
                threshold=["threshold"],
                device=["device"]
            ),
            self.toxic_language(
                validation_method="sentence",
                threshold=0.5
            ),
            self.bias_check(
                debias_strength=0.5,
                on_fail=["on_fail"]
            ),
            self.guardrails_pii(
                entities=["entities"],
                model_name="urchade/gliner_small-v2.1"
            ),
            self.shield_gemma_2b(),
            self.llama_guard_7b()
        ]

    def _check_request_allowed(self):
        """Check if the guardrail is allowed to make a request due to rate limits."""
        # limits: 100 requests per minute, 500 in total for 5 minutes. Every scanner (e.g., bias_check counts as one request)
        pass
