import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4

from src.taskwarrior import TaskWarrior, TaskInputDTO, TaskOutputDTO
from src.taskwarrior.enums import Priority, TaskStatus, RecurrencePeriod
from src.taskwarrior.exceptions import TaskNotFound, TaskValidationError, TaskWarriorError


class TestTaskWarrior:
    """Test cases for TaskWarrior main class."""

    @pytest.fixture
    def taskwarrior(self):
        """Create a TaskWarrior instance for testing."""
        return TaskWarrior(task_cmd="task", taskrc_path="/tmp/taskrc")

    def test_add_task_success(self, taskwarrior):
        """Test add_task method with valid task."""
        with patch.object(taskwarrior.adapter, 'add_task') as mock_add:
            mock_task_output = MagicMock()
            mock_task_output.uuid = "test-uuid"
            mock_add.return_value = mock_task_output
            
            task = TaskInputDTO(description="Test task")
            result = taskwarrior.add_task(task)
            
            assert result.uuid == "test-uuid"
            mock_add.assert_called_once_with(task)

    def test_modify_task_success(self, taskwarrior):
        """Test modify_task method with valid task modification."""
        with patch.object(taskwarrior.adapter, 'modify_task') as mock_modify:
            mock_task_output = MagicMock()
            mock_task_output.uuid = "test-uuid"
            mock_modify.return_value = mock_task_output
            
            task = TaskInputDTO(description="Modified task")
            result = taskwarrior.modify_task(task, "test-uuid")
            
            assert result.uuid == "test-uuid"
            mock_modify.assert_called_once_with(task, "test-uuid")

    def test_get_task_success(self, taskwarrior):
        """Test get_task method with valid UUID."""
        with patch.object(taskwarrior.adapter, 'get_task') as mock_get:
            mock_task_output = MagicMock()
            mock_task_output.uuid = "test-uuid"
            mock_get.return_value = mock_task_output
            
            result = taskwarrior.get_task("test-uuid")
            
            assert result.uuid == "test-uuid"
            mock_get.assert_called_once_with("test-uuid")

    def test_get_tasks_success(self, taskwarrior):
        """Test get_tasks method with filters."""
        with patch.object(taskwarrior.adapter, 'get_tasks') as mock_get:
            mock_task_output = [MagicMock(uuid="test-uuid")]
            mock_get.return_value = mock_task_output
            
            result = taskwarrior.get_tasks(["status:pending"])
            
            assert len(result) == 1
            assert result[0].uuid == "test-uuid"
            mock_get.assert_called_once_with(["status:pending"])

    def test_delete_task_success(self, taskwarrior):
        """Test delete_task method."""
        with patch.object(taskwarrior.adapter, 'delete_task') as mock_delete:
            taskwarrior.delete_task("test-uuid")
            
            mock_delete.assert_called_once_with("test-uuid")

    def test_purge_task_success(self, taskwarrior):
        """Test purge_task method."""
        with patch.object(taskwarrior.adapter, 'purge_task') as mock_purge:
            taskwarrior.purge_task("test-uuid")
            
            mock_purge.assert_called_once_with("test-uuid")

    def test_done_task_success(self, taskwarrior):
        """Test done_task method."""
        with patch.object(taskwarrior.adapter, 'done_task') as mock_done:
            taskwarrior.done_task("test-uuid")
            
            mock_done.assert_called_once_with("test-uuid")

    def test_start_task_success(self, taskwarrior):
        """Test start_task method."""
        with patch.object(taskwarrior.adapter, 'start_task') as mock_start:
            taskwarrior.start_task("test-uuid")
            
            mock_start.assert_called_once_with("test-uuid")

    def test_stop_task_success(self, taskwarrior):
        """Test stop_task method."""
        with patch.object(taskwarrior.adapter, 'stop_task') as mock_stop:
            taskwarrior.stop_task("test-uuid")
            
            mock_stop.assert_called_once_with("test-uuid")

    def test_annotate_task_success(self, taskwarrior):
        """Test annotate_task method."""
        with patch.object(taskwarrior.adapter, 'annotate_task') as mock_annotate:
            taskwarrior.annotate_task("test-uuid", "Test annotation")
            
            mock_annotate.assert_called_once_with("test-uuid", "Test annotation")

    def test_set_context_success(self, taskwarrior):
        """Test set_context method."""
        with patch.object(taskwarrior.adapter, 'set_context') as mock_set:
            taskwarrior.set_context("test_context", "status:pending")
            
            mock_set.assert_called_once_with("test_context", "status:pending")

    def test_apply_context_success(self, taskwarrior):
        """Test apply_context method."""
        with patch.object(taskwarrior.adapter, 'apply_context') as mock_apply:
            taskwarrior.apply_context("test_context")
            
            mock_apply.assert_called_once_with("test_context")

    def test_remove_context_success(self, taskwarrior):
        """Test remove_context method."""
        with patch.object(taskwarrior.adapter, 'remove_context') as mock_remove:
            taskwarrior.remove_context()
            
            mock_remove.assert_called_once()

    def test_get_info_success(self, taskwarrior):
        """Test get_info method."""
        with patch.object(taskwarrior.adapter, 'get_info') as mock_get_info:
            mock_info = {"version": "2.6.1", "task_cmd": "task"}
            mock_get_info.return_value = mock_info
            
            result = taskwarrior.get_info()
            
            assert result["version"] == "2.6.1"
            mock_get_info.assert_called_once()

    def test_add_task_validation_error_propagation(self, taskwarrior):
        """Test that TaskValidationError is propagated from adapter."""
        with patch.object(taskwarrior.adapter, 'add_task') as mock_add:
            mock_add.side_effect = TaskValidationError("Invalid task")
            
            task = TaskInputDTO(description="")
            
            with pytest.raises(TaskValidationError, match="Invalid task"):
                taskwarrior.add_task(task)

    def test_get_task_not_found_propagation(self, taskwarrior):
        """Test that TaskNotFound is propagated from adapter."""
        with patch.object(taskwarrior.adapter, 'get_task') as mock_get:
            mock_get.side_effect = TaskNotFound("Task not found")
            
            with pytest.raises(TaskNotFound, match="Task not found"):
                taskwarrior.get_task("nonexistent-uuid")

    def test_get_tasks_not_found_propagation(self, taskwarrior):
        """Test that TaskNotFound is propagated from adapter."""
        with patch.object(taskwarrior.adapter, 'get_tasks') as mock_get:
            mock_get.side_effect = TaskNotFound("No tasks found")
            
            with pytest.raises(TaskNotFound, match="No tasks found"):
                taskwarrior.get_tasks()

    def test_taskwarrior_error_propagation(self, taskwarrior):
        """Test that TaskWarriorError is propagated from adapter."""
        with patch.object(taskwarrior.adapter, 'set_context') as mock_set:
            mock_set.side_effect = TaskWarriorError("Context error")
            
            with pytest.raises(TaskWarriorError, match="Context error"):
                taskwarrior.set_context("test_context", "status:pending")

    def test_get_tasks_default_filters(self, taskwarrior):
        """Test that get_tasks uses default filters when none provided."""
        with patch.object(taskwarrior.adapter, 'get_tasks') as mock_get:
            mock_task_output = [MagicMock(uuid="test-uuid")]
            mock_get.return_value = mock_task_output
            
            result = taskwarrior.get_tasks()
            
            assert len(result) == 1
            # Check that default filters were applied
            mock_get.assert_called_once_with([
                "status.not:" + TaskStatus.DELETED,
                "status.not:" + TaskStatus.COMPLETED,
            ])

    def test_get_recurring_task_success(self, taskwarrior):
        """Test get_recurring_task method."""
        with patch.object(taskwarrior.adapter, 'get_recurring_task') as mock_get:
            mock_task_output = MagicMock()
            mock_task_output.uuid = "test-uuid"
            mock_get.return_value = mock_task_output
            
            result = taskwarrior.get_recurring_task("test-uuid")
            
            assert result.uuid == "test-uuid"
            mock_get.assert_called_once_with("test-uuid")

    def test_get_recurring_instances_success(self, taskwarrior):
        """Test get_recurring_instances method."""
        with patch.object(taskwarrior.adapter, 'get_recurring_instances') as mock_get:
            mock_task_output = [MagicMock(uuid="test-uuid")]
            mock_get.return_value = mock_task_output
            
            result = taskwarrior.get_recurring_instances("test-uuid")
            
            assert len(result) == 1
            assert result[0].uuid == "test-uuid"
            mock_get.assert_called_once_with("test-uuid")

    def test_task_output_to_input_conversion(self, taskwarrior):
        """Test task_output_to_input conversion function."""
        from src.taskwarrior.main import task_output_to_input
        
        # Create a sample TaskOutputDTO
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
        
        # Convert to input DTO
        input_task = task_output_to_input(output_task)
        
        assert input_task.description == "Test task"
        assert input_task.priority == Priority.HIGH
        assert input_task.project == "TestProject"
        assert input_task.tags == ["tag1", "tag2"]
        # UUID should not be present in the input DTO
        assert not hasattr(input_task, "uuid")
