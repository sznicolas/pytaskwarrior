"""Adapter interfaces for pytaskwarrior.

This module exposes the :class:`AdapterProtocol` that any backend adapter
must satisfy, enabling dependency injection and testability.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ..dto.task_dto import TaskInputDTO, TaskOutputDTO
from ..dto.task_id import TaskRef


@runtime_checkable
class AdapterProtocol(Protocol):
    """Structural protocol satisfied by every pytaskwarrior adapter.

    Both :class:`~taskwarrior.adapters.taskwarrior_adapter.TaskWarriorAdapter`
    (subprocess-based) and
    :class:`~taskwarrior.adapters.taskchampion_adapter.TaskChampionAdapter`
    (direct SQLite via taskchampion-py) implement this protocol.
    """

    def add_task(self, task: TaskInputDTO) -> TaskOutputDTO: ...

    def modify_task(self, task: TaskInputDTO, task_id: TaskRef) -> TaskOutputDTO: ...

    def get_task(self, task_id: TaskRef, filter_args: str = "") -> TaskOutputDTO: ...

    def get_tasks(
        self,
        filter: str = "",
        include_completed: bool = False,
        include_deleted: bool = False,
    ) -> list[TaskOutputDTO]: ...

    def get_recurring_task(self, task_id: TaskRef) -> TaskOutputDTO: ...

    def get_recurring_instances(self, task_id: TaskRef) -> list[TaskOutputDTO]: ...

    def delete_task(self, task_id: TaskRef) -> None: ...

    def purge_task(self, task_id: TaskRef) -> None: ...

    def done_task(self, task_id: TaskRef) -> None: ...

    def start_task(self, task_id: TaskRef) -> None: ...

    def stop_task(self, task_id: TaskRef) -> None: ...

    def annotate_task(self, task_id: TaskRef, annotation: str) -> None: ...

    def synchronize(self) -> None: ...

    def is_sync_configured(self) -> bool: ...

    def task_calc(self, date_str: str) -> str: ...

    def task_date_validator(self, date_str: str) -> bool: ...

    def get_version(self) -> str: ...

    def get_projects(self) -> list[str]: ...

    def get_tags(self, include_virtual_tags: bool = False) -> list[str]: ...
