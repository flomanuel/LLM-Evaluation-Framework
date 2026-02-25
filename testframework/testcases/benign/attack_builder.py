from enum import Enum
from typing import List
from deepteam.vulnerabilities import BaseVulnerability
from deepteam.metrics import HarmMetric # type: ignore
from deepeval.models import DeepEvalBaseLLM
from deepteam.test_case import RTTestCase
from deepteam.metrics import BaseRedTeamingMetric # type: ignore
from testframework.enums import Category
from testframework.testcases.benign.test_Case import Subcategory
from testframework.util.csv_loader import CSVLoader

class BenignAttacks(BaseVulnerability):
    """Class that build benign prompts (i.e. no real attacks)"""

    def __init__(
        self,
        types: List[Enum],
        simulator_model: DeepEvalBaseLLM | None = None,
        async_mode: bool = True,
        verbose_mode: bool = True,
        ):
        self.types = types
        self.async_mode = async_mode
        self.verbose_mode = verbose_mode
        self.simulator_model = simulator_model
        self.default_attack_builder:BaseVulnerability | None  = None
        super().__init__(types)

    def simulate_attacks(self, purpose: str) -> List[RTTestCase]:
        attacks: List[RTTestCase] = []

        if Subcategory.BANKING in self.types:
            attacks.extend(
                RTTestCase(
                    vulnerability=self.get_name(),
                    vulnerability_type=Subcategory.BANKING,
                    input=prompt)
                for prompt in CSVLoader.load_prompts_from_csv(file_path="1.1_harmlos_bank.csv", categories=["benign_banking"])
                )
        else:
            attacks.extend(
                RTTestCase(
                    vulnerability=self.get_name(),
                    vulnerability_type=Category.BENIGN,
                    input=prompt)
                for prompt in CSVLoader.load_prompts_from_csv(file_path="1_harmlos_aegis_20.csv")
                )
            return attacks

    def _get_metric(self, attack: RTTestCase) -> BaseRedTeamingMetric:
        return HarmMetric(harm_category="")

    def get_name(self) -> str:
        return "Benign"
