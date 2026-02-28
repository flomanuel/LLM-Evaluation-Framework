from __future__ import annotations
from copy import deepcopy
from dataclasses import dataclass
from typing import Callable, List

from deepeval.models import DeepEvalBaseLLM
from deepteam.attacks.single_turn import AdversarialPoetry, MathProblem, GoalRedirection, PromptInjection, Roleplay, \
    Base64, Leetspeak, InputBypass, SystemOverride
from deepteam.test_case import RTTestCase
from loguru import logger

from testframework.custom_attack_techniques.cipher_code_expert.cipher_code_expert import CipherCodeExpert
from testframework.custom_attack_techniques.emotional_manipulation import EmotionalManipulation
from testframework.custom_attack_techniques.synthetic_context_injection import SyntheticContextInjection
from testframework.models import EnhancedAttack, TestErrorInfo


@dataclass(frozen=True)
class AttackEnhancement:
    """Single enhancement strategy applied to an attack input."""

    name: str
    transform: Callable[[str, DeepEvalBaseLLM | str], str]


class AttackListEnhancer:
    """Enhance a list of attacks.
    """

    def __init__(self, simulator_model: DeepEvalBaseLLM | str):
        self.simulator_model = simulator_model

    ENHANCEMENTS: List[AttackEnhancement] = [
        AttackEnhancement(
            name=AdversarialPoetry.name,
            transform=lambda prompt, model: AdversarialPoetry().enhance(attack=prompt, simulator_model=model)
        ),
        AttackEnhancement(
            name=MathProblem.name,
            transform=lambda prompt, model: MathProblem().enhance(prompt, simulator_model=model)
        ),
        AttackEnhancement(
            name=GoalRedirection.name,
            transform=lambda prompt, model: GoalRedirection().enhance(prompt)
        ),
        AttackEnhancement(
            name=PromptInjection.name,
            transform=lambda prompt, model: PromptInjection().enhance(prompt)
        ),
        AttackEnhancement(
            name=Roleplay.name,
            transform=lambda prompt, model: Roleplay().enhance(prompt, simulator_model=model)
        ),
        AttackEnhancement(
            name=EmotionalManipulation.name,
            transform=lambda prompt, model: EmotionalManipulation().enhance(prompt, simulator_model=model)
        ),
        AttackEnhancement(
            name=SyntheticContextInjection.name,
            transform=lambda prompt, model: SyntheticContextInjection(
                "Bank chatbot used internally by the employees.").enhance(prompt, simulator_model=model)
        ),
        AttackEnhancement(
            name=CipherCodeExpert.name,
            transform=lambda prompt, model: CipherCodeExpert().enhance(prompt)
        ),
        AttackEnhancement(
            name=Base64.name,
            transform=lambda prompt, model: Base64().enhance(prompt)
        ),
        AttackEnhancement(
            name=Leetspeak.name,
            transform=lambda prompt, model: Leetspeak().enhance(prompt)
        ),
        AttackEnhancement(
            name=InputBypass.name,
            transform=lambda prompt, model: InputBypass().enhance(prompt)
        ),
        AttackEnhancement(
            name=SystemOverride.name,
            transform=lambda prompt, model: SystemOverride().enhance(prompt)
        ),
    ]

    def enhance(
            self,
            attacks: List[RTTestCase],
            enhancements: List[AttackEnhancement] | None = None,
    ) -> List[EnhancedAttack]:
        logger.info(
            f"Enhancing {len(attacks)} attacks with {len(enhancements) if enhancements else len(AttackListEnhancer.ENHANCEMENTS)} techniques.")
        active_enhancements = (
            enhancements if enhancements is not None else AttackListEnhancer.ENHANCEMENTS
        )

        if not active_enhancements:
            return [
                EnhancedAttack(
                    attack_case=deepcopy(attack),
                    baseline_input=str(attack.input),
                    enhanced_input=str(attack.input),
                )
                for attack in attacks
            ]

        enhanced_attacks: List[EnhancedAttack] = []
        for attack in attacks:
            baseline_input = str(attack.input)
            for enhancement in active_enhancements:
                cloned_attack = deepcopy(attack)
                try:
                    enhanced_input = enhancement.transform(baseline_input, self.simulator_model)
                    enhanced_attacks.append(
                        EnhancedAttack(
                            attack_case=cloned_attack,
                            baseline_input=baseline_input,
                            enhanced_input=enhanced_input,
                            techniques=[enhancement.name],
                        )
                    )
                except Exception as exc:
                    enhancement_error = TestErrorInfo.from_exception(exc)
                    logger.exception(
                        f"Enhancement '{enhancement.name}' failed "
                        f"({enhancement_error.error_type.value}): {enhancement_error.message}"
                    )
                    enhanced_attacks.append(
                        EnhancedAttack(
                            attack_case=cloned_attack,
                            baseline_input=baseline_input,
                            enhanced_input=baseline_input,
                            techniques=[enhancement.name],
                            error=enhancement_error,
                        )
                    )

        logger.info(f"Enhanced {len(enhanced_attacks)} attacks.")
        return enhanced_attacks
