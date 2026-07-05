#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from testframework.persistence.entity.analysis import AnalysisRunEntity, SummaryErrorEntity, SummaryRowEntity


class AnalysisRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, entity: AnalysisRunEntity) -> AnalysisRunEntity:
        """Persist an analysis run with its rows and errors."""
        self._session.add(entity)
        self._session.flush()
        return entity

    def find_by_id(self, analysis_id: int) -> AnalysisRunEntity | None:
        """Return a single analysis run by its id, or None if not found."""
        stmt = (
            select(AnalysisRunEntity)
            .where(AnalysisRunEntity.id == analysis_id)
            .options(
                selectinload(AnalysisRunEntity.summary_rows),
                selectinload(AnalysisRunEntity.summary_errors),
            )
        )
        return self._session.scalars(stmt).first()

    def find_by_run_id(self, run_id: str) -> list[AnalysisRunEntity]:
        """Return all analysis runs for a given test run."""
        stmt = (
            select(AnalysisRunEntity)
            .where(AnalysisRunEntity.run_id == run_id)
            .options(
                selectinload(AnalysisRunEntity.summary_rows),
                selectinload(AnalysisRunEntity.summary_errors),
            )
        )
        return list(self._session.scalars(stmt).all())

    def find_latest(
        self,
        run_id: str,
        exclude_scanners: bool,
        consider_chatbot_success: bool,
    ) -> AnalysisRunEntity | None:
        """Return the most-recently-created analysis for the given parameter combination."""
        stmt = (
            select(AnalysisRunEntity)
            .where(
                AnalysisRunEntity.run_id == run_id,
                AnalysisRunEntity.exclude_scanners == exclude_scanners,
                AnalysisRunEntity.consider_chatbot_success == consider_chatbot_success,
            )
            .order_by(AnalysisRunEntity.created_at.desc())
            .limit(1)
            .options(
                selectinload(AnalysisRunEntity.summary_rows),
                selectinload(AnalysisRunEntity.summary_errors),
            )
        )
        return self._session.scalars(stmt).first()
