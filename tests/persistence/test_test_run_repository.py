#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from testframework.persistence.entity.test_run import TestRunEntity
from testframework.persistence.repository.test_run_repository import TestRunRepository


_NOW = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


def _new_run_entity(run_id: str | None = None) -> TestRunEntity:
    return TestRunEntity(
        run_id=run_id or str(uuid4()),
        start_ts=_NOW,
        end_ts=_NOW,
    )


def test_save_and_find_by_id(db_session):
    repo = TestRunRepository(db_session)
    run_id = str(uuid4())
    entity = _new_run_entity(run_id)

    saved = repo.save(entity)
    assert saved.run_id == run_id

    found = repo.find_by_id(run_id)
    assert found is not None
    assert found.run_id == run_id
    assert found.start_ts == _NOW


def test_find_by_id_returns_none_for_missing(db_session):
    repo = TestRunRepository(db_session)
    assert repo.find_by_id("nonexistent-id") is None


def test_exists_true_after_save(db_session):
    repo = TestRunRepository(db_session)
    run_id = str(uuid4())
    repo.save(_new_run_entity(run_id))
    assert repo.exists(run_id) is True


def test_exists_false_when_not_saved(db_session):
    repo = TestRunRepository(db_session)
    assert repo.exists(str(uuid4())) is False


def test_find_all_returns_saved_runs(db_session):
    repo = TestRunRepository(db_session)
    ids = [str(uuid4()) for _ in range(3)]
    for run_id in ids:
        repo.save(_new_run_entity(run_id))

    found_ids = {r.run_id for r in repo.find_all()}
    assert set(ids) <= found_ids


def test_delete_removes_run(db_session):
    repo = TestRunRepository(db_session)
    run_id = str(uuid4())
    repo.save(_new_run_entity(run_id))
    assert repo.exists(run_id)

    repo.delete(run_id)
    assert not repo.exists(run_id)
