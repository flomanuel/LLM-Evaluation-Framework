#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

"""Common abstractions for internal red-team attack builders."""

from enum import Enum
from typing import Any

from deepeval.models import DeepEvalBaseLLM

from testframework.enums import Severity
from testframework.redteam.test_case import RTTestCase
from testframework.util.csv_loader import CSVLoader


class BaseAttackBuilder:
    """Shared helper methods used by testcase-specific builders."""

    def __init__(
            self,
            types: list[Enum] | None,
            simulator_model: DeepEvalBaseLLM | None | str = None,
            evaluation_model: DeepEvalBaseLLM | None | str = None,
            async_mode: bool = True,
            verbose_mode: bool = True,
    ) -> None:
        self.types = types or []
        self.async_mode = async_mode
        self.verbose_mode = verbose_mode
        self.simulator_model = simulator_model
        self.evaluation_model = evaluation_model

    @staticmethod
    def build_attack(
            vulnerability: str,
            vulnerability_type: Any,
            prompt: str,
            metadata: dict[str, Any] | None = None,
    ) -> RTTestCase:
        """Build one project-owned red-team test case instance."""
        attack = RTTestCase(
            vulnerability=vulnerability,
            vulnerability_type=vulnerability_type,
            input=prompt,
        )
        if metadata is not None:
            attack.metadata = metadata
        return attack

    def load_attacks_from_csv(
            self,
            file_path: str,
            categories: list[str],
            vulnerability: str,
            vulnerability_type: Any,
            severity: Severity = Severity.UNSAFE,
            is_rag: bool = True,
    ) -> list[RTTestCase]:
        """Create attacks from one CSV source with shared metadata handling."""
        attacks: list[RTTestCase] = []
        rows = CSVLoader.load_prompts_from_csv(
            file_path=file_path,
            categories=categories,
            severity=severity,
        )
        for row in rows:
            attacks.append(
                self.build_attack(
                    vulnerability=vulnerability,
                    vulnerability_type=vulnerability_type,
                    prompt=row.prompt,
                    metadata=row.build_attack_metadata(is_rag=is_rag),
                )
            )
        return attacks
