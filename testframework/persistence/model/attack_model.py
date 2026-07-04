#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

from __future__ import annotations

from pydantic import BaseModel, Field

from testframework.enums import Severity
from testframework.persistence.entity.attack import AttackEntity


class AttackInputModel(BaseModel):
    """Input model for adding an attack to a test case."""

    category: str = Field(min_length=1)
    severity: Severity
    prompt_baseline: str = Field(min_length=1)
    prompt_enhanced: str = Field(min_length=1)
    subcategory: str | None = None
    techniques: list[str] = Field(default_factory=list)

    def to_entity(self) -> AttackEntity:
        entity = AttackEntity(
            test_case_id=0,  # FK set by caller after linking to a TestCaseEntity
            category=self.category,
            severity=self.severity,
            prompt_baseline=self.prompt_baseline,
            prompt_enhanced=self.prompt_enhanced,
            subcategory=self.subcategory,
            techniques=self.techniques,
        )
        return entity
