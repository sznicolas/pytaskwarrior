"""TaskWarrior CLI adapter.

This module provides the low-level interface to TaskWarrior CLI commands.
"""

import json
import logging
import re
import shlex
import shutil
import subprocess
from pathlib import Path
from uuid import UUID

from ..config.config_store import ConfigStore
from ..dto.task_dto import TaskInputDTO, TaskOutputDTO
from ..enums import TaskStatus
from ..exceptions import (
    TaskConfigurationError,
    TaskNotFound,
    TaskOperationError,
    TaskSyncError,
    TaskValidationError,
    TaskWarriorError,
)

logger = logging.getLogger(__name__)


class TaskWarriorAdapter:

    """Low-level adapter for TaskWarrior CLI commands.

    This class handles direct communication with the TaskWarrior binary,
    including command execution, argument building, and response parsing.
    It is used internally by the TaskWarrior facade class.

    Attributes:
        task_cmd: Path to the TaskWarrior binary.
    """

    def __init__(
        self,
        config_store: ConfigStore,
        task_cmd: str = "task",
    ):
        """Initialize the adapter.

        Args:
            task_cmd: TaskWarrior binary name or path.
            config_store: The configuration store instance (required).

        Raises:
            TaskConfigurationError: If TaskWarrior binary not found.
        """

        self.task_cmd: Path = self._check_binary_path(task_cmd)
        self._cli_options: list[str] = config_store.cli_options
        self._sync_configured: bool = bool(config_store.get_sync_config())

    @property
    def cli_options(self) -> list[str]:
        """Public accessor for CLI options."""
        return self._cli_options

    def _check_binary_path(self, task_cmd: str) -> Path:
        """Verify TaskWarrior binary exists in PATH."""
        resolved_path = shutil.which(task_cmd)
        if not resolved_path:
            raise TaskConfigurationError(f"TaskWarrior command '{task_cmd}' not found in PATH")
        return Path(resolved_path)

    def is_sync_configured(self) -> bool:
        """Return True if sync settings are present in taskrc (any ``sync.*`` key)."""
        return self._sync_configured

    def run_task_command(
        self, args: list[str], no_opt: bool = False
    ) -> subprocess.CompletedProcess[str]:
        """Execute a TaskWarrior CLI command.

        Args:
            args: Command arguments to pass to TaskWarrior.
            no_opt: If True, skip default options.

        Returns:
            CompletedProcess with stdout, stderr, and returncode.
        """
        cmd = [str(self.task_cmd)]
        # Options (rc:...) must come before command and filter arguments so they are applied properly.
        if not no_opt:
            cmd.extend(self._cli_options)
        cmd.extend(args)
        logger.debug(f"Running command: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
            )

            if result.returncode != 0:
                logger.warning(
                    f"Task '{cmd}' command failed with return code {result.returncode}: {result.stderr}"
                )

            logger.debug(
                f"Command '{cmd}' result - stdout: {result.stdout[:40]}... stderr: {result.stderr[:40]}..."
            )
            return result

        except (OSError, subprocess.SubprocessError) as e:
            logger.error(f"Exception while running '{cmd}': {e}")
            raise TaskWarriorError(f"Command execution failed: {e}") from e

    def synchronize(self) -> None:
        """Synchronize tasks by running ``task sync``.

        Delegates to the TaskWarrior CLI's built-in sync command, which handles
        both local (``sync.local.server_dir``) and remote (``sync.server.origin``)
        synchronization based on the taskrc configuration.

        Raises:
            TaskSyncError: If no sync settings are configured, or if the sync
                command exits with a non-zero return code.
        """
        if not self._sync_configured:
            raise TaskSyncError(
                "No sync server is configured. "
                "Add sync.* settings to your taskrc (e.g. sync.local.server_dir)."
            )
        result = self.run_task_command(["sync"])
        if result.returncode != 0:
            raise TaskSyncError(
                f"Synchronization failed: {result.stderr or result.stdout}"
            )

    @staticmethod
    def _wrap_filter(f: str) -> str:
        """Wrap a non-empty filter expression in parentheses.

        Taskwarrior requires parentheses around compound expressions (those
        containing ``or`` or ``and``) when they are passed as a single CLI
        argument.  Wrapping unconditionally is safe: ``(x)`` and ``((x))``
        are equivalent to Taskwarrior.

        Args:
            f: Raw filter string, possibly empty.

        Returns:
            ``"(f)"`` if *f* is non-empty after stripping, else ``""``.
        """
        f = f.strip()
        return f"({f})" if f else ""

    def _build_args(self, task: TaskInputDTO) -> list[str]:
        """Build CLI arguments from a TaskInputDTO."""
        args = []

        for field_name, value in task.model_dump(exclude_unset=True).items():
            if field_name == "uuid":
                continue

            if field_name == "tags" and value:
                if isinstance(value, list):
                    args.append(f"tags:{','.join(shlex.quote(str(v)) for v in value)}")
                else:
                    args.append(f"tags:{shlex.quote(str(value))}")
            elif field_name == "depends" and value:
                args.extend([f"depends:{shlex.quote(str(dep))}" for dep in value])
            elif field_name == "annotations" and value:
                pass  # Handled separately via annotate command
            elif field_name == "udas" and value:
                # Handle UDA values from the dict
                for uda_name, uda_value in value.items():
                    if uda_value is not None:
                        args.append(f"{uda_name}:{shlex.quote(str(uda_value))}")
            else:
                if isinstance(value, (list, tuple)):
                    str_value = ",".join(shlex.quote(str(v)) for v in value)
                elif isinstance(value, UUID):
                    str_value = shlex.quote(str(value))
                else:
                    str_value = shlex.quote(str(value))

                args.append(f"{field_name}:{str_value}")

        logger.debug(f"Built arguments: {args}")
        return args

    def add_task(self, task: TaskInputDTO) -> TaskOutputDTO:
        """Add a new task. Returns the created task."""
        logger.info(f"Adding task with description: {task.description}")

        if not task.description or not task.description.strip():
            raise TaskValidationError("Task description cannot be empty")

        args = self._build_args(task)
        result = self.run_task_command(["add"] + args)

        if result.returncode != 0:
            error_msg = f"Failed to add task: {result.stderr}"
            logger.error(error_msg)
            raise TaskValidationError(error_msg)

        # Parse the task ID from TaskWarrior output: "Created task N."
        match = re.search(r"Created task (\d+)", result.stdout)
        if match:
            task_id = int(match.group(1))
            added_task = self.get_task(task_id)
        else:
            # Fallback: retrieve the most recently added task
            tasks = self.get_tasks(filter="+LATEST", include_completed=True, include_deleted=True)
            if not tasks:
                error_msg = "Failed to retrieve added task"
                logger.error(error_msg)
                raise TaskWarriorError(error_msg)
            added_task = tasks[0]

        if task.annotations:
            for annotation in task.annotations:
                self.annotate_task(added_task.uuid, annotation)

        logger.info(f"Successfully added task with UUID: {added_task.uuid}")
        return added_task

    def modify_task(self, task: TaskInputDTO, task_id_or_uuid: str | int | UUID) -> TaskOutputDTO:
        """Modify an existing task. Returns the updated task."""
        logger.info(f"Modifying task with UUID: {task_id_or_uuid}")

        args = self._build_args(task)
        result = self.run_task_command([str(task_id_or_uuid), "modify"] + args)

        if result.returncode != 0:
            error_msg = f"Failed to modify task: {result.stderr}"
            logger.error(error_msg)
            raise TaskWarriorError(error_msg)

        updated_task = self.get_task(task_id_or_uuid)
        logger.info(f"Successfully modified task with UUID: {task_id_or_uuid}")
        return updated_task

    def get_task(self, task_id_or_uuid: str | int | UUID, filter_args: str = "") -> TaskOutputDTO:
        """Retrieve a single task by ID or UUID."""
        task_id_or_uuid = str(task_id_or_uuid)
        logger.debug(f"Retrieving task with ID/UUID: {task_id_or_uuid}")

        args = [filter_args, task_id_or_uuid, "export"]
        result = self.run_task_command(args)
        if result.returncode == 0:
            try:
                tasks_data = json.loads(result.stdout)
                if len(tasks_data) == 1:
                    task = TaskOutputDTO.model_validate(tasks_data[0])
                    logger.debug(f"Successfully retrieved task: {task.uuid}")
                    return task
                elif len(tasks_data) == 0:
                    raise TaskNotFound(
                        f"No task ID/UUID {task_id_or_uuid} with filter {filter_args}"
                    )
                else:
                    raise TaskWarriorError(
                        f"More than one task returned for ID/UUID {task_id_or_uuid} with filter '{filter_args}'"
                    )
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                raise TaskWarriorError(
                    f"Invalid response from TaskWarrior: {result.stdout}"
                ) from e
        else:
            raise TaskNotFound(
                f"Task ID/UUID {task_id_or_uuid} not found"
            )

    def get_tasks(
        self,
        filter: str = "",
        include_completed: bool = False,
        include_deleted: bool = False,
    ) -> list[TaskOutputDTO]:
        """Retrieve multiple tasks matching a filter.

        The user filter is automatically wrapped in parentheses so that
        compound expressions (e.g. ``"project:a or project:b"``) are
        evaluated correctly by Taskwarrior.

        A status exclusion clause is combined automatically unless overridden:
        - deleted tasks are excluded unless *include_deleted* is ``True``
        - completed tasks are excluded unless *include_completed* is ``True``

        Args:
            filter: TaskWarrior filter expression (e.g. ``"project:work +urgent"``).
                Defaults to no additional filter (all non-deleted/completed tasks).
            include_completed: If ``True``, completed tasks are included.
            include_deleted: If ``True``, deleted tasks are included.

        Returns:
            List of tasks matching the combined filter.

        Raises:
            TaskWarriorError: If the query fails.
        """
        # Build status exclusion clause
        status_parts: list[str] = []
        if not include_deleted:
            status_parts.append(f"status.not:{TaskStatus.DELETED.value}")
        if not include_completed:
            status_parts.append(f"status.not:{TaskStatus.COMPLETED.value}")
        status_clause = " and ".join(status_parts)

        # Combine user filter (wrapped) with status clause
        wrapped = self._wrap_filter(filter)
        wrapped_status = self._wrap_filter(status_clause)
        if wrapped and wrapped_status:
            combined = f"{wrapped} and {wrapped_status}"
        else:
            combined = wrapped or wrapped_status

        logger.debug(f"Getting tasks with combined filter: {combined!r}")
        args = [combined, "export"] if combined else ["export"]
        result = self.run_task_command(args)

        if result.returncode != 0:
            error_msg = f"Failed to get tasks: {result.stderr}"
            logger.error(error_msg)
            raise TaskWarriorError(error_msg)

        try:
            tasks_data = json.loads(result.stdout)
            tasks = [TaskOutputDTO.model_validate(task_data) for task_data in tasks_data]
            logger.debug(f"Retrieved {len(tasks)} tasks")
            return tasks
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise TaskWarriorError(f"Invalid response from TaskWarrior: {result.stdout}") from e

    def get_recurring_task(self, task_id_or_uuid: str | int | UUID) -> TaskOutputDTO:
        """Get the parent recurring task template."""
        task_id_or_uuid = str(task_id_or_uuid)
        logger.debug(f"Getting recurring task with UUID: {task_id_or_uuid}")

        result = self.run_task_command(
            [str(task_id_or_uuid), "status:" + TaskStatus.RECURRING, "export"]
        )

        if result.returncode == 0:
            try:
                tasks_data = json.loads(result.stdout)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                raise TaskWarriorError(
                    f"Invalid response from TaskWarrior: {result.stdout}"
                ) from e
            if tasks_data:
                task = TaskOutputDTO.model_validate(tasks_data[0])
                logger.debug(f"Successfully retrieved recurring task: {task.uuid}")
                return task

        logger.debug(
            f"Recurring task {task_id_or_uuid} not found as recurring, trying normal retrieval"
        )
        return self.get_task(task_id_or_uuid)

    def get_recurring_instances(self, task_id_or_uuid: str | int | UUID) -> list[TaskOutputDTO]:
        """Get all instances of a recurring task."""
        task_id_or_uuid = str(task_id_or_uuid)
        logger.debug(f"Getting recurring instances for parent UUID: {task_id_or_uuid}")

        result = self.run_task_command([f"parent:{str(task_id_or_uuid)}", "export"])

        if result.returncode != 0:
            if (
                "No matches" in result.stderr
                or "Unable to find report that matches" in result.stderr
            ):
                logger.debug("No recurring instances found")
                return []
            error_msg = f"Failed to get recurring instances: {result.stderr}"
            logger.error(error_msg)
            raise TaskWarriorError(error_msg)

        if not result.stdout.strip():
            logger.debug("No recurring instances returned (empty response)")
            return []

        try:
            tasks_data = json.loads(result.stdout)
            tasks = [TaskOutputDTO.model_validate(task_data) for task_data in tasks_data]
            logger.debug(f"Retrieved {len(tasks)} recurring instances")
            return tasks
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise TaskWarriorError(f"Invalid response from TaskWarrior: {result.stdout}") from e

    def delete_task(self, task_id_or_uuid: str | int | UUID) -> None:
        """Mark a task as deleted."""
        task_ref = str(task_id_or_uuid)
        logger.info(f"Deleting task: {task_ref}")

        result = self.run_task_command([task_ref, "delete"])

        if result.returncode != 0:
            error_msg = f"Failed to delete task: {result.stderr}"
            logger.error(error_msg)
            raise TaskOperationError(error_msg)

        logger.info(f"Successfully deleted task: {task_ref}")

    def purge_task(self, task_id_or_uuid: str | int | UUID) -> None:
        """Permanently remove a task."""
        task_ref = str(task_id_or_uuid)
        logger.info(f"Purging task: {task_ref}")

        result = self.run_task_command([task_ref, "purge"])

        if result.returncode != 0:
            error_msg = f"Failed to purge task: {result.stderr}"
            logger.error(error_msg)
            raise TaskOperationError(error_msg)

        logger.info(f"Successfully purged task: {task_ref}")

    def done_task(self, task_id_or_uuid: str | int | UUID) -> None:
        """Mark a task as completed."""
        task_ref = str(task_id_or_uuid)
        logger.info(f"Completing task: {task_ref}")

        result = self.run_task_command([task_ref, "done"])

        if result.returncode != 0:
            error_msg = f"Failed to mark task as done: {result.stderr}"
            logger.error(error_msg)
            raise TaskOperationError(error_msg)

        logger.info(f"Successfully completed task: {task_ref}")

    def start_task(self, task_id_or_uuid: str | int | UUID) -> None:
        """Start working on a task."""
        task_ref = str(task_id_or_uuid)
        logger.info(f"Starting task: {task_ref}")

        result = self.run_task_command([task_ref, "start"])

        if result.returncode != 0:
            error_msg = f"Failed to start task: {result.stderr}"
            logger.error(error_msg)
            raise TaskOperationError(error_msg)

        logger.info(f"Successfully started task: {task_ref}")

    def stop_task(self, task_id_or_uuid: str | int | UUID) -> None:
        """Stop working on a task."""
        task_ref = str(task_id_or_uuid)
        logger.info(f"Stopping task: {task_ref}")

        result = self.run_task_command([task_ref, "stop"])

        if result.returncode != 0:
            error_msg = f"Failed to stop task: {result.stderr}"
            logger.error(error_msg)
            raise TaskOperationError(error_msg)

        logger.info(f"Successfully stopped task: {task_ref}")

    def annotate_task(self, task_id_or_uuid: str | int | UUID, annotation: str) -> None:
        """Add an annotation to a task."""
        task_ref = str(task_id_or_uuid)
        logger.info(f"Annotating task {task_ref} with: {annotation}")

        sanitized_annotation = shlex.quote(annotation)
        result = self.run_task_command([task_ref, "annotate", sanitized_annotation])

        if result.returncode != 0:
            error_msg = f"Failed to annotate task: {result.stderr}"
            logger.error(error_msg)
            raise TaskOperationError(error_msg)

        logger.info(f"Successfully annotated task: {task_ref}")

    def task_calc(self, date_str: str) -> str:
        """Calculate a TaskWarrior date expression."""
        try:
            result = self.run_task_command(["calc", date_str])
            if result.returncode:
                raise TaskWarriorError(f"Failed to calculate date '{date_str}'")

            output: str = result.stdout.strip()
            return output
        except Exception as e:
            raise TaskWarriorError(f"Failed to calculate date '{date_str}': {str(e)}") from e

    def task_date_validator(self, date_str: str) -> bool:
        """Validate a TaskWarrior date expression. Returns True if valid."""
        try:
            result = self.run_task_command(["calc", date_str])
            if result.returncode != 0:
                return False
            # TaskWarrior returns an ISO datetime for valid dates (e.g. 2026-02-26T00:00:00)
            # and returns the input unchanged for invalid expressions
            return bool(re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", result.stdout.strip()))
        except subprocess.SubprocessError:
            return False

    def get_version(self) -> str:
        """Return the TaskWarrior CLI version as a string."""
        version_result = self.run_task_command(["--version"], no_opt=True)
        if version_result.returncode == 0 and version_result.stdout:
            return version_result.stdout.strip()
        return "unknown"

    def get_projects(self) -> list[str]:
        """Get all projects defined in TaskWarrior.

        Returns:
            List of project names.
        """
        result = self.run_task_command(["_projects"])

        if result.returncode != 0:
            raise TaskWarriorError(f"Failed to get projects: {result.stderr}")

        projects = [line.strip() for line in result.stdout.split("\n") if line.strip()]
        return projects
