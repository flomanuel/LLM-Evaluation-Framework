from enum import Enum
from typing import List, cast
from deepteam.vulnerabilities import BaseVulnerability, Toxicity, PersonalSafety
from deepteam.vulnerabilities.personal_safety import PersonalSafetyType
from deepteam.metrics import BaseRedTeamingMetric
from deepeval.models import DeepEvalBaseLLM
from deepteam.test_case import RTTestCase
from deepteam.vulnerabilities.toxicity import ToxicityType


class ToxicityAttacks(BaseVulnerability):
    """Class that builds toxicity attack prompts from DeepTeam."""

    def __init__(
            self,
            types: List[Enum],
            simulator_model: DeepEvalBaseLLM | None = None,
            evaluation_model: DeepEvalBaseLLM | None = None,
            async_mode: bool = True,
            verbose_mode: bool = True,
    ):
        self.types = types
        self.async_mode = async_mode
        self.verbose_mode = verbose_mode
        self.simulator_model = simulator_model
        self.evaluation_model = evaluation_model
        self.toxicity_attack_builder: Toxicity | None = None
        self.personal_safety_attack_builder: PersonalSafety | None = None
        super().__init__(types)

    def simulate_attacks(self, purpose: str = None) -> List[RTTestCase]:
        attacks: List[RTTestCase] = []
        self.toxicity_attack_builder = Toxicity(
            simulator_model=self.simulator_model,
            evaluation_model=self.evaluation_model
        )
        attacks.extend(self.toxicity_attack_builder.simulate_attacks())
        self.personal_safety_attack_builder = PersonalSafety(
            simulator_model=self.simulator_model,
            evaluation_model=self.evaluation_model,
            types=[PersonalSafetyType.BULLYING.value]
        )
        attacks.extend(self.personal_safety_attack_builder.simulate_attacks())
        return attacks

    def _get_metric(self, attack: RTTestCase) -> BaseRedTeamingMetric:
        attack_type = cast(ToxicityType, attack.vulnerability_type)
        return self.toxicity_attack_builder._get_metric(type=attack_type)  # pylint: disable=protected-access

    def get_name(self) -> str:
        return "Toxicity"
