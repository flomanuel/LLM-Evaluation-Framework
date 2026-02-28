#  Copyright (c) 2026.
#  Florian Emanuel Sauer

from typing import List
from deepteam.vulnerabilities import BaseVulnerability
from deepteam.metrics import BaseRedTeamingMetric, FairnessMetric
from deepeval.models import DeepEvalBaseLLM
from deepteam.test_case import RTTestCase
from testframework.testcases.fairness.subcategory import FairnessSubcategory
from testframework.util.csv_loader import CSVLoader


class FairnessAttacks(BaseVulnerability):
    """Class that builds fairness attack prompts from CSV and DeepTeam."""

    def __init__(
            self,
            types=None,
            simulator_model: DeepEvalBaseLLM | None = None,
            evaluation_model: DeepEvalBaseLLM | None = None,
            async_mode: bool = True,
            verbose_mode: bool = True,
    ):
        if types is None:
            types = [FairnessSubcategory.BANKING]
        self.types = types
        self.async_mode = async_mode
        self.verbose_mode = verbose_mode
        self.simulator_model = simulator_model
        self.evaluation_model = evaluation_model
        self.default_attack_builder: BaseVulnerability | None = None
        super().__init__(types)

    def simulate_attacks(self, purpose: str = None) -> List[RTTestCase]:
        attacks: List[RTTestCase] = []

        if FairnessSubcategory.BANKING in self.types:
            for row in CSVLoader.load_prompts_from_csv(
                    file_path="2_schaedlich_manuell_erstellt_basic.csv",
                    categories=["fairness_banking"]
            ):
                attack = RTTestCase(
                    vulnerability=self.get_name(),
                    vulnerability_type=FairnessSubcategory.BANKING,
                    input=row.prompt
                )
                if row.document_path:
                    attack.file_path = row.document_path
                metadata = row.build_attack_metadata()
                if metadata is not None:
                    attack.metadata = metadata
                attacks.append(attack)
        return attacks

    def _get_metric(self) -> BaseRedTeamingMetric:
        return FairnessMetric(purpose="Bank chatbot that acts as an assistant for employees.", model=self.evaluation_model)

    def get_name(self) -> str:
        return "Fairness"
