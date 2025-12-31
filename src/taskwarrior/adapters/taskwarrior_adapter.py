import json
import logging
import subprocess
import shlex
from typing import List, Optional, Union
from uuid import UUID

from ..exceptions import TaskNotFound, TaskValidationError
from ..task import Task

logger = logging.getLogger(__name__)


class TaskWarriorAdapter:
    """Adapter for TaskWarrior CLI commands."""

    def __init__(self, task_cmd: str = "task", taskrc_path: Optional[str] = None):
        self.task_cmd = task_cmd
        self.taskrc_path = taskrc_path

    def _run_task_command(self, args: List[str]) -> subprocess.CompletedProcess:
        """Run a taskwarrior command."""
        # Prepend the taskrc path to all commands
        cmd = [self.task_cmd]
        if self.taskrc_path:
            cmd.extend([f"rc:{self.taskrc_path}"])
        cmd.extend(args)
        logger.debug(f"Running command: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,  # We'll handle the error checking ourselves
            )

            if result.returncode != 0:
                logger.warning(
                    f"Task command failed with return code {result.returncode}: {result.stderr}"
                )

            logger.debug(
                f"Command result - stdout: {result.stdout[:100]}... stderr: {result.stderr[:100]}..."
            )
            return result

        except Exception as e:
            logger.error(f"Exception while running task command: {e}")
            raise

    def _build_args(self, task: Task) -> List[str]:
        """Build command arguments for a task."""
        args = []

        # Add all fields that are not None
        for field_name, value in task.model_dump(exclude_unset=True).items():
            if field_name == "uuid":
                continue
            elif field_name == "tags" and value:
                # Handle tags correctly - use proper TaskWarrior syntax
                if isinstance(value, list):
                    args.append(f"tags={','.join(shlex.quote(str(v)) for v in value)}")
                elif isinstance(value, str):
                    # If it's already a string (comma-separated), use as-is
                    args.append(f"tags={value}")
                else:
                    # For other types, convert to string and quote
                    args.append(f"tags={shlex.quote(str(value))}")
            elif field_name == "depends" and value:
                args.extend([f"depends+={shlex.quote(str(dep))}" for dep in value])
            else:
                if isinstance(value, (list, tuple)):
                    # For lists that aren't tags, join them properly and quote each element
                    if field_name == "tags":
                        args.append(
                            f"tags={','.join(shlex.quote(str(v)) for v in value)}"
                        )
                    else:
                        args.append(
                            f"{field_name}={','.join(shlex.quote(str(v)) for v in value)}"
                        )
                elif isinstance(value, UUID):
                    args.append(f"{field_name}={shlex.quote(str(value))}")
                elif hasattr(value, "total_seconds"):
                    # Handle timedelta objects by converting to days
                    total_days = value.total_seconds() / (24 * 3600)
                    args.append(f"{field_name}={int(total_days)}d")
                else:
                    # Convert to string for other types and quote
                    str_value = str(value)
                    args.append(f"{field_name}={shlex.quote(str_value)}")

        logger.debug(f"Built arguments: {args}")
        return args

    def add_task(self, task: Task) -> Task:
        """Add a new task."""
        logger.info(f"Adding task with description: {task.description}")

        if not task.description.strip():
            raise TaskValidationError("Task description cannot be empty")

        args = self._build_args(task)
        result = self._run_task_command(["add"] + args)

        if result.returncode != 0:
            error_msg = f"Failed to add task: {result.stderr}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        # Get the latest added task
        tasks = self.get_tasks(filter_args=["+LATEST"])
        if not tasks:
            error_msg = "Failed to retrieve added task"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        logger.info(f"Successfully added task with UUID: {tasks[0].uuid}")
        return tasks[0]

    def modify_task(self, task: Task) -> Task:
        """Modify an existing task."""
        logger.info(f"Modifying task with UUID: {task.uuid}")

        if not task.uuid:
            raise TaskValidationError("Task must have a UUID to modify")

        args = self._build_args(task)
        result = self._run_task_command([str(task.uuid), "modify"] + args)

        if result.returncode != 0:
            error_msg = f"Failed to modify task: {result.stderr}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        # Get the updated task details
        updated_task = self.get_task(task.uuid)
        logger.info(f"Successfully modified task with UUID: {task.uuid}")
        return updated_task

    def get_task(self, task_id_or_uuid: Union[str, int]) -> Task:
        """Retrieve a task by ID or UUID."""
        logger.debug(f"Retrieving task with ID/UUID: {task_id_or_uuid}")

        # First try to get the task normally
        result = self._run_task_command([str(task_id_or_uuid), "export"])

        if result.returncode == 0:
            try:
                tasks_data = json.loads(result.stdout)
                if tasks_data:
                    task = Task.model_validate(tasks_data[0])
                    logger.debug(f"Successfully retrieved task: {task.uuid}")
                    return task
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                raise RuntimeError(
                    f"Invalid response from TaskWarrior: {result.stdout}"
                )

        # If that fails, check if it's a deleted task
        try:
            # Try to get the task with status:deleted filter
            result = self._run_task_command(
                [str(task_id_or_uuid), "status:deleted", "export"]
            )
            if result.returncode == 0:
                tasks_data = json.loads(result.stdout)
                if tasks_data:
                    task = Task.model_validate(tasks_data[0])
                    logger.debug(f"Successfully retrieved deleted task: {task.uuid}")
                    return task
        except Exception as e:
            logger.warning(f"Error checking deleted tasks: {e}")

        # If we still haven't found it, raise the exception
        error_msg = f"Task {task_id_or_uuid} not found."
        logger.warning(error_msg)
        raise TaskNotFound(error_msg)

    def get_tasks(self, filter_args: List[str]) -> List[Task]:
        """Get multiple tasks based on filters."""
        logger.debug(f"Getting tasks with filters: {filter_args}")

        # Convert any UUID objects to strings in filter_args
        str_filter_args = [
            str(arg) if isinstance(arg, UUID) else arg for arg in filter_args
        ]
        # Ensure we properly handle regex patterns by wrapping them appropriately
        args = str_filter_args + ["export"]
        result = self._run_task_command(args)

        if result.returncode != 0:
            # Check if it's a "no matches" error that we should handle gracefully
            if (
                "No matches" in result.stderr
                or "Unable to find report that matches" in result.stderr
            ):
                logger.debug("No tasks found matching filters")
                return []
            error_msg = f"Failed to get tasks: {result.stderr}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        if not result.stdout.strip():
            logger.debug("No tasks returned (empty response)")
            return []

        try:
            tasks_data = json.loads(result.stdout)
            tasks = [Task.model_validate(task_data) for task_data in tasks_data]
            logger.debug(f"Retrieved {len(tasks)} tasks")
            return tasks
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise RuntimeError(f"Invalid response from TaskWarrior: {result.stdout}")

    def get_recurring_task(self, uuid: UUID) -> Task:
        """Get the recurring task (parent) by its UUID."""
        logger.debug(f"Getting recurring task with UUID: {uuid}")

        # Get the parent recurring task
        result = self._run_task_command([str(uuid), "status:recurring", "export"])

        if result.returncode == 0:
            tasks_data = json.loads(result.stdout)
            if tasks_data:
                task = Task.model_validate(tasks_data[0])
                logger.debug(f"Successfully retrieved recurring task: {task.uuid}")
                return task

        # If not found as recurring, try to get it normally
        logger.debug(
            f"Recurring task {uuid} not found as recurring, trying normal retrieval"
        )
        return self.get_task(uuid)

    def get_recurring_instances(self, uuid: UUID) -> List[Task]:
        """Get all instances of a recurring task."""
        logger.debug(f"Getting recurring instances for parent UUID: {uuid}")

        # Get child tasks that are instances of the recurring parent
        result = self._run_task_command([f"parent:{str(uuid)}", "export"])

        if result.returncode != 0:
            # Check if it's a "no matches" error that we should handle gracefully
            if (
                "No matches" in result.stderr
                or "Unable to find report that matches" in result.stderr
            ):
                logger.debug("No recurring instances found")
                return []
            error_msg = f"Failed to get recurring instances: {result.stderr}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        if not result.stdout.strip():
            logger.debug("No recurring instances returned (empty response)")
            return []

        try:
            tasks_data = json.loads(result.stdout)
            tasks = [Task.model_validate(task_data) for task_data in tasks_data]
            logger.debug(f"Retrieved {len(tasks)} recurring instances")
            return tasks
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise RuntimeError(f"Invalid response from TaskWarrior: {result.stdout}")

    def delete_task(self, uuid: UUID) -> None:
        """Delete a task."""
        logger.info(f"Deleting task with UUID: {uuid}")

        result = self._run_task_command([str(uuid), "delete"])

        if result.returncode != 0:
            error_msg = f"Failed to delete task: {result.stderr}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        logger.info(f"Successfully deleted task with UUID: {uuid}")

    def purge_task(self, uuid: UUID) -> None:
        """Purge a task permanently."""
        logger.info(f"Purging task with UUID: {uuid}")

        result = self._run_task_command([str(uuid), "purge"])

        if result.returncode != 0:
            error_msg = f"Failed to purge task: {result.stderr}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        logger.info(f"Successfully purged task with UUID: {uuid}")

    def done_task(self, uuid: UUID) -> None:
        """Mark a task as done."""
        logger.info(f"Completing task with UUID: {uuid}")

        result = self._run_task_command([str(uuid), "done"])

        if result.returncode != 0:
            error_msg = f"Failed to mark task as done: {result.stderr}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        logger.info(f"Successfully completed task with UUID: {uuid}")

    def start_task(self, uuid: UUID) -> None:
        """Start a task."""
        logger.info(f"Starting task with UUID: {uuid}")

        result = self._run_task_command([str(uuid), "start"])

        if result.returncode != 0:
            error_msg = f"Failed to start task: {result.stderr}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        logger.info(f"Successfully started task with UUID: {uuid}")

    def stop_task(self, uuid: UUID) -> None:
        """Stop a task."""
        logger.info(f"Stopping task with UUID: {uuid}")

        result = self._run_task_command([str(uuid), "stop"])

        if result.returncode != 0:
            error_msg = f"Failed to stop task: {result.stderr}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        logger.info(f"Successfully stopped task with UUID: {uuid}")

    def annotate_task(self, uuid: UUID, annotation: str) -> None:
        """Add an annotation to a task."""
        logger.info(f"Annotating task {uuid} with: {annotation}")

        # Sanitize the annotation to prevent command injection
        sanitized_annotation = shlex.quote(annotation)
        result = self._run_task_command([str(uuid), "annotate", sanitized_annotation])

        if result.returncode != 0:
            error_msg = f"Failed to annotate task: {result.stderr}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        logger.info(f"Successfully annotated task with UUID: {uuid}")

    def set_context(self, context: str, filter_str: str) -> None:
        """Set a context."""
        logger.info(f"Setting context '{context}' with filter: {filter_str}")

        # Sanitize both context and filter_str to prevent command injection
        sanitized_context = shlex.quote(context)
        sanitized_filter = shlex.quote(filter_str)
        result = self._run_task_command(
            ["context", "add", sanitized_context, sanitized_filter]
        )

        if result.returncode != 0:
            error_msg = f"Failed to set context: {result.stderr}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        logger.info(f"Successfully set context: {context}")

    def apply_context(self, context: str) -> None:
        """Apply a context."""
        logger.info(f"Applying context: {context}")

        # Sanitize the context to prevent command injection
        sanitized_context = shlex.quote(context)
        result = self._run_task_command(["context", "apply", sanitized_context])

        if result.returncode != 0:
            error_msg = f"Failed to apply context: {result.stderr}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        logger.info(f"Successfully applied context: {context}")

    def remove_context(self) -> None:
        """Remove the current context."""
        logger.info("Removing current context")

        result = self._run_task_command(["context", "remove"])

        if result.returncode != 0:
            error_msg = f"Failed to remove context: {result.stderr}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        logger.info("Successfully removed context")
