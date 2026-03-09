#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.


from enum import Enum
from typing import List
from deepteam.vulnerabilities import BaseVulnerability
from deepteam.metrics import HarmMetric
from deepeval.models import DeepEvalBaseLLM
from deepteam.test_case import RTTestCase
from deepteam.metrics import BaseRedTeamingMetric
from testframework.enums import Category, Severity
from testframework.testcases.benign.subcategory import BenignSubcategory
from testframework.util.csv_loader import CSVLoader


class BenignAttacks(BaseVulnerability):
    """Class that build benign prompts (i.e., no real attacks)"""

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
        self.default_attack_builder: BaseVulnerability | None = None
        super().__init__(types)

    def simulate_attacks(self, purpose: str = None) -> List[RTTestCase]:
        attacks: List[RTTestCase] = []
        for row in CSVLoader.load_prompts_from_csv(
                file_path="1.1_harmlos_bank.csv",
                categories=["benign", "benign_banking"],
                severity=Severity.SAFE
        ):
            attack = RTTestCase(
                vulnerability=self.get_name(),
                vulnerability_type=BenignSubcategory.BANKING,
                input=row.prompt
            )
            metadata = row.build_attack_metadata()
            attack.metadata = metadata
            attacks.append(attack)
        for row in CSVLoader.load_prompts_from_csv(
                file_path="1_harmlos_aegis_20.csv",
                categories=["benign"],
                severity=Severity.SAFE
        ):
            attack = RTTestCase(
                vulnerability=self.get_name(),
                vulnerability_type=Category.BENIGN,
                input=row.prompt
            )
            metadata = row.build_attack_metadata()
            attack.metadata = metadata
            attacks.append(attack)

        return attacks

    def _get_metric(self) -> BaseRedTeamingMetric:
        return HarmMetric(
            harm_category="Data Leakage, PII, IBANS, Toxic content, Illegal Activities, Violence, "
                          "Bullying, Discrimination, Immoral and Unethical Behaviour, Programming Code, "
                          "Prompt Injections, etc.",
            model=self.evaluation_model)

    def get_name(self) -> str:
        return "Benign"
