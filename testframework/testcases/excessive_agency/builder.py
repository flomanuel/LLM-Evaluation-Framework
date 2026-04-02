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

from testframework.testcases.excessive_agency.subcategory import ExcessiveAgencySubcategory
from testframework.util.csv_loader import CSVLoader


class ExcessiveAgencyAttacks(BaseVulnerability):
    """Class that builds excessive agency attack prompts."""

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
        """Simulate attacks for the test case."""
        attacks: List[RTTestCase] = []
        for row in CSVLoader.load_prompts_from_csv(
                file_path="2_schaedlich_manuell_erstellt_basic.csv",
                categories=["excessive-agency"]
        ):
            attack = RTTestCase(
                vulnerability=self.get_name(),
                input=row.prompt,
                vulnerability_type=ExcessiveAgencySubcategory.CUSTOM
            )
            metadata = row.build_attack_metadata()
            attack.metadata = metadata
            attacks.append(attack)
        return attacks

    def _get_metric(self) -> BaseRedTeamingMetric:
        """Get the metric for the test case."""
        return HarmMetric(harm_category="Excessive Agency", model=self.evaluation_model)

    def get_name(self) -> str:
        """Get the human-readable name of the test case."""
        return "ExcessiveAgency"
