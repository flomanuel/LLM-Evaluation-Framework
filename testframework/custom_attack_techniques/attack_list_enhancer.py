#  Copyright (c) 2026.
#  Florian Emanuel Sauer

from __future__ import annotations

import os
from copy import deepcopy
from typing import List
from deepeval.models import DeepEvalBaseLLM, OllamaModel
from dotenv import load_dotenv
from deepteam.test_case import RTTestCase
from loguru import logger

from testframework.custom_attack_techniques.techniques import AttackEnhancement, ENHANCEMENTS
from testframework.models import AttackEnhancementResult, EnhancedAttack, TestErrorInfo
from testframework.util.ollama_handler import OllamaGenerator


class AttackListEnhancer:
    """Enhance a list of attacks.
    """

    ERROR_THRESHOLD_ENV_VAR = "ENHANCED_ATTACK_ERROR_THRESHOLD_PERCENT"
    DEFAULT_ERROR_THRESHOLD_PERCENT = 100.0
    MAX_RETRIES = 1
    RETRY_COOLDOWN_SECONDS = 420
    SUCCESS_COOLDOWN_SECONDS = 30
    LOCAL_MODEL_ID = os.environ.get("LOCAL_MODEL_ID", False)

    def __init__(self, simulator_model: DeepEvalBaseLLM | None | str):
        self.simulator_model = simulator_model

    def enhance(
            self,
            attacks: List[RTTestCase],
            enhancements: List[AttackEnhancement] | None = None,
    ) -> AttackEnhancementResult:
        logger.info(
            f"Enhancing {len(attacks)} attacks with "
            f"{len(enhancements) if enhancements else len(ENHANCEMENTS)} "
            f"techniques."
        )
        active_enhancements = (
            enhancements if enhancements is not None else ENHANCEMENTS
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
        enhanceable_attacks = sum(
            1 for attack in attacks if
            attack.vulnerability_type != "document-embedded-instructions" and (
                        attack.metadata is not None and attack.metadata.get(
                    "technique", "") == ""))
        planned_attack_count = enhanceable_attacks * len(active_enhancements) + (len(attacks) - enhanceable_attacks)
        failed_attack_count = 0
        enhanced_attack_count = 0
        for attack in attacks:
            logger.info(f"=== Enhancing attack {enhanced_attack_count + 1}/{len(attacks)} === ")
            is_doc_embedding_attack = attack.vulnerability_type == "document-embedded-instructions"
            has_technique = attack.metadata is not None and attack.metadata.get("technique", "") != ""
            if is_doc_embedding_attack and has_technique:
                cloned_attack = deepcopy(attack)
                enhanced_input = cloned_attack.input
                enhanced_attacks.append(
                    EnhancedAttack(
                        attack_case=cloned_attack,
                        baseline_input=str(attack.input),
                        enhanced_input=enhanced_input,
                        techniques=[attack.metadata.get("technique")],
                    )
                )
                enhanced_attack_count += 1
            else:
                # deactivate the if-branch in line 75, including the else statement in line 87. Then uncomment this
                # section and indent the former-else-flow one to the left.
                # if is_doc_embedding_attack:
                #     simulate indirect document injection by adding the injection defined in the prompt
                #     raw_prompts: List[str] = str(attack.input).split("#")
                #     user_prompt = raw_prompts[0] if len(raw_prompts) > 0 else ""
                #     baseline_input = raw_prompts[1] if len(raw_prompts) > 1 else ""
                # else:
                #     user_prompt = ""
                #     baseline_input = str(attack.input)
                baseline_input = str(attack.input)
                for enhancement in active_enhancements:
                    logger.info(f"Applying enhancement '{enhancement.name}'")
                    cloned_attack = deepcopy(attack)
                    enhanced_input, enhancement_error = self._apply_enhancement(
                        enhancement=enhancement,
                        baseline_input=baseline_input,
                    )
                    if enhancement_error is None:
                        enhanced_attacks.append(
                            EnhancedAttack(attack_case=cloned_attack, baseline_input=baseline_input,
                                           # baseline_input=baseline_input if not user_prompt else user_prompt,
                                           enhanced_input=enhanced_input, techniques=[enhancement.name],
                                           # enhanced_input=f"{user_prompt}\n{enhanced_input}" if user_prompt else enhanced_input,
                                           ))
                    else:
                        failed_attack_count += 1
                        logger.error(
                            f"Enhancement '{enhancement.name}' failed "
                            f"({enhancement_error.error_type.value}): {enhancement_error.message}"
                        )
                        enhanced_attacks.append(
                            EnhancedAttack(attack_case=cloned_attack, baseline_input=baseline_input,
                                           enhanced_input=baseline_input, techniques=[enhancement.name],
                                           error=enhancement_error)
                        )
                        if self._is_error_threshold_exceeded(failed_attack_count, planned_attack_count,
                                                             error_threshold_percent):
                            logger.warning(
                                "Stopping attack enhancement early because the failed enhancement "
                                f"rate exceeded the configured threshold: "
                                f"({failed_attack_count}/{planned_attack_count}) > {error_threshold_percent}"
                            )
                            return AttackEnhancementResult(enhanced_attacks=enhanced_attacks,
                                                           planned_attack_count=planned_attack_count,
                                                           failed_attack_count=failed_attack_count,
                                                           error_threshold_percent=error_threshold_percent,
                                                           stopped_early=True)
                enhanced_attack_count += 1
        logger.info(f"Enhanced {len(enhanced_attacks)} attacks.")
        return AttackEnhancementResult(enhanced_attacks=enhanced_attacks, planned_attack_count=planned_attack_count,
                                       failed_attack_count=failed_attack_count,
                                       error_threshold_percent=error_threshold_percent)

    def _apply_enhancement(
            self,
            enhancement: AttackEnhancement,
            baseline_input: str,
    ) -> tuple[str | None, TestErrorInfo | None]:
        """Apply one enhancement and retry it once after a cooldown if it fails."""
        max_attempts = self.MAX_RETRIES + 1
        for attempt in range(1, max_attempts + 1):
            try:
                enhanced_input = enhancement.transform(baseline_input, self.simulator_model)
                if isinstance(self.simulator_model, OllamaModel) and enhancement.cooldown is not None:
                    logger.info(
                        f"Cooldown: {self.SUCCESS_COOLDOWN_SECONDS}s.")
                    enhancement.cooldown(self.SUCCESS_COOLDOWN_SECONDS)
                return enhanced_input, None
            except Exception as exc:
                enhancement_error = TestErrorInfo.from_exception(exc)
                if attempt >= max_attempts:
                    return None, enhancement_error

                logger.warning(
                    f"Enhancement '{enhancement.name}' failed on attempt {attempt}/{max_attempts} "
                    f"({enhancement_error.error_type.value}): {enhancement_error.message}. "
                    "Preparing retry."
                )

                if self.LOCAL_MODEL_ID is not False and enhancement.cooldown is not None:
                    OllamaGenerator.require_local_model_shutdown()
                    logger.info(f"Retry cooldown: {self.RETRY_COOLDOWN_SECONDS}s.")
                    enhancement.cooldown(self.RETRY_COOLDOWN_SECONDS)
                    OllamaGenerator.start_model_if_not_running()

        raise RuntimeError("Enhancement retry loop ended unexpectedly.")

    @classmethod
    def _load_error_threshold_percent(cls) -> float:
        """Read and normalize the failed enhancement threshold from the environment."""
        load_dotenv(override=False)
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
