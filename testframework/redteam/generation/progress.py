#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

"""Progress helpers decoupled from DeepTeam utilities."""

from typing import Any

try:
    from rich.progress import Progress
except Exception:  # pragma: no cover - optional dependency behavior
    Progress = None


class _NoOpProgress:
    """Fallback progress object used when rich is unavailable."""

    def __enter__(self) -> "_NoOpProgress":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False

    @staticmethod
    def add_task(*args, **kwargs) -> int:
        return 0

    @staticmethod
    def update(*args, **kwargs) -> None:
        return None


def create_progress() -> Any:
    """Create a progress object with the same call shape as DeepTeam helpers."""
    if Progress is None:
        return _NoOpProgress()
    return Progress(transient=True)


def add_pbar(
        progress: Any,
        description: str,
        total: int,
) -> int:
    """Add one progress task and return the task id."""
    return progress.add_task(description=description, total=total)


def update_pbar(
        progress: Any,
        task_id: int,
        advance: int = 1,
        advance_to_end: bool = False,
) -> None:
    """Advance a progress task by one step or complete it."""
    if advance_to_end:
        try:
            task = progress.tasks[task_id]
            remaining = max(int(task.total or 0) - int(task.completed), 0)
            progress.update(task_id, advance=remaining)
            return
        except Exception:
            progress.update(task_id)
            return

    progress.update(task_id, advance=advance)
