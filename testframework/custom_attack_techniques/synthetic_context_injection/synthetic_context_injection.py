#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.


from typing import Optional, Union
from deepeval.models import DeepEvalBaseLLM
from deepeval.metrics.utils import initialize_model
from deepteam.utils import create_progress, update_pbar, add_pbar
from deepteam.attacks.single_turn import BaseSingleTurnAttack
from deepteam.attacks.base_attack import Exploitability
from deepteam.attacks.attack_simulator.utils import (
    generate,
    a_generate,
)
from loguru import logger

from testframework.custom_attack_techniques.synthetic_context_injection.schema import EnhancedContext, ComplianceData, \
    IsContextValid
from testframework.custom_attack_techniques.synthetic_context_injection.template import \
    SyntheticContextInjectionTemplate


class SyntheticContextInjection(BaseSingleTurnAttack):
    """Build the synthetic context injection technique."""
    name = "Synthetic Context Injection"
    exploitability = Exploitability.HIGH
    description = "Generates domain-specific 'fake history' that mimics internal company logs, emails, and verification states."

    def __init__(
            self,
            target_information: str,
            context_style: Optional[str] = None,
            weight: int = 1,
            max_retries: int = 3,
    ):
        self.target_information = target_information
        self.context_style = context_style
        self.weight = weight
        self.max_retries = max_retries

    def enhance(
            self,
            attack: str,
            simulator_model: Optional[Union[DeepEvalBaseLLM, str]] = None,
    ) -> str:
        logger.info(f"Enhancing attack with {self.name} technique.")
        self.simulator_model, _ = initialize_model(simulator_model)

        prompt = SyntheticContextInjectionTemplate.enhance(
            attack,
            self.target_information,
        )

        progress = create_progress()
        with progress:
            task_id = add_pbar(
                progress,
                description=f"...... 📜 Generating Prior Context",
                total=self.max_retries * 3,
            )

            for _ in range(self.max_retries):
                res: EnhancedContext = generate(
                    prompt, EnhancedContext, self.simulator_model
                )
                generated_context = res.input
                update_pbar(progress, task_id)

                compliance_prompt = (
                    SyntheticContextInjectionTemplate.non_compliant(
                        res.model_dump()
                    )
                )
                compliance_res: ComplianceData = generate(
                    compliance_prompt, ComplianceData, self.simulator_model
                )
                update_pbar(progress, task_id)

                is_valid_prompt = (
                    SyntheticContextInjectionTemplate.is_valid_context(
                        res.model_dump()
                    )
                )
                is_valid_res: IsContextValid = generate(
                    is_valid_prompt,
                    IsContextValid,
                    self.simulator_model,
                )
                update_pbar(progress, task_id)

                if (
                        not compliance_res.non_compliant
                        and is_valid_res.is_valid_context
                ):
                    update_pbar(progress, task_id, advance_to_end=True)

                    final_attack = f"{generated_context}\n\nUSER: {attack}"
                    return final_attack

            update_pbar(progress, task_id, advance_to_end=True)

        return attack

    async def a_enhance(
            self,
            attack: str,
            simulator_model: Optional[Union[DeepEvalBaseLLM, str]] = None,
    ) -> str:
        self.simulator_model, _ = initialize_model(simulator_model)
        prompt = SyntheticContextInjectionTemplate.enhance(
            attack,
            self.target_information,
        )

        progress = create_progress()
        with progress:
            task_id = add_pbar(
                progress,
                description=f"...... 📜 Generating Prior Context",
                total=self.max_retries * 3,
            )

            try:
                for _ in range(self.max_retries):
                    res: EnhancedContext = await a_generate(
                        prompt, EnhancedContext, self.simulator_model
                    )
                    generated_context = res.input
                    update_pbar(progress, task_id)

                    compliance_prompt = (
                        SyntheticContextInjectionTemplate.non_compliant(
                            res.model_dump()
                        )
                    )
                    compliance_res: ComplianceData = await a_generate(
                        compliance_prompt,
                        ComplianceData,
                        self.simulator_model,
                    )
                    update_pbar(progress, task_id)

                    is_valid_prompt = (
                        SyntheticContextInjectionTemplate.is_valid_context(
                            res.model_dump()
                        )
                    )
                    is_valid_res: IsContextValid = await a_generate(
                        is_valid_prompt,
                        IsContextValid,
                        self.simulator_model,
                    )
                    update_pbar(progress, task_id)

                    if (
                            not compliance_res.non_compliant
                            and is_valid_res.is_valid_context
                    ):
                        update_pbar(progress, task_id, advance_to_end=True)
                        final_attack = f"{generated_context}\n\nUSER: {attack}"
                        return final_attack

            finally:
                update_pbar(progress, task_id, advance_to_end=True)

        return attack

    def get_name(self) -> str:
        return self.name
