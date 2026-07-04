#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from testframework.persistence.entity.attack import AttackEntity
from testframework.persistence.entity.chatbot_response import (
    ChatbotResponseEntity,
    ChatbotResponseEvaluationEntity,
)
from testframework.persistence.entity.detection import (
    DetectionElementEntity,
    DetectionResultEntity,
    ScannerDetailEntity,
)
from testframework.persistence.entity.test_case import TestCaseEntity
from testframework.persistence.entity.test_run import TestRunEntity


def _load_options():
    """Return selectinload options that eagerly load the full aggregate."""
    return [
        selectinload(TestRunEntity.test_cases).selectinload(TestCaseEntity.attacks).options(
            selectinload(AttackEntity.evaluations).selectinload(
                ChatbotResponseEvaluationEntity.chatbot_response
            ),
            selectinload(AttackEntity.detection_results).selectinload(
                DetectionResultEntity.detection_elements
            ).options(
                selectinload(DetectionElementEntity.scanner_details),
                selectinload(DetectionElementEntity.prompt_hardening_chatbot_response),
            ),
        ),
    ]


class TestRunRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, entity: TestRunEntity) -> TestRunEntity:
        """Persist a new test run aggregate."""
        self._session.add(entity)
        self._session.flush()
        return entity

    def find_by_id(self, run_id: str) -> TestRunEntity | None:
        """Load a full test run aggregate by run_id."""
        stmt = (
            select(TestRunEntity)
            .where(TestRunEntity.run_id == run_id)
            .options(*_load_options())
        )
        return self._session.scalars(stmt).first()

    def find_all(self) -> list[TestRunEntity]:
        """Load all test run aggregates (shallow — no nested loading)."""
        return list(self._session.scalars(select(TestRunEntity)).all())

    def exists(self, run_id: str) -> bool:
        """Return True if a run with the given run_id is present."""
        stmt = select(TestRunEntity.run_id).where(TestRunEntity.run_id == run_id)
        return self._session.scalars(stmt).first() is not None

    def delete(self, run_id: str) -> None:
        """Delete a test run and all its children (via CASCADE)."""
        entity = self._session.get(TestRunEntity, run_id)
        if entity is not None:
            self._session.delete(entity)
            self._session.flush()
