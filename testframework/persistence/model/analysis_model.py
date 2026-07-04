#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from pydantic import BaseModel

from testframework.persistence.entity.analysis import AnalysisRunEntity


class AnalysisRunInputModel(BaseModel):
    """Input model for triggering an analysis run for a given test run."""

    run_id: UUID
    exclude_scanners: bool = False
    consider_chatbot_success: bool = False

    def to_entity(self) -> AnalysisRunEntity:
        return AnalysisRunEntity(
            run_id=str(self.run_id),
            exclude_scanners=self.exclude_scanners,
            consider_chatbot_success=self.consider_chatbot_success,
            created_at=datetime.now(timezone.utc),
        )
