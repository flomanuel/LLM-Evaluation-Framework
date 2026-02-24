from __future__ import annotations

from typing import cast

from deepeval.models import OllamaModel
from deepteam.metrics import BaseRedTeamingMetric
from deepteam.test_case import RTTestCase
from deepteam.vulnerabilities import IllegalActivity  # type: ignore
from deepteam.vulnerabilities.illegal_activity import IllegalActivityType

from ..enums import Category, TestCaseName
from .base import BaseTestCase


class IllegalActivityTestCase(BaseTestCase):
    """Test case using DeepTeam's IllegalActivity vulnerability as an attack source."""

    DEFAULT_OLLAMA_TIMEOUT: float = 120.0

    def __init__(self, timeout: float | None = None) -> None:
        # ollama run llama2-uncensored
        # ollama run ollama run aqualaguna/gemma-3-27b-it-abliterated-GGUF:q2_k
        effective_timeout = timeout or self.DEFAULT_OLLAMA_TIMEOUT
        simulator_model = OllamaModel(
            model="llama2-uncensored",
            temperature=1.0,
            generation_kwargs={
                "timeout": effective_timeout,
            }
        )

        super().__init__(TestCaseName.ILLEGAL_ACTIVITY,
                         Category.ILLEGAL_ACTIVITY,
                         None,
                         IllegalActivity(simulator_model=simulator_model)
                         )

    def _get_metric(self, attack: RTTestCase = None) -> BaseRedTeamingMetric:
        illegal_activity = cast(IllegalActivity, self.attack_builder)
        attack_type = cast(IllegalActivityType, attack.vulnerability_type)
        return illegal_activity._get_metric(type=attack_type)

    def enhance_base_attack(self, base_attack: str) -> str:
        # todo: implement
        return base_attack

