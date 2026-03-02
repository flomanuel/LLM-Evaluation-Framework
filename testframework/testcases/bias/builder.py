#  Copyright (c) 2026.
#  Florian Emanuel Sauer
from enum import Enum
from typing import List, cast, Dict
from deepteam.vulnerabilities import BaseVulnerability, Bias
from deepteam.vulnerabilities.bias import BiasType
from deepteam.metrics import BaseRedTeamingMetric
from deepeval.models import DeepEvalBaseLLM
from deepteam.test_case import RTTestCase
from testframework.testcases.bias.subcategory import BiasSubcategory


class BiasAttacks(BaseVulnerability):
    """Class that builds bias attack prompts from DeepTeam."""

    def subcategory_to_illegal_activity_type(self, category: BiasSubcategory) -> str | None:
        map: Dict[BiasSubcategory, str] = {
            BiasSubcategory.RACE: BiasType.RACE.value,
            BiasSubcategory.GENDER: BiasType.GENDER.value,
            BiasSubcategory.RELIGION: BiasType.RELIGION.value,
            BiasSubcategory.POLITICS: BiasType.POLITICS.value,
        }
        return map.get(category)

    def __init__(
            self,
            types: List[Enum],
            simulator_model: DeepEvalBaseLLM | None | str = None,
            evaluation_model: DeepEvalBaseLLM | None | str = None,
            async_mode: bool = True,
            verbose_mode: bool = True,
    ):
        self.types = types
        self.async_mode = async_mode
        self.verbose_mode = verbose_mode
        self.simulator_model = simulator_model
        self.evaluation_model = evaluation_model
        self.attack_builder: Bias | None = None
        super().__init__(types)

    def simulate_attacks(self, purpose: str = None, attacks_per_vulnerability_type: int = 1) -> List[RTTestCase]:
        attacks: List[RTTestCase] = []
        deepteam_types: List[str | None] = [self.subcategory_to_illegal_activity_type(category) for category in
                                            self.types]
        if deepteam_types:
            self.attack_builder = Bias(
                simulator_model=self.simulator_model,
                evaluation_model=self.evaluation_model,
                types=deepteam_types
            )
            attacks.extend(
                self.attack_builder.simulate_attacks(
                    attacks_per_vulnerability_type=attacks_per_vulnerability_type))

        return attacks

    def _get_metric(self, attack: RTTestCase) -> BaseRedTeamingMetric:
        attack_type = cast(BiasType, attack.vulnerability_type)
        return self.attack_builder._get_metric(type=attack_type)  # pylint: disable=protected-access

    def get_name(self) -> str:
        return "Bias"
