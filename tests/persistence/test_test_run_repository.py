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


def test_find_page_orders_newest_first_and_paginates(db_session):
    """The shared container accumulates committed rows from every other test in the
    session (only db_session's OWN writes roll back, pre-existing committed rows from
    other tests remain visible), so every case here scopes down via a private
    run_status marker to get exact, collision-free totals.
    """
    repo = TestRunRepository(db_session)
    marker = f"test_marker_{uuid4()}"
    ids = [str(uuid4()) for _ in range(3)]
    for i, run_id in enumerate(ids):
        repo.save(TestRunEntity(
            run_id=run_id,
            start_ts=datetime(2026, 1, i + 1, tzinfo=timezone.utc),
            end_ts=None,
            status=marker,
        ))

    rows, total = repo.find_page(run_status=marker, offset=0, limit=2)
    assert total == 3
    assert [r.run_id for r in rows] == [ids[2], ids[1]]  # newest (Jan 3) first

    rows_page2, total2 = repo.find_page(run_status=marker, offset=2, limit=2)
    assert total2 == 3
    assert [r.run_id for r in rows_page2] == [ids[0]]


def test_find_page_filters_by_status(db_session):
    repo = TestRunRepository(db_session)
    marker = f"test_marker_{uuid4()}"
    matching_id = str(uuid4())
    repo.save(TestRunEntity(run_id=matching_id, start_ts=_NOW, end_ts=None, status=marker))
    repo.save(TestRunEntity(run_id=str(uuid4()), start_ts=_NOW, end_ts=None, status=f"other_{marker}"))

    rows, total = repo.find_page(run_status=marker, offset=0, limit=20)
    assert total == 1
    assert rows[0].run_id == matching_id


def test_find_page_filters_by_start_date_range(db_session):
    repo = TestRunRepository(db_session)
    marker = f"test_marker_{uuid4()}"
    early_id = str(uuid4())
    late_id = str(uuid4())
    repo.save(TestRunEntity(
        run_id=early_id, start_ts=datetime(2020, 1, 1, tzinfo=timezone.utc), end_ts=None, status=marker
    ))
    repo.save(TestRunEntity(
        run_id=late_id, start_ts=datetime(2030, 1, 1, tzinfo=timezone.utc), end_ts=None, status=marker
    ))

    rows, total = repo.find_page(
        run_status=marker, start_after=datetime(2025, 1, 1, tzinfo=timezone.utc), offset=0, limit=20
    )
    assert total == 1
    assert rows[0].run_id == late_id
