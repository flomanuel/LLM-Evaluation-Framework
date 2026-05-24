#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.


from enum import Enum
from deepeval.models import DeepEvalBaseLLM
from testframework.redteam.builders.base_builder import BaseAttackBuilder
from testframework.redteam.metric_adapters import IndirectInstructionMetric
from testframework.redteam.metric_protocol import RedTeamingMetric
from testframework.redteam.test_case import RTTestCase
from testframework.testcases.indirect_instruction.subcategory import IndirectInstructionSubcategory
from testframework.util.csv_loader import CSVLoader


class IndirectInstructionAttacks(BaseAttackBuilder):
    """Class that builds indirect prompt injection attack prompts."""

    def __init__(
            self,
            types: list[Enum],
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
        super().__init__(types, simulator_model, evaluation_model, async_mode, verbose_mode)

    def simulate_attacks(self, purpose: str = None) -> list[RTTestCase]:
        """Simulate attacks for the test case."""
        attacks: list[RTTestCase] = []
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

            csv_data = CSVLoader.load_prompts_from_csv(
                file_path="2_schaedlich_manuell_erstellt_basic_ergaenzung.csv",
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

    def _get_metric(self, attack: RTTestCase) -> RedTeamingMetric:
        """Get the metric for the test case."""
        del attack
        return IndirectInstructionMetric(
            IndirectInstructionSubcategory.DOCUMENT_EMBEDDED_INSTRUCTIONS.value,
            model=self.evaluation_model,
        )

    def get_name(self) -> str:
        """Get the human-readable name of the test case."""
        return "IndirectInstruction"
