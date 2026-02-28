#  Copyright (c) 2026.
#  Florian Emanuel Sauer

from enum import Enum
from typing import List
from deepteam.vulnerabilities import BaseVulnerability
from deepteam.metrics import HarmMetric  # type: ignore
from deepeval.models import DeepEvalBaseLLM
from deepteam.test_case import RTTestCase
from deepteam.metrics import BaseRedTeamingMetric  # type: ignore
from testframework.util.csv_loader import CSVLoader


class PrivacyViolationsAttacks(BaseVulnerability):
    """Class that builds privacy violations attack prompts."""

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
        super().__init__(types)

    def simulate_attacks(self, purpose: str = None) -> List[RTTestCase]:
        attacks: List[RTTestCase] = []
        for row in CSVLoader.load_prompts_from_csv(
                file_path="2_schaedlich_manuell_erstellt_basic.csv",
                categories=["privacy-violations"]
        ):
            attack = RTTestCase(
                vulnerability=self.get_name(),
                input=row.prompt
            )
            metadata = row.build_attack_metadata()
            if metadata is not None:
                attack.metadata = metadata
            attacks.append(attack)
        return attacks

    def _get_metric(self) -> BaseRedTeamingMetric:
        return HarmMetric(harm_category="privacy-violations", model=self.evaluation_model)

    def get_name(self) -> str:
        return "PrivacyViolations"
