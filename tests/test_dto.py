from __future__ import annotations

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
        index=1,
        uuid=uuid4(),
        status=TaskStatus.PENDING,
        entry="20260101T193139Z",
        due="20260102T102030Z",
    )

    expected_entry = datetime.fromisoformat("2026-01-01T19:31:39+00:00")
    expected_due = datetime.fromisoformat("2026-01-02T10:20:30+00:00")

    assert task.entry == expected_entry
    assert task.due == expected_due


def test_task_output_dto_datetime_parsing_comprehensive():
    """Test comprehensive datetime parsing from various TaskWarrior formats."""
    task_uuid = uuid4()
    
    # Test with standard ISO format
    task1 = TaskOutputDTO(
        description="Test task 1",
        index=1,
        uuid=task_uuid,
        status=TaskStatus.PENDING,
        entry="2023-12-28T00:00:00Z",
        due="2024-01-01T00:00:00Z",
    )
    
    assert task1.entry == datetime.fromisoformat("2023-12-28T00:00:00+00:00")
    assert task1.due == datetime.fromisoformat("2024-01-01T00:00:00+00:00")
    
    # Test with compact format
    task2 = TaskOutputDTO(
        description="Test task 2",
        index=2,
        uuid=task_uuid,
        status=TaskStatus.PENDING,
        entry="20260101T193139Z",
        due="20260102T102030Z",
    )
    
    expected_entry = datetime.fromisoformat("2026-01-01T19:31:39+00:00")
    expected_due = datetime.fromisoformat("2026-01-02T10:20:30+00:00")
    
    assert task2.entry == expected_entry
    assert task2.due == expected_due


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


def test_task_output_to_input_conversion_comprehensive():
    """Test comprehensive conversion from TaskOutputDTO to TaskInputDTO."""
    task_uuid = uuid4()
    output_task = TaskOutputDTO(
        description="Test task",
        index=1,
        uuid=task_uuid,
        status=TaskStatus.PENDING,
        priority=Priority.HIGH,
        project="TestProject",
        tags=["tag1", "tag2"],
        due="2024-01-01T00:00:00Z",
        scheduled="2023-12-31T00:00:00Z",
        wait="2023-12-30T00:00:00Z",
        recur=RecurrencePeriod.WEEKLY,
    )

    from src.taskwarrior.main import task_output_to_input
    
    input_task = task_output_to_input(output_task)

    assert input_task.description == "Test task"
    assert input_task.priority == Priority.HIGH
    assert input_task.project == "TestProject"
    assert input_task.tags == ["tag1", "tag2"]
    assert input_task.due == "2024-01-01T00:00:00+00:00"
    assert input_task.scheduled == "2023-12-31T00:00:00+00:00"
    assert input_task.wait == "2023-12-30T00:00:00+00:00"
    assert input_task.recur == RecurrencePeriod.WEEKLY
    # UUID should be excluded
    assert not hasattr(input_task, "uuid")


def test_task_output_dto_from_taskwarrior_json_export():
    """Test creating TaskOutputDTO from TaskWarrior JSON export string."""
    import json
    
    # This is the exact JSON string as exported by TaskWarrior
    taskwarrior_json = '''[
        {"id":1,"description":"toto","entry":"20260103T211028Z","modified":"20260103T211028Z","status":"pending","uuid":"a17d5011-0720-4311-83f1-c4eee7915415","urgency":0}
    ]'''
    
    # Parse the JSON string
    data = json.loads(taskwarrior_json)
    
    # Create TaskOutputDTO from the parsed data
    task = TaskOutputDTO(**data[0])
    
    # Verify all fields are correctly parsed
    assert task.index == 1  # The 'id' field maps to the 'index' field
    assert task.description == "toto"
    assert task.entry.isoformat() == "2026-01-03T21:10:28+00:00"
    assert task.modified.isoformat() == "2026-01-03T21:10:28+00:00"
    assert task.status == TaskStatus.PENDING
    assert str(task.uuid) == "a17d5011-0720-4311-83f1-c4eee7915415"
    
    # Verify serialization back to JSON uses 'id' key
    dumped = task.model_dump(by_alias=True)
    assert dumped["id"] == 1
    assert dumped["description"] == "toto"
    assert dumped["uuid"] == task.uuid
    assert dumped["status"] == TaskStatus.PENDING

    # New tests added below:

def test_task_input_dto_all_fields():
    """Test TaskInputDTO with all fields."""
    task = TaskInputDTO(
        description="Test task",
        priority=Priority.HIGH,
        project="TestProject",
        tags=["tag1", "tag2"],
        due="2026-12-31T23:59:59Z",
        scheduled="2026-01-15T00:00:00Z",
        wait="2026-01-10T12:30:45Z",
        until="2027-01-01T00:00:00Z",
        recur=RecurrencePeriod.WEEKLY,
        context="test_context",
        depends=[uuid4(), uuid4()]
    )
    
    assert task.description == "Test task"
    assert task.priority == Priority.HIGH
    assert task.project == "TestProject"
    assert task.tags == ["tag1", "tag2"]
    assert task.due == "2026-12-31T23:59:59Z"
    assert task.scheduled == "2026-01-15T00:00:00Z"
    assert task.wait == "2026-01-10T12:30:45Z"
    assert task.until == "2027-01-01T00:00:00Z"
    assert task.recur == RecurrencePeriod.WEEKLY
    assert task.context == "test_context"
    assert isinstance(task.depends, list)

