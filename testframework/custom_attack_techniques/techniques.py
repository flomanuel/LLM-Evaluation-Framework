#  Copyright (c) 2026.
#  Florian Emanuel Sauer

import time
from dataclasses import dataclass
from typing import List, Callable
from deepeval.models import DeepEvalBaseLLM
from deepteam.attacks.single_turn import AdversarialPoetry, GoalRedirection, MathProblem, PromptInjection, Base64, \
    Roleplay, Leetspeak

from testframework.custom_attack_techniques.cipher_code_expert.cipher_code_expert import CipherCodeExpert


@dataclass(frozen=True)
class AttackEnhancement:
    """Single enhancement strategy applied to an attack input."""
    name: str
    transform: Callable[[str, DeepEvalBaseLLM | None | str], str]
    cooldown: Callable[[int], None] | None  # add a cooldown since techniques are generated locally


ENHANCEMENTS: List[AttackEnhancement] = [
    AttackEnhancement(
        name=AdversarialPoetry.name,
        transform=lambda prompt, model: AdversarialPoetry().enhance(attack=prompt, simulator_model=model),
        cooldown=time.sleep
    ),
    AttackEnhancement(
        name=GoalRedirection.name,
        transform=lambda prompt, model: GoalRedirection().enhance(prompt),
        cooldown=None
    ),
    AttackEnhancement(
        name=MathProblem.name,
        transform=lambda prompt, model: MathProblem().enhance(prompt, simulator_model=model),
        cooldown=time.sleep
    ),
    AttackEnhancement(
        name=CipherCodeExpert.name,
        transform=lambda prompt, model: CipherCodeExpert().enhance(prompt),
        cooldown=None
    ),
    AttackEnhancement(
        name=f"{Base64.name}/{PromptInjection.name}",
        transform=lambda prompt, model: PromptInjection().enhance(Base64().enhance(prompt)),
        cooldown=None
    ),
    AttackEnhancement(
        name=Roleplay.name,
        transform=lambda prompt, model: Roleplay().enhance(prompt, simulator_model=model),
        cooldown=time.sleep
    ),
    AttackEnhancement(
        name=Leetspeak.name,
        transform=lambda prompt, model: Leetspeak().enhance(prompt),
        cooldown=None
    ),
]
