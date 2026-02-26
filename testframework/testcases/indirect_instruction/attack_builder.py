from enum import Enum
from typing import List, Dict, cast
from deepteam.vulnerabilities import BaseVulnerability, IndirectInstruction
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
            async_mode: bool = True,
            verbose_mode: bool = True,
    ):
        self.types = types
        self.async_mode = async_mode
        self.verbose_mode = verbose_mode
        self.simulator_model = simulator_model
        self.default_attack_builder: IndirectInstruction | None = None
        super().__init__(types)

    def subcategory_to_indirect_instruction_type(self, subcategory) -> str | None:
        """Map IndirectInstructionSubcategory to DeepTeam IndirectInstructionType value."""
        mapping: Dict[IndirectInstructionSubcategory, str] = {
            IndirectInstructionSubcategory.RAG_INJECTION: IndirectInstructionType.RAG_INJECTION.value,
            IndirectInstructionSubcategory.DOCUMENT_EMBEDDED_INSTRUCTIONS: IndirectInstructionType.DOCUMENT_EMBEDDED_INSTRUCTIONS.value,
        }
        return mapping.get(subcategory)

    def simulate_attacks(self, purpose: str = None) -> List[RTTestCase]:
        attacks: List[RTTestCase] = []
        if IndirectInstructionSubcategory.DOCUMENT_EMBEDDED_INSTRUCTIONS in self.types:
            csv_data = CSVLoader.load_prompts_from_csv(
                file_path="2_schaedlich_manuell_erstellt_basic.csv",
                categories=["indirect-prompt-injection"]
            )
            for prompt, document_path in csv_data:
                attack = RTTestCase(
                    vulnerability=self.get_name(),
                    input=prompt
                )
                if document_path:
                    attack.file_path = document_path
                attacks.append(attack)

        deep_team_types: List[str] = []
        for subcategory in self.types:
            mapped_type = self.subcategory_to_indirect_instruction_type(subcategory)
            if mapped_type:
                deep_team_types.append(mapped_type)

        if deep_team_types:
            self.default_attack_builder = IndirectInstruction(
                simulator_model=self.simulator_model,
                types=deep_team_types
            )
            attacks.extend(self.default_attack_builder.simulate_attacks())

        return attacks

    def _get_metric(self, attack: RTTestCase) -> BaseRedTeamingMetric:
        if self.default_attack_builder:
            attack_type = cast(IndirectInstructionType, attack.vulnerability_type)
            return self.default_attack_builder._get_metric(type=attack_type)
        return IndirectInstructionMetric(IndirectInstructionType.DOCUMENT_EMBEDDED_INSTRUCTIONS.value)

    def get_name(self) -> str:
        return "IndirectInstruction"
