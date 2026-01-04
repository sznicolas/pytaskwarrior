# tests/test_dto.py

import pytest
from datetime import datetime
from uuid import uuid4

from src.taskwarrior.dto.task_dto import TaskInputDTO, TaskOutputDTO
from src.taskwarrior.enums import Priority, TaskStatus, RecurrencePeriod


def test_task_input_dto_creation():
    """Test creating a TaskInputDTO with valid data."""
    task = TaskInputDTO(
        description="Test task",
        priority=Priority.HIGH,
        project="TestProject",
        tags=["tag1", "tag2"],
        due="2023-12-31T23:59:59Z",
        scheduled="2023-12-30T00:00:00Z",
        wait="2023-12-29T00:00:00Z",
        until="2024-12-31T23:59:59Z",
        recur=RecurrencePeriod.WEEKLY,
        context="test_context",
    )

    assert task.description == "Test task"
    assert task.priority == Priority.HIGH
    assert task.project == "TestProject"
    assert task.tags == ["tag1", "tag2"]
    assert task.due == "2023-12-31T23:59:59Z"
    assert task.scheduled == "2023-12-30T00:00:00Z"
    assert task.wait == "2023-12-29T00:00:00Z"
    assert task.until == "2024-12-31T23:59:59Z"
    assert task.recur == RecurrencePeriod.WEEKLY
    assert task.context == "test_context"


def test_task_input_dto_empty_description_validation():
    """Test that empty description raises ValueError."""
    with pytest.raises(ValueError, match="Description cannot be empty"):
        TaskInputDTO(description="")


def test_task_input_dto_whitespace_description_validation():
    """Test that whitespace-only description raises ValueError."""
    with pytest.raises(ValueError, match="Description cannot be empty"):
        TaskInputDTO(description="   ")


def test_task_output_dto_creation():
    """Test creating a TaskOutputDTO with valid data."""
    task_uuid = uuid4()
    task = TaskOutputDTO(
        description="Test task",
        index=1,
        uuid=task_uuid,
        status=TaskStatus.PENDING,
        priority=Priority.HIGH,
        project="TestProject",
        tags=["tag1", "tag2"],
        entry="2023-12-28T00:00:00Z",
        start="2023-12-29T00:00:00Z",
        end="2023-12-30T00:00:00Z",
        modified="2023-12-31T00:00:00Z",
        due="2024-01-01T00:00:00Z",
        scheduled="2024-01-02T00:00:00Z",
        wait="2024-01-03T00:00:00Z",
        until="2024-01-04T00:00:00Z",
        recur=RecurrencePeriod.WEEKLY,
        context="test_context",
    )

    assert task.description == "Test task"
    assert task.index == 1
    assert task.uuid == task_uuid
    assert task.status == TaskStatus.PENDING
    assert task.priority == Priority.HIGH
    assert task.project == "TestProject"
    assert task.tags == ["tag1", "tag2"]
    assert task.entry == datetime.fromisoformat("2023-12-28T00:00:00+00:00")
    assert task.start == datetime.fromisoformat("2023-12-29T00:00:00+00:00")
    assert task.end == datetime.fromisoformat("2023-12-30T00:00:00+00:00")
    assert task.modified == datetime.fromisoformat("2023-12-31T00:00:00+00:00")
    assert task.due == datetime.fromisoformat("2024-01-01T00:00:00+00:00")
    assert task.scheduled == datetime.fromisoformat("2024-01-02T00:00:00+00:00")
    assert task.wait == datetime.fromisoformat("2024-01-03T00:00:00+00:00")
    assert task.until == datetime.fromisoformat("2024-01-04T00:00:00+00:00")
    assert task.recur == RecurrencePeriod.WEEKLY
    assert task.context == "test_context"


def test_task_output_dto_datetime_parsing():
    """Test datetime parsing from TaskWarrior format."""
    # Test standard ISO format
    task = TaskOutputDTO(
        description="Test",
        index=1,
        uuid=uuid4(),
        status=TaskStatus.PENDING,
        entry="2023-12-28T00:00:00Z",
        due="2024-01-01T00:00:00Z",
    )

    assert task.entry == datetime.fromisoformat("2023-12-28T00:00:00+00:00")
    assert task.due == datetime.fromisoformat("2024-01-01T00:00:00+00:00")


def test_task_output_dto_compact_datetime_parsing():
    """Test parsing of compact TaskWarrior datetime format."""
    # Test compact format (20260101T193139Z)
    task = TaskOutputDTO(
        description="Test",
        id=1,
        uuid=uuid4(),
        status=TaskStatus.PENDING,
        entry="20260101T193139Z",
        due="20260102T102030Z",
    )

    expected_entry = datetime.fromisoformat("2026-01-01T19:31:39+00:00")
    expected_due = datetime.fromisoformat("2026-01-02T10:20:30+00:00")

    assert task.entry == expected_entry
    assert task.due == expected_due


def test_task_input_dto_model_dump():
    """Test model_dump functionality."""
    task = TaskInputDTO(
        description="Test task", priority=Priority.HIGH, project="TestProject"
    )

    dumped = task.model_dump()
    assert dumped["description"] == "Test task"
    assert dumped["priority"] == Priority.HIGH
    assert dumped["project"] == "TestProject"


def test_task_output_dto_model_dump():
    """Test model_dump functionality."""
    task_uuid = uuid4()
    task = TaskOutputDTO(
        description="Test task",
        index=1,
        uuid=task_uuid,
        status=TaskStatus.PENDING,
        priority=Priority.HIGH,
    )

    dumped = task.model_dump(by_alias=True)
    assert dumped["description"] == "Test task"
    assert dumped["id"] == 1
    assert dumped["uuid"] == task_uuid
    assert dumped["status"] == TaskStatus.PENDING
    assert dumped["priority"] == Priority.HIGH


def test_task_output_to_input_conversion():
    """Test conversion from TaskOutputDTO to TaskInputDTO."""
    task_uuid = uuid4()
    output_task = TaskOutputDTO(
        description="Test task",
        index=1,
        uuid=task_uuid,
        status=TaskStatus.PENDING,
        priority=Priority.HIGH,
        project="TestProject",
        tags=["tag1", "tag2"],
    )

    # This function is defined in main.py
    from src.taskwarrior.main import task_output_to_input

    input_task = task_output_to_input(output_task)

    assert input_task.description == "Test task"
    assert input_task.priority == Priority.HIGH
    assert input_task.project == "TestProject"
    assert input_task.tags == ["tag1", "tag2"]
    # UUID should be excluded
    assert not hasattr(input_task, "uuid")
