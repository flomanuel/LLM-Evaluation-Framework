from __future__ import annotations
from copy import deepcopy
from dataclasses import dataclass
from typing import Callable, List
from deepteam.test_case import RTTestCase
from testframework.models import EnhancedAttack


@dataclass(frozen=True)
class AttackEnhancement:
    """Single enhancement strategy applied to an attack input."""

    name: str
    transform: Callable[[str], str]


class AttackListEnhancer:
    """Enhance a list of attacks.
    """

    # todo: add enhancements
    ENHANCEMENTS: List[AttackEnhancement] = []

    @staticmethod
    def enhance(
            attacks: List[RTTestCase],
            enhancements: List[AttackEnhancement] | None = None
    ) -> List[EnhancedAttack]:
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

        # apply all enhancements to all attacks, effectively multiplying the attacks by the number of enhancements
        enhanced_attacks: List[EnhancedAttack] = []
        for attack in attacks:
            baseline_input = str(attack.input)
            for enhancement in active_enhancements:
                cloned_attack = deepcopy(attack)
                enhanced_input = enhancement.transform(baseline_input)
                enhanced_attacks.append(
                    EnhancedAttack(
                        attack_case=cloned_attack,
                        baseline_input=baseline_input,
                        enhanced_input=enhanced_input,
                        techniques=[enhancement.name],
                    )
                )

        return enhanced_attacks
