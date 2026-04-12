"""TaskID — unified identifier for a TaskWarrior task.

A task can be referenced either by its working-set index (``int``) or by its
persistent UUID.  This class wraps both forms under a single type so that
every API method only needs one parameter type instead of ``str | int | UUID``.
"""

from __future__ import annotations

from uuid import UUID

from ..exceptions import TaskValidationError


class TaskID:
    """Unified identifier for a TaskWarrior task.

    A ``TaskID`` holds either the task's working-set index (a positive integer)
    or its UUID, and produces the correct string representation for the
    TaskWarrior CLI via ``str(task_id)``.

    TaskWarrior also supports partial UUID prefixes; these are accepted as-is
    when provided as a plain string.

    Args:
        value: The task identifier — one of:

            * ``int``  — working-set index (must be > 0).
            * ``UUID`` — the task's persistent UUID.
            * ``str``  — a UUID string, an integer string, or a UUID prefix.

    Raises:
        TaskValidationError: If *value* is an integer ≤ 0 or an empty string.

    Example:
        >>> TaskID(1)
        TaskID('1')
        >>> TaskID("abc-def-uuid")
        TaskID('abc-def-uuid')
        >>> TaskID(some_uuid_obj)
        TaskID('550e8400-e29b-41d4-a716-446655440000')

        Factory from an existing task output::

            task = tw.get_task(TaskID(1))
            tw.done_task(TaskID.from_task(task))
    """

    __slots__ = ("_value",)

    def __init__(self, value: str | int | UUID) -> None:
        if isinstance(value, int):
            if value <= 0:
                raise TaskValidationError(
                    f"Task working-set index must be a positive integer, got {value}"
                )
            self._value: str = str(value)
        elif isinstance(value, UUID):
            self._value = str(value)
        elif isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                raise TaskValidationError("TaskID string cannot be empty")
            self._value = stripped
        else:
            raise TaskValidationError(
                f"TaskID requires str, int, or UUID — got {type(value).__name__!r}"
            )

    @classmethod
    def from_task(cls, task: TaskOutputDTO) -> TaskID:  # type: ignore[name-defined]  # noqa: F821
        """Create a ``TaskID`` from the UUID of an existing task output.

        Args:
            task: A :class:`~taskwarrior.dto.task_dto.TaskOutputDTO` instance.

        Returns:
            A ``TaskID`` wrapping the task's UUID.

        Example:
            >>> task = tw.get_task(TaskID(1))
            >>> tw.done_task(TaskID.from_task(task))
        """
        return cls(task.uuid)

    def __str__(self) -> str:
        return self._value

    def __repr__(self) -> str:
        return f"TaskID({self._value!r})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, TaskID):
            return self._value == other._value
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self._value)


# Type alias to reduce repeated unions across the codebase
type TaskRef = str | int | UUID | TaskID
