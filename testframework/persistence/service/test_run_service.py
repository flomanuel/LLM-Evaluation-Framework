#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

from datetime import datetime, timezone

import testframework.persistence.session as _session_mod
from testframework.models import TestCaseResult, TestRunResult
from testframework.persistence.entity.test_run import TestRunEntity
from testframework.persistence.repository.mapper import (
    case_result_to_entity,
    run_result_from_entity,
    run_result_to_entity,
)
from testframework.persistence.repository.test_run_repository import TestRunRepository


class TestRunService:
    """Orchestrates test run persistence — transaction boundaries live here."""

    def start_run(self, run_id: str, start_ts: datetime) -> None:
        """Insert a new test_run row so incremental per-case writes have a parent."""
        with _session_mod.Session() as session:
            repo = TestRunRepository(session)
            entity = TestRunEntity(run_id=run_id, start_ts=start_ts)
            repo.save(entity)
            session.commit()

    def persist_test_case(self, run_id: str, tc: TestCaseResult) -> None:
        """Append a completed test case to an in-progress run."""
        with _session_mod.Session() as session:
            repo = TestRunRepository(session)
            tc_entity = case_result_to_entity(tc, run_id)
            run_entity = session.get(TestRunEntity, run_id)
            if run_entity is None:
                raise ValueError(f"TestRun {run_id} not found — call start_run first")
            run_entity.test_cases.append(tc_entity)
            session.commit()

    def finalize_run(self, run_id: str, end_ts: datetime) -> None:
        """Set the end timestamp on a completed run."""
        with _session_mod.Session() as session:
            run_entity = session.get(TestRunEntity, run_id)
            if run_entity is None:
                raise ValueError(f"TestRun {run_id} not found")
            run_entity.end_ts = end_ts
            session.commit()

    def persist_full_run(self, run: TestRunResult) -> None:
        """Persist a fully-assembled TestRunResult in one transaction (e.g., importer)."""
        with _session_mod.Session() as session:
            repo = TestRunRepository(session)
            entity = run_result_to_entity(run)
            repo.save(entity)
            session.commit()

    def get_run(self, run_id: str) -> TestRunResult | None:
        """Load a test run and return it as a DTO."""
        with _session_mod.Session() as session:
            repo = TestRunRepository(session)
            entity = repo.find_by_id(run_id)
            if entity is None:
                return None
            return run_result_from_entity(entity)

    def exists(self, run_id: str) -> bool:
        """Return True if a run with this ID is in the DB."""
        with _session_mod.Session() as session:
            return TestRunRepository(session).exists(run_id)

    def delete(self, run_id: str) -> None:
        """Delete a test run and all its children."""
        with _session_mod.Session() as session:
            TestRunRepository(session).delete(run_id)
            session.commit()
