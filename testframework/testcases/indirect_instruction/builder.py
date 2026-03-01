#  Copyright (c) 2026.
#  Florian Emanuel Sauer

from enum import Enum
from typing import List, Dict, cast
from deepteam.vulnerabilities import BaseVulnerability
from deepteam.metrics import IndirectInstructionMetric
from deepeval.models import DeepEvalBaseLLM
from deepteam.test_case import RTTestCase
from deepteam.metrics import BaseRedTeamingMetric
from deepteam.vulnerabilities.indirect_instruction import IndirectInstructionType
from testframework.testcases.indirect_instruction.subcategory import IndirectInstructionSubcategory
from testframework.util.csv_loader import CSVLoader


class IndirectInstructionAttacks(BaseVulnerability):
    """Class that builds indirect prompt injection attack prompts."""

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
        if IndirectInstructionSubcategory.DOCUMENT_EMBEDDED_INSTRUCTIONS in self.types:
            csv_data = CSVLoader.load_prompts_from_csv(
                file_path="2_schaedlich_manuell_erstellt_basic.csv",
                categories=["indirect-prompt-injection"]
            )
            for row in csv_data:
                attack = RTTestCase(
                    vulnerability=self.get_name(),
                    input=row.prompt,
                    vulnerability_type=IndirectInstructionSubcategory.DOCUMENT_EMBEDDED_INSTRUCTIONS
                )
                metadata = row.build_attack_metadata(is_rag=False)
                attack.metadata = metadata
                attacks.append(attack)

        return attacks

    def _get_metric(self, attack: RTTestCase) -> BaseRedTeamingMetric:
        return IndirectInstructionMetric(IndirectInstructionType.DOCUMENT_EMBEDDED_INSTRUCTIONS.value,
                                         model=self.evaluation_model)

    def get_name(self) -> str:
        return "IndirectInstruction"
