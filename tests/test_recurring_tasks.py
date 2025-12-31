import pytest

from src.taskwarrior import TaskWarrior, Task, Priority, RecurrencePeriod, TaskStatus


def test_recurring_task(tw: TaskWarrior, sample_task: Task) -> None:
    """Test adding a recurring task."""
    sample_task.until = 'P3W'
    sample_task.recur = RecurrencePeriod.WEEKLY
    task = tw.add_task(sample_task)
    recurring_task = tw.get_recurring_task(task.parent)
    assert recurring_task.recur == "weekly"
    # Recurring tasks should have status 'recurring' when created
    assert recurring_task.status == TaskStatus.RECURRING
    # Check that the child task have status 'pending'
    instances = tw.get_recurring_instances(recurring_task.uuid)
    assert instances[0].parent == recurring_task.uuid
    assert instances[0].status == TaskStatus.PENDING
    assert len(instances) == 1
