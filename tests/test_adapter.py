import json
import subprocess
from unittest.mock import patch, MagicMock

import pytest

from src.taskwarrior.adapters.taskwarrior_adapter import TaskWarriorAdapter
from src.taskwarrior.dto.task_dto import TaskInputDTO
from src.taskwarrior.enums import Priority, RecurrencePeriod
from src.taskwarrior.exceptions import TaskNotFound, TaskValidationError, TaskWarriorError


class TestTaskWarriorAdapter:
    """Test cases for TaskWarriorAdapter."""

    @pytest.fixture
    def adapter(self):
        """Create a TaskWarriorAdapter instance for testing."""
        return TaskWarriorAdapter(task_cmd="task", taskrc_path="/tmp/taskrc")

    @pytest.fixture
    def sample_task(self):
        """Create a sample TaskInputDTO for testing."""
        return TaskInputDTO(
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

    def test_run_task_command_success(self, adapter):
        """Test _run_task_command with successful command execution."""
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "success"
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            result = adapter._run_task_command(["add", "test"])

            assert result.returncode == 0
            assert result.stdout == "success"
            assert result.stderr == ""
            mock_run.assert_called_once()

    def test_run_task_command_failure(self, adapter):
        """Test _run_task_command with failed command execution."""
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stdout = ""
            mock_result.stderr = "error"
            mock_run.return_value = mock_result

            result = adapter._run_task_command(["add", "test"])

            assert result.returncode == 1
            assert result.stderr == "error"
            mock_run.assert_called_once()

    def test_validate_date_string_valid(self, adapter):
        """Test _validate_date_string with valid date formats."""
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = ""
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            assert adapter._validate_date_string("tomorrow") is True
            mock_run.assert_called_once_with(
                ["task", "calc", "tomorrow"],
                capture_output=True,
                text=True,
                check=True
            )

    def test_validate_date_string_invalid(self, adapter):
        """Test _validate_date_string with invalid date formats."""
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stdout = ""
            mock_result.stderr = "error"
            mock_run.return_value = mock_result

            assert adapter._validate_date_string("invalid_date") is False
            mock_run.assert_called_once_with(
                ["task", "calc", "invalid_date"],
                capture_output=True,
                text=True,
                check=True
            )

    def test_build_args_minimal(self, adapter):
        """Test _build_args with minimal TaskInputDTO."""
        task = TaskInputDTO(description="Minimal task")
        args = adapter._build_args(task)
        
        assert "description=Minimal task" in args
        assert len(args) == 1

    def test_build_args_all_fields(self, adapter, sample_task):
        """Test _build_args with all fields populated."""
        args = adapter._build_args(sample_task)
        
        assert "description=Test task" in args
        assert "priority=H" in args
        assert "project=TestProject" in args
        assert "tags=tag1,tag2" in args
        assert "due=2023-12-31T23:59:59Z" in args
        assert "scheduled=2023-12-30T00:00:00Z" in args
        assert "wait=2023-12-29T00:00:00Z" in args
        assert "until=2024-12-31T23:59:59Z" in args
        assert "recur=weekly" in args
        assert "context=test_context" in args

    def test_build_args_tags_handling(self, adapter):
        """Test _build_args with tags handling."""
        task = TaskInputDTO(
            description="Task with tags",
            tags=["tag1", "tag2", "tag3"]
        )
        args = adapter._build_args(task)
        
        assert "tags=tag1,tag2,tag3" in args

    def test_build_args_depends_handling(self, adapter):
        """Test _build_args with depends field handling."""
        from uuid import uuid4
        dep_uuid = uuid4()
        task = TaskInputDTO(
            description="Task with depends",
            depends=[dep_uuid]
        )
        args = adapter._build_args(task)
        
        assert f"depends+={dep_uuid!r}" in args

    def test_build_args_uuid_fields(self, adapter):
        """Test _build_args with UUID fields."""
        from uuid import uuid4
        task_uuid = uuid4()
        task = TaskInputDTO(
            description="Task with UUID",
            parent=task_uuid
        )
        args = adapter._build_args(task)
        
        assert f"parent={task_uuid!r}" in args

    def test_add_task_success(self, adapter):
        """Test add_task with valid task."""
        with patch.object(adapter, '_run_task_command') as mock_run:
            with patch.object(adapter, 'get_tasks') as mock_get_tasks:
                # Mock successful add command
                mock_result = MagicMock()
                mock_result.returncode = 0
                mock_result.stdout = ""
                mock_result.stderr = ""
                mock_run.return_value = mock_result
                
                # Mock successful get_tasks response
                mock_get_tasks.return_value = [MagicMock(uuid="test-uuid")]
                
                task = TaskInputDTO(description="Test task")
                result = adapter.add_task(task)
                
                assert result.uuid == "test-uuid"
                mock_run.assert_called_once()
                mock_get_tasks.assert_called_once()

    def test_add_task_empty_description_validation(self, adapter):
        """Test add_task with empty description validation."""
        task = TaskInputDTO(description="")
        
        with pytest.raises(TaskValidationError, match="Task description cannot be empty"):
            adapter.add_task(task)

    def test_add_task_invalid_date_format_validation(self, adapter):
        """Test add_task with invalid date format validation."""
        task = TaskInputDTO(
            description="Test task",
            due="invalid_date"
        )
        
        with patch.object(adapter, '_validate_date_string') as mock_validate:
            mock_validate.return_value = False
            
            with pytest.raises(TaskValidationError, match="Invalid date format for due"):
                adapter.add_task(task)

    def test_modify_task_success(self, adapter):
        """Test modify_task with valid task modification."""
        with patch.object(adapter, '_run_task_command') as mock_run:
            # Mock successful modify command
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = ""
            mock_result.stderr = ""
            mock_run.return_value = mock_result
            
            task = TaskInputDTO(description="Modified task")
            # This would normally be called with a UUID, but we're just testing the command
            result = adapter.modify_task(task, "test-uuid")
            
            assert mock_run.called

    def test_modify_task_invalid_date_format_validation(self, adapter):
        """Test modify_task with invalid date format validation."""
        task = TaskInputDTO(
            description="Test task",
            due="invalid_date"
        )
        
        with patch.object(adapter, '_validate_date_string') as mock_validate:
            mock_validate.return_value = False
            
            with pytest.raises(TaskValidationError, match="Invalid date format for due"):
                adapter.modify_task(task, "test-uuid")

    def test_get_task_existing(self, adapter):
        """Test get_task with existing task."""
        with patch.object(adapter, '_run_task_command') as mock_run:
            # Mock successful get command
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = json.dumps([{
                "id": 1,
                "description": "Test task",
                "uuid": "test-uuid",
                "status": "pending"
            }])
            mock_result.stderr = ""
            mock_run.return_value = mock_result
            
            result = adapter.get_task("test-uuid")
            
            assert result.uuid == "test-uuid"
            assert result.description == "Test task"

    def test_get_task_nonexistent(self, adapter):
        """Test get_task with non-existent task."""
        with patch.object(adapter, '_run_task_command') as mock_run:
            # Mock failed get command
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stdout = ""
            mock_result.stderr = "error"
            mock_run.return_value = mock_result
            
            with pytest.raises(TaskNotFound):
                adapter.get_task("nonexistent-uuid")

    def test_get_tasks_with_filters(self, adapter):
        """Test get_tasks with various filter arguments."""
        with patch.object(adapter, '_run_task_command') as mock_run:
            # Mock successful get command
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = json.dumps([{
                "id": 1,
                "description": "Test task",
                "uuid": "test-uuid",
                "status": "pending"
            }])
            mock_result.stderr = ""
            mock_run.return_value = mock_result
            
            result = adapter.get_tasks(["status:pending"])
            
            assert len(result) == 1
            assert result[0].uuid == "test-uuid"

    def test_delete_task_success(self, adapter):
        """Test delete_task with valid UUID."""
        with patch.object(adapter, '_run_task_command') as mock_run:
            # Mock successful delete command
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = ""
            mock_result.stderr = ""
            mock_run.return_value = mock_result
            
            adapter.delete_task("test-uuid")
            
            assert mock_run.called

    def test_purge_task_success(self, adapter):
        """Test purge_task with valid UUID."""
        with patch.object(adapter, '_run_task_command') as mock_run:
            # Mock successful purge command
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = ""
            mock_result.stderr = ""
            mock_run.return_value = mock_result
            
            adapter.purge_task("test-uuid")
            
            assert mock_run.called

    def test_done_task_success(self, adapter):
        """Test done_task with valid UUID."""
        with patch.object(adapter, '_run_task_command') as mock_run:
            # Mock successful done command
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = ""
            mock_result.stderr = ""
            mock_run.return_value = mock_result
            
            adapter.done_task("test-uuid")
            
            assert mock_run.called

    def test_start_task_success(self, adapter):
        """Test start_task with valid UUID."""
        with patch.object(adapter, '_run_task_command') as mock_run:
            # Mock successful start command
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = ""
            mock_result.stderr = ""
            mock_run.return_value = mock_result
            
            adapter.start_task("test-uuid")
            
            assert mock_run.called

    def test_stop_task_success(self, adapter):
        """Test stop_task with valid UUID."""
        with patch.object(adapter, '_run_task_command') as mock_run:
            # Mock successful stop command
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = ""
            mock_result.stderr = ""
            mock_run.return_value = mock_result
            
            adapter.stop_task("test-uuid")
            
            assert mock_run.called

    def test_annotate_task_success(self, adapter):
        """Test annotate_task with valid annotation."""
        with patch.object(adapter, '_run_task_command') as mock_run:
            # Mock successful annotate command
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = ""
            mock_result.stderr = ""
            mock_run.return_value = mock_result
            
            adapter.annotate_task("test-uuid", "Test annotation")
            
            assert mock_run.called

    def test_set_context_success(self, adapter):
        """Test set_context with valid context."""
        with patch.object(adapter, '_run_task_command') as mock_run:
            # Mock successful set context command
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = ""
            mock_result.stderr = ""
            mock_run.return_value = mock_result
            
            adapter.set_context("test_context", "status:pending")
            
            assert mock_run.called

    def test_apply_context_success(self, adapter):
        """Test apply_context with valid context."""
        with patch.object(adapter, '_run_task_command') as mock_run:
            # Mock successful apply context command
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = ""
            mock_result.stderr = ""
            mock_run.return_value = mock_result
            
            adapter.apply_context("test_context")
            
            assert mock_run.called

    def test_remove_context_success(self, adapter):
        """Test remove_context with valid context."""
        with patch.object(adapter, '_run_task_command') as mock_run:
            # Mock successful remove context command
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = ""
            mock_result.stderr = ""
            mock_run.return_value = mock_result
            
            adapter.remove_context()
            
            assert mock_run.called

    def test_get_info_success(self, adapter):
        """Test get_info with successful retrieval."""
        with patch.object(adapter, '_run_task_command') as mock_run:
            # Mock successful version command
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "Taskwarrior 2.6.1\n"
            mock_result.stderr = ""
            mock_run.return_value = mock_result
            
            info = adapter.get_info()
            
            assert "version" in info
            assert info["task_cmd"] == "task"
            assert info["taskrc_path"] == "/tmp/taskrc"
            assert "default_options" in info
