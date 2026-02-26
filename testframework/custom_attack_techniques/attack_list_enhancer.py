from __future__ import annotations
from typing import List
from deepteam.test_case import RTTestCase

from testframework.models import EnhancedAttack


class AttackListEnhancer:
    """Enhance a list of attacks.
    """

    @staticmethod
    def enhance(attacks: List[RTTestCase]) -> List[EnhancedAttack]:
        return [
            EnhancedAttack(
                attack_case=attack,
                baseline_input=str(attack.input),
                enhanced_input=str(attack.input),
            )
            for attack in attacks
        ]
