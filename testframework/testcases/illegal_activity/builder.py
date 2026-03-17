#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.


from enum import Enum
from typing import Dict, List, cast
from deepteam.vulnerabilities.illegal_activity import IllegalActivityType
from deepteam.vulnerabilities import BaseVulnerability, IllegalActivity as DeepTeamIllegalActivity
from deepeval.models import DeepEvalBaseLLM
from deepteam.metrics import BaseRedTeamingMetric
from deepteam.test_case import RTTestCase
from testframework.testcases.illegal_activity.subcategory import IllegalActivitySubcategory
from testframework.util.csv_loader import CSVLoader


class IllegalActivity(BaseVulnerability):
    """Test case for illegal activity attacks."""

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
        self.default_attack_builder: DeepTeamIllegalActivity | None = None
        super().__init__(types)

    def subcategory_to_illegal_activity_type(self, category: IllegalActivitySubcategory) -> str | None:
        """Map Subcategory to DeepTeam IllegalActivityType value."""
        map: Dict[IllegalActivitySubcategory, str] = {
            IllegalActivitySubcategory.WEAPONS: IllegalActivityType.WEAPONS.value,
            IllegalActivitySubcategory.CHILD_EXPLOITATION: IllegalActivityType.CHILD_EXPLOITATION.value,
            IllegalActivitySubcategory.ILLEGAL_DRUGS: IllegalActivityType.ILLEGAL_DRUGS.value,
            IllegalActivitySubcategory.VIOLENT_CRIME: IllegalActivityType.VIOLENT_CRIME.value,
            IllegalActivitySubcategory.NONVIOLENT_CRIME: IllegalActivityType.NON_VIOLENT_CRIME.value,
            IllegalActivitySubcategory.SEX_CRIME: IllegalActivityType.SEX_CRIME.value,
            IllegalActivitySubcategory.CYBERCRIME: IllegalActivityType.CYBERCRIME.value,
        }
        return map.get(category)

    def simulate_attacks(self, purpose: str = None, attacks_per_vulnerability_type: int = 1) -> List[RTTestCase]:
        """Simulate attacks for the test case."""
        attacks: List[RTTestCase] = []
        if IllegalActivitySubcategory.WEAPONS in self.types:
            for row in CSVLoader.load_prompts_from_csv(
                    file_path="2_schaedlich_manuell_erstellt_basic.csv",
                    categories=["illegal-activity_weapons"]
            ):
                attack = RTTestCase(
                    vulnerability=self.get_name(),
                    vulnerability_type=IllegalActivityType.WEAPONS,
                    input=row.prompt
                )
                metadata = row.build_attack_metadata()
                attack.metadata = metadata
                attacks.append(attack)
        if IllegalActivitySubcategory.ILLEGAL_DRUGS in self.types:
            for row in CSVLoader.load_prompts_from_csv(
                    file_path="2_schaedlich_manuell_erstellt_basic.csv",
                    categories=["illegal-activity_drugs"]
            ):
                attack = RTTestCase(
                    vulnerability=self.get_name(),
                    vulnerability_type=IllegalActivityType.ILLEGAL_DRUGS,
                    input=row.prompt
                )
                metadata = row.build_attack_metadata()
                attack.metadata = metadata
                attacks.append(attack)
        if IllegalActivitySubcategory.VIOLENT_CRIME in self.types:
            for row in CSVLoader.load_prompts_from_csv(
                    file_path="2_schaedlich_manuell_erstellt_basic.csv",
                    categories=["illegal-activity_crime"]
            ):
                attack = RTTestCase(
                    vulnerability=self.get_name(),
                    vulnerability_type=IllegalActivityType.VIOLENT_CRIME,
                    input=row.prompt
                )
                metadata = row.build_attack_metadata()
                attack.metadata = metadata
                attacks.append(attack)
        if IllegalActivitySubcategory.CHILD_EXPLOITATION in self.types:
            for row in CSVLoader.load_prompts_from_csv(
                    file_path="2_schaedlich_manuell_erstellt_basic.csv",
                    categories=["illegal-activity_child-exploitation"]
            ):
                attack = RTTestCase(
                    vulnerability=self.get_name(),
                    vulnerability_type=IllegalActivityType.CHILD_EXPLOITATION,
                    input=row.prompt
                )
                metadata = row.build_attack_metadata()
                attack.metadata = metadata
                attacks.append(attack)
        deep_team_types: List[str | None] = [self.subcategory_to_illegal_activity_type(category) for category in
                                             self.types]
        if deep_team_types:
            self.default_attack_builder = DeepTeamIllegalActivity(simulator_model=self.simulator_model,
                                                                  evaluation_model=self.evaluation_model,
                                                                  types=deep_team_types)
            attacks.extend(
                self.default_attack_builder.simulate_attacks(
                    attacks_per_vulnerability_type=attacks_per_vulnerability_type))
        return attacks

    def _get_metric(self, attack: RTTestCase) -> BaseRedTeamingMetric:
        """Get the metric for the test case."""
        attack_type = cast(IllegalActivityType, attack.vulnerability_type)
        return self.default_attack_builder._get_metric(type=attack_type)  # pylint: disable=protected-access

    def get_name(self) -> str:
        """Get the human readable name of the test case."""
        return "IllegalActivity"
