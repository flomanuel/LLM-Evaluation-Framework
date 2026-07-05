#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

from datetime import datetime, timezone
from typing import Any

import testframework.persistence.session as _session_mod
from testframework.models import AnalysisRunResult
from testframework.persistence.entity.analysis import AnalysisRunEntity, SummaryErrorEntity, SummaryRowEntity
from testframework.persistence.repository.analysis_repository import AnalysisRepository
from testframework.persistence.repository.mapper import analysis_run_from_entity, run_result_from_entity
from testframework.persistence.repository.test_run_repository import TestRunRepository
from testframework.reporting.run_summary import RunSummary


class AnalysisService:
    """Build and persist per-run confusion-matrix summaries from DB data."""

    def summarize_and_store(
        self,
        run_id: str,
        exclude_scanners: bool = False,
        consider_chatbot_success: bool = False,
    ) -> dict[str, Any]:
        """
        Load the run from the DB, compute the summary, persist it as an
        analysis_run + summary_row/error rows, and return the raw summary dict.
        """
        with _session_mod.Session() as session:
            run_entity = TestRunRepository(session).find_by_id(run_id)
            if run_entity is None:
                raise ValueError(f"TestRun {run_id} not found")
            run_dto = run_result_from_entity(run_entity)

            summary = self._build_summary_from_dto(
                run_dto, exclude_scanners=exclude_scanners, consider_chatbot_success=consider_chatbot_success
            )

            analysis_entity = self._dto_summary_to_entity(
                run_id=run_id,
                summary=summary,
                exclude_scanners=exclude_scanners,
                consider_chatbot_success=consider_chatbot_success,
            )
            # Explicitly set the relationship so SQLAlchemy does not null out the FK:
            # MappedAsDataclass sets init=False fields (like test_run=None) AFTER init=True
            # fields in __init__, which would otherwise override the run_id FK during flush.
            analysis_entity.test_run = run_entity
            AnalysisRepository(session).save(analysis_entity)
            session.commit()

        return summary

    def find_by_run_id(self, run_id: str) -> list[AnalysisRunResult]:
        """Return all stored analyses for a run as DTOs."""
        with _session_mod.Session() as session:
            entities = AnalysisRepository(session).find_by_run_id(run_id)
            return [analysis_run_from_entity(e) for e in entities]

    def find_by_id(self, analysis_id: int) -> AnalysisRunResult | None:
        """Return a single analysis by id, or None if not found."""
        with _session_mod.Session() as session:
            entity = AnalysisRepository(session).find_by_id(analysis_id)
            if entity is None:
                return None
            return analysis_run_from_entity(entity)

    def _build_summary_from_dto(
        self,
        run_dto,
        exclude_scanners: bool,
        consider_chatbot_success: bool,
    ) -> dict[str, Any]:
        """Re-use the existing RunSummary logic operating on the DTO's dict representation."""
        from dataclasses import asdict
        import json

        # Serialize the DTO to the same dict format RunSummary reads from JSON
        run_dict = json.loads(json.dumps(asdict(run_dto), default=str))

        summary = RunSummary._build_from_dict(
            run_dict,
            exclude_scanners=exclude_scanners,
            consider_chatbot_success=consider_chatbot_success,
        )
        return summary

    @staticmethod
    def _dto_summary_to_entity(
        run_id: str,
        summary: dict[str, Any],
        exclude_scanners: bool,
        consider_chatbot_success: bool,
    ) -> AnalysisRunEntity:
        entity = AnalysisRunEntity(
            run_id=run_id,
            exclude_scanners=exclude_scanners,
            consider_chatbot_success=consider_chatbot_success,
            created_at=datetime.now(timezone.utc),
        )
        rows: list[SummaryRowEntity] = []
        errors: list[SummaryErrorEntity] = []

        for model_name, model_summary in summary.items():
            for node_name, node in model_summary.items():
                if node_name == "_errors":
                    for attack_category, count in node.items():
                        errors.append(SummaryErrorEntity(
                            analysis_run_id=0,
                            node=model_name,
                            attack_category=attack_category,
                            count=count,
                        ))
                    continue

                rows.append(SummaryRowEntity(
                    analysis_run_id=0,
                    node=f"{model_name}/{node_name}",
                    scope="overall",
                    attack_category="",
                    technique="",
                    count=node.get("count", 0),
                    tp=node.get("TP", 0),
                    fp=node.get("FP", 0),
                    tn=node.get("TN", 0),
                    fn=node.get("FN", 0),
                ))

                for attack_category, category_node in node.get("per_attack_category", {}).items():
                    rows.append(SummaryRowEntity(
                        analysis_run_id=0,
                        node=f"{model_name}/{node_name}",
                        scope="attack_category",
                        attack_category=attack_category,
                        technique="",
                        count=category_node.get("count", 0),
                        tp=category_node.get("TP", 0),
                        fp=category_node.get("FP", 0),
                        tn=category_node.get("TN", 0),
                        fn=category_node.get("FN", 0),
                    ))

                    for technique, technique_node in category_node.get("per_technique", {}).items():
                        rows.append(SummaryRowEntity(
                            analysis_run_id=0,
                            node=f"{model_name}/{node_name}",
                            scope="technique",
                            attack_category=attack_category,
                            technique=technique,
                            count=technique_node.get("count", 0),
                            tp=technique_node.get("TP", 0),
                            fp=technique_node.get("FP", 0),
                            tn=technique_node.get("TN", 0),
                            fn=technique_node.get("FN", 0),
                        ))

        entity.summary_rows = rows
        entity.summary_errors = errors
        return entity
