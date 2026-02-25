from enum import Enum
from typing import Dict, List, cast
from deepteam.vulnerabilities.illegal_activity import IllegalActivityType # type: ignore
from deepteam.vulnerabilities import BaseVulnerability, IllegalActivity # type: ignore
from deepeval.models import DeepEvalBaseLLM
from deepteam.metrics import BaseRedTeamingMetric # type: ignore
from deepteam.test_case import RTTestCase
from testframework.testcases.illegal_activity.test_case import Subcategory
from testframework.util.csv_loader import CSVLoader

class IllegalActivity(BaseVulnerability):
    def __init__(
        self,
        types: List[Enum],
        simulator_model: DeepEvalBaseLLM,
        async_mode: bool = True,
        verbose_mode: bool = True,
        ):
        self.types = types
        self.async_mode = async_mode
        self.verbose_mode = verbose_mode
        self.simulator_model = simulator_model
        self.default_attack_builder:BaseVulnerability | None  = None
        super().__init__(types)

    def subcategory_to_illegal_activity_type(self, category: Subcategory) -> str | None:
            map: Dict[Subcategory,str] = {
                Subcategory.WEAPONS: IllegalActivityType.WEAPONS.value,
                Subcategory.CHILD_EXPLOITATION : IllegalActivityType.CHILD_EXPLOITATION.value,
                Subcategory.ILLEGAL_DRUGS: IllegalActivityType.ILLEGAL_DRUGS.value,
                Subcategory.VIOLENT_CRIME: IllegalActivityType.VIOLENT_CRIME.value,
                Subcategory.NONVIOLENT_CRIME: IllegalActivityType.NON_VIOLENT_CRIME.value,
                Subcategory.SEX_CRIME: IllegalActivityType.SEX_CRIME.value,
                Subcategory.CYBERCRIME: IllegalActivityType.CYBERCRIME.value,
            }
            return map.get(category)

    def simulate_attacks(self, purpose: str = None) -> List[RTTestCase]:
        attacks: List[RTTestCase] = []
        if Subcategory.WEAPONS in self.types:
            attacks.extend(
                RTTestCase(
                    vulnerability=self.get_name(),
                    vulnerability_type=Subcategory.WEAPONS,
                    input=prompt)
                for prompt in CSVLoader.load_prompts_from_csv(file_path="2_schaedlich_manuell.csv", categories=["illegal-activity_weapons"])
            )
        elif Subcategory.CHILD_EXPLOITATION in self.types:
            attacks.extend(
                RTTestCase(
                    vulnerability=self.get_name(),
                    vulnerability_type=Subcategory.CHILD_EXPLOITATION,
                    input=prompt)
                for prompt in CSVLoader.load_prompts_from_csv(file_path="2_schaedlich_manuell.csv", categories=["illegal-activity_child-exploitation"])
            )
        deep_team_types: List[str | None] = [self.subcategory_to_illegal_activity_type(category) for category in self.get_types()]
        self.default_attack_builder = IllegalActivity(simulator_model=self.simulator_model, types=deep_team_types)
        attacks.extend(self.default_attack_builder.simulate_attacks())
        return attacks

    def _get_metric(self, attack: RTTestCase) -> BaseRedTeamingMetric:
        attack_type = cast(IllegalActivityType, attack.vulnerability_type)
        return cast(IllegalActivity, self.default_attack_builder)._get_metric(type=attack_type)  # pylint: disable=protected-access

    def get_name(self) -> str:
        return "IllegalActivity"
