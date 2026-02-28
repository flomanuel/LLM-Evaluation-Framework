#  Copyright (c) 2026.
#  Florian Emanuel Sauer

from enum import Enum
from typing import Dict, List, cast
from deepteam.vulnerabilities import BaseVulnerability, Ethics  # type: ignore
from deepteam.vulnerabilities.ethics import EthicsType  # type: ignore
from deepteam.metrics import BaseRedTeamingMetric, HarmMetric  # type: ignore
from deepeval.models import DeepEvalBaseLLM
from deepteam.test_case import RTTestCase

from testframework.testcases.ethics.subcategory import EthicsSubcategory
from testframework.util.csv_loader import CSVLoader


class EthicsAttacks(BaseVulnerability):
    """Class that builds ethics attack prompts from CSV and DeepTeam."""

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
        self.default_attack_builder: BaseVulnerability | None = None
        super().__init__(types)

    def subcategory_to_ethics_type(self, subcategory) -> str | None:
        """Map Subcategory to DeepTeam EthicsType value."""
        mapping: Dict[EthicsSubcategory, str] = {
            EthicsSubcategory.HARM_PREVENTION: EthicsType.HARM_PREVENTION.value,
            EthicsSubcategory.MORAL_INTEGRITY: EthicsType.MORAL_INTEGRITY.value,
        }
        return mapping.get(subcategory)

    def simulate_attacks(self, purpose: str = None) -> List[RTTestCase]:
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
            attacks.extend(self.default_attack_builder.simulate_attacks())

        return attacks

    def _get_metric(self, attack: RTTestCase) -> BaseRedTeamingMetric:
        if self.default_attack_builder:
            attack_type = cast(EthicsType, attack.vulnerability_type)
            return cast(Ethics, self.default_attack_builder)._get_metric(  # pylint: disable=protected-access
                type=attack_type)
        return HarmMetric(harm_category="ethics", model=self.evaluation_model)

    def get_name(self) -> str:
        return "Ethics"
