#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.


from enum import Enum
from typing import Dict, List, cast
from deepteam.vulnerabilities import BaseVulnerability, Ethics
from deepteam.vulnerabilities.ethics import EthicsType
from deepteam.metrics import BaseRedTeamingMetric, HarmMetric
from deepeval.models import DeepEvalBaseLLM
from deepteam.test_case import RTTestCase
from testframework.testcases.ethics.subcategory import EthicsSubcategory
from testframework.util.csv_loader import CSVLoader


class EthicsAttacks(BaseVulnerability):
    """Class that builds ethics attack prompts from CSV and DeepTeam."""

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
        self.default_attack_builder: Ethics | None = None
        super().__init__(types)

    def subcategory_to_ethics_type(self, subcategory) -> str | None:
        """Map Subcategory to DeepTeam EthicsType value."""
        mapping: Dict[EthicsSubcategory, str] = {
            EthicsSubcategory.HARM_PREVENTION: EthicsType.HARM_PREVENTION.value,
            EthicsSubcategory.MORAL_INTEGRITY: EthicsType.MORAL_INTEGRITY.value,
        }
        return mapping.get(subcategory)

    def simulate_attacks(self, purpose: str = None, attacks_per_vulnerability_type: int = 1) -> List[RTTestCase]:
        """Simulate attacks for the test case."""
        attacks: List[RTTestCase] = []

        if EthicsSubcategory.BANKING in self.types:
            for row in CSVLoader.load_prompts_from_csv(
                    file_path="2_schaedlich_manuell_erstellt_basic.csv",
                    categories=["ethics_banking"]
            ):
                attack = RTTestCase(
                    vulnerability=self.get_name(),
                    vulnerability_type=EthicsSubcategory.BANKING,
                    input=row.prompt
                )
                metadata = row.build_attack_metadata()
                attack.metadata = metadata
                attacks.append(attack)

        deep_team_types: List[str] = []
        for subcategory in self.types:
            mapped_type = self.subcategory_to_ethics_type(subcategory)
            if mapped_type:
                deep_team_types.append(mapped_type)

        if deep_team_types:
            self.default_attack_builder = Ethics(
                simulator_model=self.simulator_model,
                evaluation_model=self.evaluation_model,
                types=deep_team_types
            )
            attacks.extend(self.default_attack_builder.simulate_attacks(
                attacks_per_vulnerability_type=attacks_per_vulnerability_type))

        return attacks

    def _get_metric(self, attack: RTTestCase) -> BaseRedTeamingMetric:
        """Get the metric for the test case."""
        if self.default_attack_builder:
            attack_type = cast(EthicsType, attack.vulnerability_type)
            return self.default_attack_builder._get_metric(type=attack_type)  # pylint: disable=protected-access
        return HarmMetric(harm_category="Ethics and breaking banking law.", model=self.evaluation_model)

    def get_name(self) -> str:
        """Get the human readable name of the test case."""
        return "Ethics"
