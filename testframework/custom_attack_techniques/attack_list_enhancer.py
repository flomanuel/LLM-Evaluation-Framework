#  Copyright (c) 2026.
#  Florian Emanuel Sauer

from __future__ import annotations

import os
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
from testframework.models import AttackEnhancementResult, EnhancedAttack, TestErrorInfo


@dataclass(frozen=True)
class AttackEnhancement:
    """Single enhancement strategy applied to an attack input."""

    name: str
    transform: Callable[[str, DeepEvalBaseLLM | str], str]


class AttackListEnhancer:
    """Enhance a list of attacks.
    """

    ERROR_THRESHOLD_ENV_VAR = "ENHANCED_ATTACK_ERROR_THRESHOLD_PERCENT"
    DEFAULT_ERROR_THRESHOLD_PERCENT = 100.0

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
    ) -> AttackEnhancementResult:
        logger.info(
            f"Enhancing {len(attacks)} attacks with "
            f"{len(enhancements) if enhancements else len(AttackListEnhancer.ENHANCEMENTS)} "
            f"techniques."
        )
        active_enhancements = (
            enhancements if enhancements is not None else AttackListEnhancer.ENHANCEMENTS
        )
        error_threshold_percent = self._load_error_threshold_percent()

        if not active_enhancements:
            return AttackEnhancementResult(
                enhanced_attacks=[
                    EnhancedAttack(
                        attack_case=deepcopy(attack),
                        baseline_input=str(attack.input),
                        enhanced_input=str(attack.input),
                    )
                    for attack in attacks
                ],
                planned_attack_count=len(attacks),
                failed_attack_count=0,
                error_threshold_percent=error_threshold_percent,
            )

        enhanced_attacks: List[EnhancedAttack] = []
        planned_attack_count = len(attacks) * len(active_enhancements)
        failed_attack_count = 0
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
                    failed_attack_count += 1
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
                    if self._is_error_threshold_exceeded(
                            failed_attack_count,
                            planned_attack_count,
                            error_threshold_percent,
                    ):
                        invalid_percentage = (
                            (failed_attack_count / planned_attack_count) * 100.0
                            if planned_attack_count > 0
                            else 0.0
                        )
                        logger.warning(
                            "Stopping attack enhancement early because the failed enhancement "
                            f"rate exceeded the configured threshold "
                            f"(failed={failed_attack_count}, planned={planned_attack_count}, "
                            f"error_rate={invalid_percentage:.2f}%, "
                            f"threshold={error_threshold_percent:.2f}%)"
                        )
                        return AttackEnhancementResult(
                            enhanced_attacks=enhanced_attacks,
                            planned_attack_count=planned_attack_count,
                            failed_attack_count=failed_attack_count,
                            error_threshold_percent=error_threshold_percent,
                            stopped_early=True,
                        )

        logger.info(f"Enhanced {len(enhanced_attacks)} attacks.")
        return AttackEnhancementResult(
            enhanced_attacks=enhanced_attacks,
            planned_attack_count=planned_attack_count,
            failed_attack_count=failed_attack_count,
            error_threshold_percent=error_threshold_percent,
        )

    @classmethod
    def _load_error_threshold_percent(cls) -> float:
        """Read and normalize the failed enhancement threshold from the environment."""
        raw_threshold = os.getenv(
            cls.ERROR_THRESHOLD_ENV_VAR,
            str(cls.DEFAULT_ERROR_THRESHOLD_PERCENT),
        )
        try:
            threshold = float(raw_threshold)
        except ValueError:
            logger.warning(
                f"Invalid value for {cls.ERROR_THRESHOLD_ENV_VAR}: '{raw_threshold}'. "
                f"Falling back to {cls.DEFAULT_ERROR_THRESHOLD_PERCENT:.2f}%."
            )
            return cls.DEFAULT_ERROR_THRESHOLD_PERCENT

        if threshold < 0.0:
            logger.warning(
                f"{cls.ERROR_THRESHOLD_ENV_VAR} is below 0: {threshold}. Using 0.00%."
            )
            return 0.0
        if threshold > 100.0:
            logger.warning(
                f"{cls.ERROR_THRESHOLD_ENV_VAR} is above 100: {threshold}. Using 100.00%."
            )
            return 100.0
        return threshold

    @staticmethod
    def _is_error_threshold_exceeded(
            failed_attack_count: int,
            planned_attack_count: int,
            error_threshold_percent: float,
    ) -> bool:
        """Check whether the failed enhancement rate is strictly above the threshold."""
        if planned_attack_count <= 0:
            return False
        return (failed_attack_count / planned_attack_count) * 100.0 > error_threshold_percent
