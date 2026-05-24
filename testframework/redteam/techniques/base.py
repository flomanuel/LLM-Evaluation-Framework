#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

"""Internal technique base classes replacing DeepTeam attack abstractions."""

from abc import ABC, abstractmethod
from enum import Enum

from deepeval.models import DeepEvalBaseLLM


class Exploitability(str, Enum):
    """Risk level of a prompt enhancement technique."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class BaseSingleTurnAttack(ABC):
    """Local replacement for DeepTeam single-turn attack techniques."""

    name = "Technique"
    exploitability = Exploitability.MEDIUM
    description = ""

    @abstractmethod
    def enhance(
            self,
            attack: str,
            simulator_model: DeepEvalBaseLLM | str | None = None,
            *args,
            **kwargs,
    ) -> str:
        """Enhance one baseline attack prompt."""
        raise NotImplementedError

    async def a_enhance(
            self,
            attack: str,
            simulator_model: DeepEvalBaseLLM | str | None = None,
            *args,
            **kwargs,
    ) -> str:
        """Async fallback implementation for techniques without custom async flow."""
        return self.enhance(attack, simulator_model=simulator_model, *args, **kwargs)

    def get_name(self) -> str:
        """Return the technique display name."""
        return self.name
