import json
import logging
import subprocess
import shlex
from uuid import UUID

from ..exceptions import TaskNotFound, TaskValidationError, TaskWarriorError
from ..dto.task_dto import TaskInputDTO, TaskOutputDTO
from ..dto.context_dto import ContextDTO
from ..enums import TaskStatus

logger = logging.getLogger(__name__)

# Default options that are always passed to taskwarrior commands
DEFAULT_OPTIONS = [
    "rc.confirmation=off",  # Avoid silent user confirmation on stdin
    "rc.bulk=0",
]


class TaskWarriorAdapter:
    """Adapter for TaskWarrior CLI commands."""

    def __init__(
        self,
        task_cmd: str = "task",
        taskrc_path: str | None = None,
        data_location: str | None = None,
    ):
        self.task_cmd: str = task_cmd
        self.taskrc_path = taskrc_path
        self.data_location = data_location
        self._options: list[str] = []
        if self.taskrc_path:
            self._options.extend([f"rc:{self.taskrc_path}"])
        if self.data_location:
            self._options.extend([f"rc.data.location={self.data_location}"])

        self._options.extend(DEFAULT_OPTIONS)

    def _run_task_command(
        self, args: list[str], no_opt=False
    ) -> subprocess.CompletedProcess:
        """Run a taskwarrior command."""
        # Prepend the taskrc path to all commands
        cmd = [self.task_cmd]
        cmd.extend(args)
        if not no_opt:
            cmd.extend(self._options)
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
                    f"Task '{cmd}' command failed with return code {result.returncode}: {result.stderr}"
                )

            logger.debug(
                f"Command '{cmd}' result - stdout: {result.stdout[:40]}... stderr: {result.stderr[:40]}..."
            )
            return result

        except Exception as e:
            logger.error(f"Exception while running '{cmd}': {e}")
            raise

    def _build_args(self, task: TaskInputDTO) -> list[str]:
        """Build command arguments for a task."""
        args = []

        # Process all fields except UUID
        for field_name, value in task.model_dump(exclude_unset=True).items():
            if field_name == "uuid":
                continue

            # Handle special cases
            if field_name == "tags" and value:
                if isinstance(value, list):
                    args.append(f"tags={','.join(shlex.quote(str(v)) for v in value)}")
                else:
                    args.append(f"tags={shlex.quote(str(value))}")
            elif field_name == "depends" and value:
                args.extend([f"depends+={shlex.quote(str(dep))}" for dep in value])
            elif field_name == "annotations" and value:
                # Handle annotations - they are added separately via annotate command
                pass
            else:
                # Handle all other fields with proper quoting
                if isinstance(value, (list, tuple)):
                    str_value = ",".join(shlex.quote(str(v)) for v in value)
                elif isinstance(value, UUID):
                    str_value = shlex.quote(str(value))
                else:
                    str_value = shlex.quote(str(value))

                args.append(f"{field_name}={str_value}")

        logger.debug(f"Built arguments: {args}")

        return args

    def add_task(self, task: TaskInputDTO) -> TaskOutputDTO:
        """Add a new task."""
        logger.info(f"Adding task with description: {task.description}")

        if not task.description.strip():
            raise TaskValidationError("Task description cannot be empty")

        args = self._build_args(task)
        result = self._run_task_command(["add"] + args)

        if result.returncode != 0:
            error_msg = f"Failed to add task: {result.stderr}"
            logger.error(error_msg)
            raise TaskValidationError(error_msg)

        # Get the latest added task
        tasks = self.get_tasks(filter_args=["+LATEST"])
        if not tasks:
            error_msg = "Failed to retrieve added task"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        # Add annotations if any
        if task.annotations:
            for annotation in task.annotations:
                self.annotate_task(tasks[0].uuid, annotation)

        logger.info(f"Successfully added task with UUID: {tasks[0].uuid}")
        return tasks[0]

    def modify_task(
        self, task: TaskInputDTO, task_id_or_uuid: str | int | UUID
    ) -> TaskOutputDTO:
        """Modify an existing task."""
        logger.info(f"Modifying task with UUID: {task_id_or_uuid}")

        args = self._build_args(task)
        result = self._run_task_command([str(task_id_or_uuid), "modify"] + args)

        if result.returncode != 0:
            error_msg = f"Failed to modify task: {result.stderr}"
            logger.error(error_msg)
            raise TaskValidationError(error_msg)

        updated_task = self.get_task(task_id_or_uuid)
        logger.info(f"Successfully modified task with UUID: {task_id_or_uuid}")
        return updated_task

    def get_task(self, task_id_or_uuid: str | int | UUID) -> TaskOutputDTO:
        """Retrieve a task by ID or UUID."""
        # Convert to string for CLI command
        task_id_or_uuid = str(task_id_or_uuid)
        logger.debug(f"Retrieving task with ID/UUID: {task_id_or_uuid}")

        # First try to get the task normally
        result = self._run_task_command([str(task_id_or_uuid), "export"])

        if result.returncode == 0:
            try:
                tasks_data = json.loads(result.stdout)
                if tasks_data:
                    task = TaskOutputDTO.model_validate(tasks_data[0])
                    logger.debug(f"Successfully retrieved task: {task.uuid}")
                    return task
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                raise TaskNotFound(
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
                    task = TaskOutputDTO.model_validate(tasks_data[0])
                    logger.debug(f"Successfully retrieved deleted task: {task.uuid}")
                    return task
        except Exception as e:
            logger.warning(f"Error checking deleted tasks: {e}")

        # If we still haven't found it, raise the exception
        error_msg = f"Task {task_id_or_uuid} not found."
        logger.warning(error_msg)
        raise TaskNotFound(error_msg)

    def get_tasks(self, filter_args: list[str] = None) -> list[TaskOutputDTO]:
        """Get multiple tasks based on filters."""
        logger.debug(f"Getting tasks with filters: {filter_args}")

        # Convert any UUID objects to strings in filter_args then prepend to args
        if filter_args:
            filter_args = [
                str(arg) if isinstance(arg, UUID) else arg for arg in filter_args
            ]
            args = filter_args + ["export"]
        else:
            args = ["export"]
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
            raise TaskNotFound(error_msg)

        if not result.stdout.strip():
            logger.debug("No tasks returned (empty response)")
            return []

        try:
            tasks_data = json.loads(result.stdout)
            tasks = [
                TaskOutputDTO.model_validate(task_data) for task_data in tasks_data
            ]
            logger.debug(f"Retrieved {len(tasks)} tasks")
            return tasks
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise TaskNotFound(f"Invalid response from TaskWarrior: {result.stdout}")

    def get_recurring_task(self, task_id_or_uuid: str | int | UUID) -> TaskOutputDTO:
        """Get the recurring task (parent) by its UUID."""
        # Convert to string for CLI command
        task_id_or_uuid = str(task_id_or_uuid)
        logger.debug(f"Getting recurring task with UUID: {task_id_or_uuid}")

        # Get the parent recurring task
        result = self._run_task_command(
            [str(task_id_or_uuid), "status:" + TaskStatus.RECURRING, "export"]
        )

        if result.returncode == 0:
            tasks_data = json.loads(result.stdout)
            if tasks_data:
                task = TaskOutputDTO.model_validate(tasks_data[0])
                logger.debug(f"Successfully retrieved recurring task: {task.uuid}")
                return task

        # If not found as recurring, try to get it normally
        logger.debug(
            f"Recurring task {task_id_or_uuid} not found as recurring, trying normal retrieval"
        )
        return self.get_task(task_id_or_uuid)

    def get_recurring_instances(
        self, task_id_or_uuid: str | int | UUID
    ) -> list[TaskOutputDTO]:
        """Get all instances of a recurring task."""
        # Convert to string for CLI command
        task_id_or_uuid = str(task_id_or_uuid)
        logger.debug(f"Getting recurring instances for parent UUID: {task_id_or_uuid}")

        # Get child tasks that are instances of the recurring parent
        result = self._run_task_command([f"parent:{str(task_id_or_uuid)}", "export"])

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
            raise TaskNotFound(error_msg)

        if not result.stdout.strip():
            logger.debug("No recurring instances returned (empty response)")
            return []

        try:
            tasks_data = json.loads(result.stdout)
            tasks = [
                TaskOutputDTO.model_validate(task_data) for task_data in tasks_data
            ]
            logger.debug(f"Retrieved {len(tasks)} recurring instances")
            return tasks
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise TaskNotFound(f"Invalid response from TaskWarrior: {result.stdout}")

    def delete_task(self, uuid: str | int | UUID) -> None:
        """Delete a task."""
        # Convert to string for CLI command
        uuid = str(uuid)
        logger.info(f"Deleting task with UUID: {uuid}")

        result = self._run_task_command([str(uuid), "delete"])

        if result.returncode != 0:
            error_msg = f"Failed to delete task: {result.stderr}"
            logger.error(error_msg)
            raise TaskNotFound(error_msg)

        logger.info(f"Successfully deleted task with UUID: {uuid}")

    def purge_task(self, uuid: str | int | UUID) -> None:
        """Purge a task permanently."""
        # Convert to string for CLI command
        uuid = str(uuid)
        logger.info(f"Purging task with UUID: {uuid}")

        result = self._run_task_command([str(uuid), "purge"])

        if result.returncode != 0:
            error_msg = f"Failed to purge task: {result.stderr}"
            logger.error(error_msg)
            raise TaskNotFound(error_msg)

        logger.info(f"Successfully purged task with UUID: {uuid}")

    def done_task(self, uuid: str | int | UUID) -> None:
        """Mark a task as done."""
        # Convert to string for CLI command
        uuid = str(uuid)
        logger.info(f"Completing task with UUID: {uuid}")

        result = self._run_task_command([str(uuid), "done"])

        if result.returncode != 0:
            error_msg = f"Failed to mark task as done: {result.stderr}"
            logger.error(error_msg)
            raise TaskNotFound(error_msg)

        logger.info(f"Successfully completed task with UUID: {uuid}")

    def start_task(self, uuid: str | int | UUID) -> None:
        """Start a task."""
        # Convert to string for CLI command
        uuid = str(uuid)
        logger.info(f"Starting task with UUID: {uuid}")

        result = self._run_task_command([str(uuid), "start"])

        if result.returncode != 0:
            error_msg = f"Failed to start task: {result.stderr}"
            logger.error(error_msg)
            raise TaskNotFound(error_msg)

        logger.info(f"Successfully started task with UUID: {uuid}")

    def stop_task(self, uuid: str | int | UUID) -> None:
        """Stop a task."""
        # Convert to string for CLI command
        uuid = str(uuid)
        logger.info(f"Stopping task with UUID: {uuid}")

        result = self._run_task_command([str(uuid), "stop"])

        if result.returncode != 0:
            error_msg = f"Failed to stop task: {result.stderr}"
            logger.error(error_msg)
            raise TaskNotFound(error_msg)

        logger.info(f"Successfully stopped task with UUID: {uuid}")

    def annotate_task(self, uuid: str | int | UUID, annotation: str) -> None:
        """Add an annotation to a task."""
        # Convert to string for CLI command
        uuid = str(uuid)
        logger.info(f"Annotating task {uuid} with: {annotation}")

        # Sanitize the annotation to prevent command injection
        sanitized_annotation = shlex.quote(annotation)
        result = self._run_task_command([str(uuid), "annotate", sanitized_annotation])

        if result.returncode != 0:
            error_msg = f"Failed to annotate task: {result.stderr}"
            logger.error(error_msg)
            raise TaskNotFound(error_msg)

        logger.info(f"Successfully annotated task with UUID: {uuid}")

    def define_context(self, context: str, filter_str: str) -> None:
        """Define a new context with the given filter."""
        # Use context define command to create a new context
        result = self._run_task_command(["context", "define", context, filter_str])
        if result.returncode != 0:
            raise TaskWarriorError(
                f"Failed to define context '{context}': {result.stderr}"
            )

    def apply_context(self, context: str) -> None:
        """Apply a context (set it as current)."""
        # Use context command with the context name to apply it
        result = self._run_task_command(["context", context])
        if result.returncode != 0:
            raise TaskWarriorError(
                f"Failed to apply context '{context}': {result.stderr}"
            )

    def remove_context(self) -> None:
        """Remove the current context (set to none)."""
        # Use context none to clear current context
        result = self._run_task_command(["context", "none"])
        if result.returncode != 0:
            raise TaskWarriorError(f"Failed to remove context: {result.stderr}")

    def get_contexts(self) -> list[ContextDTO]:
        """List all defined contexts."""
        result = self._run_task_command(["context", "list"])
        if result.returncode != 0:
            raise TaskWarriorError(f"Failed to list contexts: {result.stderr}")

        # Parse the output to extract context names and filters
        lines = result.stdout.strip().split("\n")
        if len(lines) > 2:  # Skip header lines
            for line in lines[2:]:  # Skip "Context Filter" and empty line
                if line.strip():
                    parts = line.split(None, 1)  # Split on first whitespace
                    if len(parts) == 2:
                        context_name, filter_str = parts
                        contexts.append(ContextDTO(name=context_name, filter=filter_str))
        return contexts

    def get_current_context(self) -> str | None:
        """Show the current context."""
        result = self._run_task_command(["_get", "rc.context"])
        if result.returncode != 0:
            # Check if it's because no context is set (command returns non-zero but that's expected)
            # We should return None when no context is set
            return None
        context_name = result.stdout.strip()
        return context_name if context_name else None

    def delete_context(self, context: str) -> None:
        """Delete a defined context."""
        result = self._run_task_command(["context", "delete", context])
        if result.returncode != 0:
            raise TaskWarriorError(
                f"Failed to delete context '{context}': {result.stderr}"
            )

    def get_info(self) -> dict:
        """Get comprehensive TaskWarrior information."""
        info = {
            "task_cmd": self.task_cmd,
            "taskrc_path": self.taskrc_path,
            "options": self._options,
        }

        # Get version
        try:
            version_result = self._run_task_command(["--version"], no_opt=True)
            if version_result.returncode == 0 and version_result.stdout:
                version = version_result.stdout.strip()
                info["version"] = version
        except Exception:
            info["version"] = "unknown"
        return info

    def task_calc(self, date_str: str) -> str:
        """Calculate a TaskWarrior date string and return the result.

        This method calculates the actual date/time for a TaskWarrior date expression
        and returns the calculated value."""
        try:
            result = self._run_task_command(["calc", date_str])
            if result.returncode:
               raise TaskWarriorError(f"Failed to calculate date '{date_str}'")
                
            return result.stdout.strip()
        except Exception as e:
            raise TaskWarriorError(f"Failed to calculate date '{date_str}': {str(e)}")

    def task_date_validator(self, date_str: str) -> bool:
        """Validate TaskWarrior date string format.

        This utility method is provided for developers who need to validate
        TaskWarrior date formats before creating tasks. It's not used internally
        by the adapter.

        Returns:
            True if valid TaskWarrior date format, False otherwise
        """
        try:
            result = self._run_task_command(["calc", date_str , "+ P1D"])
            if result.returncode:
                return False
            return result.stdout.strip() != date_str.strip() + "P1D"
        except subprocess.CalledProcessError:
            return False
