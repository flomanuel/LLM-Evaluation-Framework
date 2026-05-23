#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.


import os
import time
from collections.abc import Callable
from copy import deepcopy
from deepeval.models import DeepEvalBaseLLM, OllamaModel
from dotenv import load_dotenv
from loguru import logger

from testframework.custom_attack_techniques.techniques import AttackEnhancement, ENHANCEMENTS, TECHNIQUE_BASELINE
from testframework.models import AttackEnhancementResult, EnhancedAttack, TestErrorInfo
from testframework.redteam.test_case import RTTestCase
from testframework.util.ollama_handler import OllamaGenerator


class AttackListEnhancer:
    """Enhance a list of attacks."""

    ERROR_THRESHOLD_ENV_VAR = "ENHANCED_ATTACK_ERROR_THRESHOLD_PERCENT"
    DEFAULT_ERROR_THRESHOLD_PERCENT = 100.0
    ERROR_RETRY_COOLDOWN_SECONDS = 420
    ATTACK_GENERATION_COOLDOWN_SECONDS = ERROR_RETRY_COOLDOWN_SECONDS
    SUCCESS_COOLDOWN_SECONDS = 10
    RETRY_ATTEMPTS_ENV_VAR = "ENHANCEMENT_RETRY_ATTEMPTS"
    DEFAULT_RETRY_ATTEMPTS = 0
    LOCAL_MODEL_ID = os.environ.get("LOCAL_MODEL_ID", False)

    def __init__(self, simulator_model: DeepEvalBaseLLM | None | str):
        self.simulator_model = simulator_model

    def enhance(
            self,
            attacks: list[RTTestCase],
            enhancements: list[AttackEnhancement] | None = None,
    ) -> AttackEnhancementResult:
        """Enhance a list of attacks with the given techniques."""
        logger.info(
            "Enhancing {} attacks with {} techniques.",
            len(attacks),
            len(enhancements) if enhancements else len(ENHANCEMENTS),
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

        enhanced_attacks: list[EnhancedAttack] = []
        enhanceable_attacks = sum(
            1 for attack in attacks if attack.vulnerability_type != "document-embedded-instructions")
        planned_attack_count = enhanceable_attacks * len(active_enhancements) + (len(attacks) - enhanceable_attacks)
        failed_attack_count = 0
        enhanced_attack_count = 0
        for attack in attacks:
            logger.info("=== Enhancing attack {}/{} === ", enhanced_attack_count + 1, len(attacks))
            is_doc_embedding_attack = attack.vulnerability_type == "document-embedded-instructions"
            # document embedding instructions have the attack + technique directly "baked" into the document.
            # So we mustn't enhance the already enhanced attack.
            if is_doc_embedding_attack:
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
                # deactivate the if-branch in line 78, including the else statement in line 90. Then uncomment this
                # section and indent the former-else-flow one to the left.
                # if is_doc_embedding_attack:
                #     simulate indirect document injection by adding the injection defined in the prompt
                #     raw_prompts: list[str] = str(attack.input).split("#")
                #     user_prompt = raw_prompts[0] if len(raw_prompts) > 0 else ""
                #     baseline_input = raw_prompts[1] if len(raw_prompts) > 1 else ""
                # else:
                #     user_prompt = ""
                #     baseline_input = str(attack.input)
                baseline_input = str(attack.input)
                for enhancement in active_enhancements:
                    logger.info("Applying enhancement '{}'", enhancement.name)
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
                            "Enhancement '{}' failed ({}): {}",
                            enhancement.name,
                            enhancement_error.error_type.value,
                            enhancement_error.message,
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
                                "rate exceeded the configured threshold: ({}/{}) > {}",
                                failed_attack_count,
                                planned_attack_count,
                                error_threshold_percent,
                            )
                            self._cooldown_with_model_shutdown(time.sleep, self.ATTACK_GENERATION_COOLDOWN_SECONDS)
                            return AttackEnhancementResult(enhanced_attacks=enhanced_attacks,
                                                           planned_attack_count=planned_attack_count,
                                                           failed_attack_count=failed_attack_count,
                                                           error_threshold_percent=error_threshold_percent,
                                                           stopped_early=True)
                enhanced_attack_count += 1
        logger.info("Enhanced {} attacks.", len(enhanced_attacks))
        return AttackEnhancementResult(enhanced_attacks=enhanced_attacks, planned_attack_count=planned_attack_count,
                                       failed_attack_count=failed_attack_count,
                                       error_threshold_percent=error_threshold_percent)

    def _cooldown_with_model_shutdown(self, cooldown: Callable[[int], None], seconds: int):
        """Apply a cooldown and shut down the model if it's an Ollama model."""
        if isinstance(self.simulator_model, OllamaModel):
            OllamaGenerator.require_local_model_shutdown()
            logger.info("Cooldown: {} seconds.", seconds)
            cooldown(seconds)
            OllamaGenerator.start_model_if_not_running()

    def _apply_enhancement(
            self,
            enhancement: AttackEnhancement,
            baseline_input: str,
    ) -> tuple[str | None, TestErrorInfo | None]:
        """Apply one enhancement with config-driven retries."""
        max_retries = self._load_retry_attempts()
        max_attempts = max_retries + 1
        for attempt in range(1, max_attempts + 1):
            try:
                enhanced_input = enhancement.transform(baseline_input, self.simulator_model)
                if enhanced_input == baseline_input and enhancement.name != TECHNIQUE_BASELINE:
                    # Treat unchanged output as enhancement failure so retries can apply.
                    raise ValueError("Enhanced input is identical to baseline input.")
                if isinstance(self.simulator_model, OllamaModel):
                    logger.info("Cooldown: {}s.", self.SUCCESS_COOLDOWN_SECONDS)
                    enhancement.cooldown(self.SUCCESS_COOLDOWN_SECONDS)
                return enhanced_input, None
            except Exception as exc:
                enhancement_error = TestErrorInfo.from_exception(exc)
                if attempt >= max_attempts:
                    return None, enhancement_error
                logger.warning(
                    "Enhancement '{}' failed on attempt {}/{} ({}): {}. Retrying.",
                    enhancement.name,
                    attempt,
                    max_attempts,
                    enhancement_error.error_type.value,
                    enhancement_error.message,
                )
                self._cooldown_with_model_shutdown(enhancement.cooldown, self.ERROR_RETRY_COOLDOWN_SECONDS)
        return None, TestErrorInfo.from_exception(RuntimeError("Unexpected retry state"))

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
                "Invalid value for {}: '{}'. Falling back to {:.2f}%.",
                cls.ERROR_THRESHOLD_ENV_VAR,
                raw_threshold,
                cls.DEFAULT_ERROR_THRESHOLD_PERCENT,
            )
            return cls.DEFAULT_ERROR_THRESHOLD_PERCENT

        if threshold < 0.0:
            logger.warning(
                "{} is below 0: {}. Using 0.00%.",
                cls.ERROR_THRESHOLD_ENV_VAR,
                threshold,
            )
            return 0.0
        if threshold > 100.0:
            logger.warning(
                "{} is above 100: {}. Using 100.00%.",
                cls.ERROR_THRESHOLD_ENV_VAR,
                threshold,
            )
            return 100.0
        return threshold

    @classmethod
    def _load_retry_attempts(cls) -> int:
        """Read and normalize configured retry attempts for failed enhancements."""
        load_dotenv(override=False)
        raw_retries = os.getenv(
            cls.RETRY_ATTEMPTS_ENV_VAR,
            str(cls.DEFAULT_RETRY_ATTEMPTS),
        )
        try:
            retries = int(raw_retries)
        except ValueError:
            logger.warning(
                "Invalid value for {}: '{}'. Falling back to {}.",
                cls.RETRY_ATTEMPTS_ENV_VAR,
                raw_retries,
                cls.DEFAULT_RETRY_ATTEMPTS,
            )
            return cls.DEFAULT_RETRY_ATTEMPTS

        if retries < 0:
            logger.warning(
                "{} is below 0: {}. Using 0.",
                cls.RETRY_ATTEMPTS_ENV_VAR,
                retries,
            )
            return 0
        return retries

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
