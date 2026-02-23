from __future__ import annotations

from typing import List, Tuple

from deepteam.attacks.single_turn import (  # type: ignore
    PromptInjection,
    MathProblem,
    Leetspeak,
)

from ..models import PromptVariants, PromptTokens


class AttackPipeline:
    """Applies a fixed sequence of DeepTeam single-turn enhancements to a baseline prompt."""

    def __init__(self) -> None:
        # Example techniques; can be configured per test case if needed.
        self.prompt_injection_attack = PromptInjection()
        self.math_attack = MathProblem()
        self.encoding_attack = Leetspeak()

    def build_variants(self, baseline: str) -> Tuple[PromptVariants, PromptTokens]:
        """Produce baseline, attack, enhanced strings and dummy token counts."""
        # For now, use two techniques in sequence as an example.
        attack = self.prompt_injection_attack.enhance(baseline)
        enhanced = self.encoding_attack.enhance(attack)

        variants = PromptVariants(
            baseline=baseline,
            attack=attack,
            enhanced=enhanced,
        )
        tokens = PromptTokens(
            baseline=len(baseline.split()),
            attack=len(attack.split()),
            enhanced=len(enhanced.split()),
        )
        return variants, tokens


