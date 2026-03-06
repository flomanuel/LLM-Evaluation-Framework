#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.



from enum import Enum
from typing import List
from deepteam.vulnerabilities import BaseVulnerability
from deepeval.models import DeepEvalBaseLLM
from deepteam.test_case import RTTestCase
from deepteam.metrics import BaseRedTeamingMetric  # type: ignore
from testframework.metrics.privacy_violations import PrivacyViolationsMetric
from testframework.testcases.privacy_violations.subcategory import PrivacyViolationsSubcategory
from testframework.util.csv_loader import CSVLoader


class PrivacyViolationsAttacks(BaseVulnerability):
    """Class that builds privacy violations attack prompts."""

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
        super().__init__(types)

    def simulate_attacks(self, purpose: str = None) -> List[RTTestCase]:
        attacks: List[RTTestCase] = []
        for row in CSVLoader.load_prompts_from_csv(
                file_path="2_schaedlich_manuell_erstellt_basic.csv",
                categories=["privacy-violations"]
        ):
            attack = RTTestCase(
                vulnerability=self.get_name(),
                input=row.prompt,
                vulnerability_type=PrivacyViolationsSubcategory.CUSTOM
            )
            metadata = row.build_attack_metadata()
            attack.metadata = metadata
            attacks.append(attack)
        return attacks

    def _get_metric(self) -> BaseRedTeamingMetric:
        return PrivacyViolationsMetric(model=self.evaluation_model)

    def get_name(self) -> str:
        return "PrivacyViolations"
