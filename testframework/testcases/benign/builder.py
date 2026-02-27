from enum import Enum
from typing import List
from deepteam.vulnerabilities import BaseVulnerability
from deepteam.metrics import HarmMetric  # type: ignore
from deepeval.models import DeepEvalBaseLLM
from deepteam.test_case import RTTestCase
from deepteam.metrics import BaseRedTeamingMetric  # type: ignore
from testframework.enums import Category, Severity
from testframework.testcases.benign.subcategory import BenignSubcategory
from testframework.util.csv_loader import CSVLoader


class BenignAttacks(BaseVulnerability):
    """Class that build benign prompts (i.e., no real attacks)"""

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

    def simulate_attacks(self, purpose: str = None) -> List[RTTestCase]:
        attacks: List[RTTestCase] = []
        if BenignSubcategory.BANKING in self.types:
            attacks.extend(
                RTTestCase(
                    vulnerability=self.get_name(),
                    vulnerability_type=BenignSubcategory.BANKING,
                    input=prompt)
                for prompt, _ in CSVLoader.load_prompts_from_csv(
                    file_path="1.1_harmlos_bank.csv",
                    categories=["benign_banking"],
                    severity=Severity.SAFE
                )
            )
        attacks.extend(
            RTTestCase(
                vulnerability=self.get_name(),
                vulnerability_type=Category.BENIGN,
                input=prompt)
            for prompt, _ in CSVLoader.load_prompts_from_csv(
                file_path="1_harmlos_aegis_20.csv",
                categories=["benign"],
                severity=Severity.SAFE
            )
        )

        return attacks

    def _get_metric(self) -> BaseRedTeamingMetric:
        return HarmMetric(harm_category="", model=self.evaluation_model)

    def get_name(self) -> str:
        return "Benign"
