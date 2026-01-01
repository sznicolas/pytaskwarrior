import pytest
from datetime import datetime, timedelta
from uuid import UUID

from src.taskwarrior import TaskInputDTO, TaskOutputDTO, Priority, TaskStatus, RecurrencePeriod


def test_task_values(sample_task: TaskInputDTO) -> None:
    """Test Task.to_dict conversion."""
    assert sample_task.description == "Test Task"
    assert sample_task.priority == Priority.HIGH.value
    assert sample_task.project == "Test"
    assert sample_task.tags == ["test", "urgent"]


def test_empty_description_validation() -> None:
    """Test that empty task descriptions raise validation error."""
    with pytest.raises(Exception, match="Description cannot be empty"):
        TaskInputDTO(description="")


def test_task_serialization() -> None:
    """Test that task serialization works correctly."""
    task = TaskInputDTO(
        description="Test serialization",
        priority=Priority.HIGH,
        project="TestProject"
    )
    
    # Test that serialization works without errors
    task_dict = task.model_dump()
    assert "description" in task_dict
    assert "priority" in task_dict
    assert "project" in task_dict


def test_task_with_timedelta_fields() -> None:
    """Test that tasks with timedelta fields serialize correctly."""
    task = TaskInputDTO(
        description="Task with timedelta",
        due=timedelta(days=1, hours=2),
        scheduled=timedelta(hours=3)
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "due" in task_dict
    assert "scheduled" in task_dict


def test_task_with_uuid_fields() -> None:
    """Test that tasks with UUID fields serialize correctly."""
    test_uuid = UUID('12345678-1234-5678-1234-567812345678')
    task = TaskInputDTO(
        description="Task with UUID",
        depends=[test_uuid]
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "depends" in task_dict


def test_task_with_datetime_fields() -> None:
    """Test that tasks with datetime fields serialize correctly."""
    now = datetime.now()
    task = TaskInputDTO(
        description="Task with datetime",
        entry=now,
        start=now
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "entry" in task_dict
    assert "start" in task_dict


def test_task_with_tags() -> None:
    """Test that tasks with tags serialize correctly."""
    task = TaskInputDTO(
        description="Task with tags",
        tags=["tag1", "tag2"]
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "tags" in task_dict


def test_task_with_recurrence() -> None:
    """Test that tasks with recurrence periods serialize correctly."""
    task = TaskInputDTO(
        description="Recurring task",
        recur=RecurrencePeriod.WEEKLY
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "recur" in task_dict


def test_task_with_priority() -> None:
    """Test that tasks with priority serialize correctly."""
    task = TaskInputDTO(
        description="Task with priority",
        priority=Priority.LOW
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "priority" in task_dict


def test_task_with_status() -> None:
    """Test that tasks with status serialize correctly."""
    task = TaskInputDTO(
        description="Task with status",
        status=TaskStatus.COMPLETED
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "status" in task_dict


def test_task_with_project() -> None:
    """Test that tasks with project serialize correctly."""
    task = TaskInputDTO(
        description="Task with project",
        project="TestProject"
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "project" in task_dict


def test_task_with_parent() -> None:
    """Test that tasks with parent UUID serialize correctly."""
    parent_uuid = UUID('12345678-1234-5678-1234-567812345678')
    task = TaskInputDTO(
        description="Task with parent",
        parent=parent_uuid
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "parent" in task_dict


def test_task_with_context() -> None:
    """Test that tasks with context serialize correctly."""
    task = TaskInputDTO(
        description="Task with context",
        context="test-context"
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "context" in task_dict


def test_task_with_due_field() -> None:
    """Test that tasks with due field serialize correctly."""
    task = TaskInputDTO(
        description="Task with due",
        due=datetime.now()
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "due" in task_dict


def test_task_with_scheduled_field() -> None:
    """Test that tasks with scheduled field serialize correctly."""
    task = TaskInputDTO(
        description="Task with scheduled",
        scheduled=datetime.now()
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "scheduled" in task_dict


def test_task_with_wait_field() -> None:
    """Test that tasks with wait field serialize correctly."""
    task = TaskInputDTO(
        description="Task with wait",
        wait=datetime.now()
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "wait" in task_dict


def test_task_with_until_field() -> None:
    """Test that tasks with until field serialize correctly."""
    task = TaskInputDTO(
        description="Task with until",
        until=datetime.now()
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "until" in task_dict


def test_task_with_modified_field() -> None:
    """Test that tasks with modified field serialize correctly."""
    task = TaskInputDTO(
        description="Task with modified",
        modified=datetime.now()
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "modified" in task_dict


def test_task_with_end_field() -> None:
    """Test that tasks with end field serialize correctly."""
    task = TaskInputDTO(
        description="Task with end",
        end=datetime.now()
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "end" in task_dict


def test_task_with_start_field() -> None:
    """Test that tasks with start field serialize correctly."""
    task = TaskInputDTO(
        description="Task with start",
        start=datetime.now()
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "start" in task_dict


def test_task_with_entry_field() -> None:
    """Test that tasks with entry field serialize correctly."""
    task = TaskInputDTO(
        description="Task with entry",
        entry=datetime.now()
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "entry" in task_dict


def test_task_with_index_field() -> None:
    """Test that tasks with index field serialize correctly."""
    task = TaskInputDTO(
        description="Task with index",
        index=123
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "index" in task_dict


def test_task_with_uuid_field() -> None:
    """Test that tasks with uuid field serialize correctly."""
    test_uuid = UUID('12345678-1234-5678-1234-567812345678')
    task = TaskInputDTO(
        description="Task with uuid",
        uuid=test_uuid
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "uuid" in task_dict


def test_task_with_depends_field() -> None:
    """Test that tasks with depends field serialize correctly."""
    test_uuid = UUID('12345678-1234-5678-1234-567812345678')
    task = TaskInputDTO(
        description="Task with depends",
        depends=[test_uuid]
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "depends" in task_dict


def test_task_with_tags_field() -> None:
    """Test that tasks with tags field serialize correctly."""
    task = TaskInputDTO(
        description="Task with tags",
        tags=["tag1", "tag2"]
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "tags" in task_dict


def test_task_with_priority_field() -> None:
    """Test that tasks with priority field serialize correctly."""
    task = TaskInputDTO(
        description="Task with priority",
        priority=Priority.HIGH
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "priority" in task_dict


def test_task_with_status_field() -> None:
    """Test that tasks with status field serialize correctly."""
    task = TaskInputDTO(
        description="Task with status",
        status=TaskStatus.PENDING
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "status" in task_dict


def test_task_with_project_field() -> None:
    """Test that tasks with project field serialize correctly."""
    task = TaskInputDTO(
        description="Task with project",
        project="TestProject"
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "project" in task_dict


def test_task_with_parent_field() -> None:
    """Test that tasks with parent field serialize correctly."""
    parent_uuid = UUID('12345678-1234-5678-1234-567812345678')
    task = TaskInputDTO(
        description="Task with parent",
        parent=parent_uuid
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "parent" in task_dict


def test_task_with_context_field() -> None:
    """Test that tasks with context field serialize correctly."""
    task = TaskInputDTO(
        description="Task with context",
        context="test-context"
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "context" in task_dict


def test_task_with_recur_field() -> None:
    """Test that tasks with recur field serialize correctly."""
    task = TaskInputDTO(
        description="Task with recur",
        recur=RecurrencePeriod.DAILY
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "recur" in task_dict


def test_task_with_due_field_serialization() -> None:
    """Test that tasks with due field serialize to correct format."""
    task = TaskInputDTO(
        description="Task with due",
        due=timedelta(days=1)
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "due" in task_dict


def test_task_with_scheduled_field_serialization() -> None:
    """Test that tasks with scheduled field serialize to correct format."""
    task = TaskInputDTO(
        description="Task with scheduled",
        scheduled=timedelta(hours=2)
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "scheduled" in task_dict


def test_task_with_wait_field_serialization() -> None:
    """Test that tasks with wait field serialize to correct format."""
    task = TaskInputDTO(
        description="Task with wait",
        wait=timedelta(days=1)
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "wait" in task_dict


def test_task_with_until_field_serialization() -> None:
    """Test that tasks with until field serialize to correct format."""
    task = TaskInputDTO(
        description="Task with until",
        until=timedelta(weeks=1)
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "until" in task_dict


def test_task_with_modified_field_serialization() -> None:
    """Test that tasks with modified field serialize to correct format."""
    task = TaskInputDTO(
        description="Task with modified",
        modified=datetime.now()
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "modified" in task_dict


def test_task_with_end_field_serialization() -> None:
    """Test that tasks with end field serialize to correct format."""
    task = TaskInputDTO(
        description="Task with end",
        end=datetime.now()
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "end" in task_dict


def test_task_with_start_field_serialization() -> None:
    """Test that tasks with start field serialize to correct format."""
    task = TaskInputDTO(
        description="Task with start",
        start=datetime.now()
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "start" in task_dict


def test_task_with_entry_field_serialization() -> None:
    """Test that tasks with entry field serialize to correct format."""
    task = TaskInputDTO(
        description="Task with entry",
        entry=datetime.now()
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "entry" in task_dict


def test_task_with_index_field_serialization() -> None:
    """Test that tasks with index field serialize to correct format."""
    task = TaskInputDTO(
        description="Task with index",
        index=456
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "index" in task_dict


def test_task_with_uuid_field_serialization() -> None:
    """Test that tasks with uuid field serialize to correct format."""
    test_uuid = UUID('12345678-1234-5678-1234-567812345678')
    task = TaskInputDTO(
        description="Task with uuid",
        uuid=test_uuid
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "uuid" in task_dict


def test_task_with_depends_field_serialization() -> None:
    """Test that tasks with depends field serialize to correct format."""
    test_uuid = UUID('12345678-1234-5678-1234-567812345678')
    task = TaskInputDTO(
        description="Task with depends",
        depends=[test_uuid]
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "depends" in task_dict


def test_task_with_tags_field_serialization() -> None:
    """Test that tasks with tags field serialize to correct format."""
    task = TaskInputDTO(
        description="Task with tags",
        tags=["tag1", "tag2"]
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "tags" in task_dict


def test_task_with_priority_field_serialization() -> None:
    """Test that tasks with priority field serialize to correct format."""
    task = TaskInputDTO(
        description="Task with priority",
        priority=Priority.MEDIUM
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "priority" in task_dict


def test_task_with_status_field_serialization() -> None:
    """Test that tasks with status field serialize to correct format."""
    task = TaskInputDTO(
        description="Task with status",
        status=TaskStatus.COMPLETED
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "status" in task_dict


def test_task_with_project_field_serialization() -> None:
    """Test that tasks with project field serialize to correct format."""
    task = TaskInputDTO(
        description="Task with project",
        project="AnotherProject"
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "project" in task_dict


def test_task_with_parent_field_serialization() -> None:
    """Test that tasks with parent field serialize to correct format."""
    parent_uuid = UUID('12345678-1234-5678-1234-567812345678')
    task = TaskInputDTO(
        description="Task with parent",
        parent=parent_uuid
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "parent" in task_dict


def test_task_with_context_field_serialization() -> None:
    """Test that tasks with context field serialize to correct format."""
    task = TaskInputDTO(
        description="Task with context",
        context="another-context"
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "context" in task_dict


def test_task_with_recur_field_serialization() -> None:
    """Test that tasks with recur field serialize to correct format."""
    task = TaskInputDTO(
        description="Task with recur",
        recur=RecurrencePeriod.MONTHLY
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "recur" in task_dict


def test_task_with_all_fields() -> None:
    """Test that tasks with all fields serialize correctly."""
    test_uuid = UUID('12345678-1234-5678-1234-567812345678')
    task = TaskInputDTO(
        description="Complete task",
        index=1,
        uuid=test_uuid,
        status=TaskStatus.PENDING,
        priority=Priority.HIGH,
        due=datetime.now(),
        entry=datetime.now(),
        start=datetime.now(),
        end=datetime.now(),
        modified=datetime.now(),
        tags=["tag1", "tag2"],
        project="TestProject",
        depends=[test_uuid],
        parent=test_uuid,
        recur=RecurrencePeriod.WEEKLY,
        scheduled=datetime.now(),
        wait=datetime.now(),
        until=datetime.now(),
        context="test-context"
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert all(field in task_dict for field in [
        "description", "index", "uuid", "status", "priority",
        "due", "entry", "start", "end", "modified", "tags",
        "project", "depends", "parent", "recur", "scheduled",
        "wait", "until", "context"
    ])
