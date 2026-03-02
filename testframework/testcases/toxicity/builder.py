#  Copyright (c) 2026.
#  Florian Emanuel Sauer
from enum import Enum
from typing import List, cast, Dict
from deepteam.vulnerabilities import BaseVulnerability, Toxicity, PersonalSafety
from deepteam.vulnerabilities.personal_safety import PersonalSafetyType
from deepteam.metrics import BaseRedTeamingMetric
from deepeval.models import DeepEvalBaseLLM
from deepteam.test_case import RTTestCase
from deepteam.vulnerabilities.toxicity import ToxicityType

from testframework.testcases.toxicity.subcategory import ToxicitySubcategory


class ToxicityAttacks(BaseVulnerability):
    """Class that builds toxicity attack prompts from DeepTeam."""

    def subcategory_to_illegal_activity_type(self, category: ToxicitySubcategory) -> str | None:
        map: Dict[ToxicitySubcategory, str] = {
            ToxicitySubcategory.BULLYING: PersonalSafetyType.BULLYING.value,
            ToxicitySubcategory.INSULTS: ToxicityType.INSULTS.value,
            ToxicitySubcategory.PROFANITY: ToxicityType.PROFANITY.value,
            ToxicitySubcategory.THREATS: ToxicityType.THREATS.value,
            ToxicitySubcategory.MOCKERY: ToxicityType.MOCKERY.value,
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
        self.toxicity_attack_builder: Toxicity | None = None
        self.personal_safety_attack_builder: PersonalSafety | None = None
        super().__init__(types)

    def simulate_attacks(self, purpose: str = None, attacks_per_vulnerability_type: int = 1) -> List[RTTestCase]:
        attacks: List[RTTestCase] = []

        toxicity_types: List[str | None] = [self.subcategory_to_illegal_activity_type(category) for category in
                                            self.types if category is not ToxicitySubcategory.BULLYING]
        if toxicity_types:
            self.toxicity_attack_builder = Toxicity(
                simulator_model=self.simulator_model,
                evaluation_model=self.evaluation_model,
                types=toxicity_types
            )
            attacks.extend(
                self.toxicity_attack_builder.simulate_attacks(
                    attacks_per_vulnerability_type=attacks_per_vulnerability_type))

        personal_safety_types: List[str | None] = [
            self.subcategory_to_illegal_activity_type(category)
            for category in self.types if category == ToxicitySubcategory.BULLYING
        ]
        if personal_safety_types:
            self.personal_safety_attack_builder = PersonalSafety(
                simulator_model=self.simulator_model,
                evaluation_model=self.evaluation_model,
                types=personal_safety_types
            )
            attacks.extend(
                self.personal_safety_attack_builder.simulate_attacks(
                    attacks_per_vulnerability_type=attacks_per_vulnerability_type))

        return attacks

    def _get_metric(self, attack: RTTestCase) -> BaseRedTeamingMetric:
        attack_type = cast(ToxicityType, attack.vulnerability_type)
        return self.toxicity_attack_builder._get_metric(type=attack_type)  # pylint: disable=protected-access

    def get_name(self) -> str:
        return "Toxicity"
