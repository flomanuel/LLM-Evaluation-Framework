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

    def enhance(self, attack: str) -> str:
        logger.info(f"Enhancing attack with {self.name} technique.")
        enhanced_prompt = CipherCodeExpertTemplate.enhance(attack)
        return enhanced_prompt

    def get_name(self) -> str:
        return self.name