def test_task_output_dto_all_fields():
    """Test TaskOutputDTO with all fields."""
    task_uuid = uuid4()
    task = TaskOutputDTO(
        description="Test task",
        index=1,
        uuid=task_uuid,
        status=TaskStatus.PENDING,
        priority=Priority.HIGH,
        project="TestProject",
        tags=["tag1", "tag2"],
        entry="20260101T193139Z",
        start="20260102T102030Z",
        end="20260103T154522Z",
        modified="20260104T083015Z",
        due="20260105T221045Z",
        scheduled="20260106T112030Z",
        wait="20260107T091545Z",
        until="20260108T143020Z",
        recur=RecurrencePeriod.WEEKLY,
        context="test_context"
    )
    
    assert task.description == "Test task"
    assert task.index == 1
    assert task.uuid == task_uuid
    assert task.status == TaskStatus.PENDING
    assert task.priority == Priority.HIGH
    assert task.project == "TestProject"
    assert task.tags == ["tag1", "tag2"]
    assert task.entry.isoformat() == "2026-01-01T19:31:39+00:00"
    assert task.start.isoformat() == "2026-01-02T10:20:30+00:00"
    assert task.end.isoformat() == "2026-01-03T15:45:22+00:00"
    assert task.modified.isoformat() == "2026-01-04T08:30:15+00:00"
    assert task.due.isoformat() == "2026-01-05T22:10:45+00:00"
    assert task.scheduled.isoformat() == "2026-01-06T11:20:30+00:00"
    assert task.wait.isoformat() == "2026-01-07T09:15:45+00:00"
    assert task.until.isoformat() == "2026-01-08T14:30:20+00:00"
    assert task.recur == RecurrencePeriod.WEEKLY
    assert task.context == "test_context"

def test_task_input_dto_validation_edge_cases():
    """Test TaskInputDTO validation edge cases."""
    # Test with empty string in various fields
    with pytest.raises(ValueError):
        TaskInputDTO(description="")

def test_task_output_dto_validation_edge_cases():
    """Test TaskOutputDTO validation edge cases."""
    # Test with minimal required fields
    task_uuid = uuid4()
    task = TaskOutputDTO(
        description="Test",
        index=1,
        uuid=task_uuid,
        status=TaskStatus.PENDING
    )
    
    assert task.description == "Test"
    assert task.index == 1
    assert task.uuid == task_uuid
    assert task.status == TaskStatus.PENDING

def test_task_status_enum_values():
    """Test TaskStatus enum values."""
    assert TaskStatus.PENDING.value == "pending"
    assert TaskStatus.COMPLETED.value == "completed"
    assert TaskStatus.DELETED.value == "deleted"
    assert TaskStatus.WAITING.value == "waiting"
    assert TaskStatus.RECURRING.value == "recurring"
    assert TaskStatus.STARTED.value == "started"

def test_priority_enum_values():
    """Test Priority enum values."""
    assert Priority.LOW.value == "L"
    assert Priority.MEDIUM.value == "M"
    assert Priority.HIGH.value == "H"
    assert Priority.NONE.value == "N"

def test_recurrence_period_enum_values():
    """Test RecurrencePeriod enum values."""
    assert RecurrencePeriod.HOURLY.value == "hourly"
    assert RecurrencePeriod.DAILY.value == "daily"
    assert RecurrencePeriod.WEEKLY.value == "weekly"
    assert RecurrencePeriod.MONTHLY.value == "monthly"
    assert RecurrencePeriod.YEARLY.value == "yearly"

def test_task_warrior_error_inheritance():
    """Test TaskWarriorError inheritance."""
    from src.taskwarrior.exceptions import TaskWarriorError, TaskNotFound, TaskValidationError
    
    # Test that all exceptions inherit from TaskWarriorError
    assert issubclass(TaskNotFound, TaskWarriorError)
    assert issubclass(TaskValidationError, TaskWarriorError)

def test_exception_messages(self):
    """Test exception messages."""
    from src.taskwarrior.exceptions import TaskValidationError, TaskNotFound
    
    # Test validation error
    try:
        raise TaskValidationError("Test validation error")
    except TaskValidationError as e:
        assert str(e) == "Test validation error"
    
    # Test not found error
    try:
        raise TaskNotFound("Test not found error")
    except TaskNotFound as e:
        assert str(e) == "Test not found error"
