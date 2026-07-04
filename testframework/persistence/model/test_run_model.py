#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from testframework.persistence.entity.test_case import TestCaseEntity
from testframework.persistence.entity.test_run import TestRunEntity


class TestRunInputModel(BaseModel):
    """Input model for creating a new test run."""

    run_id: UUID
    start_ts: datetime
    end_ts: datetime | None = None

    def to_entity(self) -> TestRunEntity:
        return TestRunEntity(
            run_id=str(self.run_id),
            start_ts=self.start_ts,
            end_ts=self.end_ts,
        )


class TestCaseInputModel(BaseModel):
    """Input model for adding a test case to a run."""

    category: str = Field(min_length=1)
    model_attack_generation: str | None = None
    subcategories: list[str] = Field(default_factory=list)

    def to_entity(self) -> TestCaseEntity:
        entity = TestCaseEntity(
            run_id="",  # FK set by caller after linking to a TestRunEntity
            category=self.category,
            model_attack_generation=self.model_attack_generation,
            subcategories=self.subcategories,
        )
        return entity
