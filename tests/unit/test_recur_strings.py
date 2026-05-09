from __future__ import annotations

from src.taskwarrior.dto.task_dto import TaskInputDTO
from src.taskwarrior.enums import RecurrencePeriod


def test_task_input_accepts_custom_string_recur():
    """TaskInputDTO should accept custom TaskWarrior recurrence strings like '2weeks'."""
    task = TaskInputDTO(description="Test task", recur="2weeks")
    assert task.recur == "2weeks"


def test_task_input_accepts_iso8601_recur():
    """TaskInputDTO should accept ISO-8601 duration strings like 'P2W'."""
    task = TaskInputDTO(description="Test task", recur="P2W")
    assert task.recur == "P2W"


def test_task_input_enum_recur_still_works():
    """Ensure RecurrencePeriod enum values still work as before."""
    task = TaskInputDTO(description="Test task", recur=RecurrencePeriod.WEEKLY)
    assert task.recur == RecurrencePeriod.WEEKLY
