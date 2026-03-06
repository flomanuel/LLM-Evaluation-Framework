#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.



from deepteam.attacks.base_attack import Exploitability
from deepteam.attacks.single_turn import BaseSingleTurnAttack
from deepteam.utils import create_progress, add_pbar, update_pbar
from loguru import logger

from testframework.custom_attack_techniques.cipher_code_expert.template import CipherCodeExpertTemplate


# Based on DeepTeam attacks like emotional manipulation
class CipherCodeExpert(BaseSingleTurnAttack):
    name = "Cipher Code Expert"
    exploitability = Exploitability.HIGH
    description = "Rewrites the attack by roleplaying a cipher code expert to bypass safety filters."

    def enhance(self, attack: str, *args, **kwargs) -> str:
        logger.info(f"Enhancing attack with {self.name} technique.")
        progress = create_progress()
        task_id = add_pbar(
            progress,
            description=f"...... 🎭 Injecting {self.name}",
            total=1,
        )
        enhanced_prompt = CipherCodeExpertTemplate.enhance(attack)
        update_pbar(progress, task_id, advance_to_end=True)
        return enhanced_prompt

    def get_name(self) -> str:
        return self.name
