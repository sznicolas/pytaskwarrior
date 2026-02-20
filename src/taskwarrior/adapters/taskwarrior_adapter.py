"""TaskWarrior CLI adapter.

This module provides the low-level interface to TaskWarrior CLI commands.
"""

import json
import logging
import os
import shlex
import shutil
import subprocess
from pathlib import Path
from uuid import UUID

from ..dto.task_dto import TaskInputDTO, TaskOutputDTO
from ..enums import TaskStatus
from ..exceptions import TaskNotFound, TaskValidationError, TaskWarriorError

logger = logging.getLogger(__name__)

DEFAULT_OPTIONS = [
    "rc.confirmation=off",
    "rc.bulk=0",
]


class TaskWarriorAdapter:
    """Low-level adapter for TaskWarrior CLI commands.

    This class handles direct communication with the TaskWarrior binary,
    including command execution, argument building, and response parsing.
    It is used internally by the TaskWarrior facade class.

    Attributes:
        task_cmd: Path to the TaskWarrior binary.
        taskrc_file: Path to the taskrc configuration file.
        data_location: Path to the task data directory.
    """

    def __init__(
        self,
        task_cmd: str = "task",
        taskrc_file: str = "~/.taskrc",
        data_location: str | None = None
    ):
        """Initialize the adapter.

        Args:
            task_cmd: TaskWarrior binary name or path.
            taskrc_file: Path to taskrc file.
            data_location: Path to data directory (optional).

        Raises:
            TaskValidationError: If TaskWarrior binary not found.
        """
        self.task_cmd: Path = self._check_binary_path(task_cmd)
        self._options: list[str] = []
        self.taskrc_file = Path(os.path.expandvars(taskrc_file)).expanduser()
        self._options.extend([f"rc:{self.taskrc_file}"])
        if data_location:
            self.data_location: Path | None = Path(os.path.expandvars(data_location)).expanduser()
            self._options.extend([f"rc.data.location={self.data_location}"])
        else:
            self.data_location = None
        self._check_or_create_taskfiles()

        self._options.extend(DEFAULT_OPTIONS)

    def _check_binary_path(self, task_cmd: str) -> Path:
        """Verify TaskWarrior binary exists in PATH."""
        resolved_path = shutil.which(task_cmd)
        if not resolved_path:
            raise TaskValidationError(
                f"TaskWarrior command '{task_cmd}' not found in PATH"
            )
        return Path(resolved_path)

    def _check_or_create_taskfiles(self) -> None:
        """Create taskrc and data directory if they don't exist."""
        if not self.taskrc_file.exists():
            default_content = """# Taskwarrior configuration file
# This file was automatically created by pytaskwarrior
# Default data location
rc.data.location={data_location}
# Disable confirmation prompts
rc.confirmation=off
rc.bulk=0
""".format(data_location=self.data_location or "~/.task")
            self.taskrc_file.parent.mkdir(parents=True, exist_ok=True)
            self.taskrc_file.write_text(default_content)
            logger.info(f"Created Taskrc file '{self.taskrc_file}'")
        if self.data_location and not self.data_location.exists():
            self.data_location.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created Task data direcory '{self.data_location}'")

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
        cmd.extend(args)
        if not no_opt:
            cmd.extend(self._options)
        logger.debug(f"Running command: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
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

        if not task.description.strip():
            raise TaskValidationError("Task description cannot be empty")

        args = self._build_args(task)
        result = self.run_task_command(["add"] + args)

        if result.returncode != 0:
            error_msg = f"Failed to add task: {result.stderr}"
            logger.error(error_msg)
            raise TaskValidationError(error_msg)

        tasks = self.get_tasks(filter_args="+LATEST")
        if not tasks:
            error_msg = "Failed to retrieve added task"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        if task.annotations:
            for annotation in task.annotations:
                self.annotate_task(tasks[0].uuid, annotation)

        logger.info(f"Successfully added task with UUID: {tasks[0].uuid}")
        return tasks[0]

    def modify_task(
        self, task: TaskInputDTO, task_id_or_uuid: str | int | UUID
    ) -> TaskOutputDTO:
        """Modify an existing task. Returns the updated task."""
        logger.info(f"Modifying task with UUID: {task_id_or_uuid}")

        args = self._build_args(task)
        result = self.run_task_command([str(task_id_or_uuid), "modify"] + args)

        if result.returncode != 0:
            error_msg = f"Failed to modify task: {result.stderr}"
            logger.error(error_msg)
            raise TaskValidationError(error_msg)

        updated_task = self.get_task(task_id_or_uuid)
        logger.info(f"Successfully modified task with UUID: {task_id_or_uuid}")
        return updated_task

    def get_task(
        self, task_id_or_uuid: str | int | UUID, filter_args: str = ""
    ) -> TaskOutputDTO:
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
                raise TaskValidationError(
                    f"Invalid response from TaskWarrior: {result.stdout}"
                ) from e
        else:
            raise TaskWarriorError(
                f"Error while retrieving task ID/UUID {task_id_or_uuid} not found"
            )

    def get_tasks(
        self,
        filter_args: str = f"(status.not:{TaskStatus.DELETED} and status.not:{TaskStatus.COMPLETED})",
    ) -> list[TaskOutputDTO]:
        """Retrieve multiple tasks matching a filter."""
        logger.debug(f"Getting tasks with filters: {filter_args}")
        args = [filter_args, "export"]
        result = self.run_task_command(args)

        if result.returncode != 0:
            error_msg = f"Failed to get tasks: {result.stderr}"
            logger.error(error_msg)
            raise TaskWarriorError(error_msg)

        try:
            tasks_data = json.loads(result.stdout)
            tasks = [
                TaskOutputDTO.model_validate(task_data) for task_data in tasks_data
            ]
            logger.debug(f"Retrieved {len(tasks)} tasks")
            return tasks
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise TaskValidationError(
                f"Invalid response from TaskWarrior: {result.stdout}"
            ) from e

    def get_recurring_task(self, task_id_or_uuid: str | int | UUID) -> TaskOutputDTO:
        """Get the parent recurring task template."""
        task_id_or_uuid = str(task_id_or_uuid)
        logger.debug(f"Getting recurring task with UUID: {task_id_or_uuid}")

        result = self.run_task_command(
            [str(task_id_or_uuid), "status:" + TaskStatus.RECURRING, "export"]
        )

        if result.returncode == 0:
            tasks_data = json.loads(result.stdout)
            if tasks_data:
                task = TaskOutputDTO.model_validate(tasks_data[0])
                logger.debug(f"Successfully retrieved recurring task: {task.uuid}")
                return task

        logger.debug(
            f"Recurring task {task_id_or_uuid} not found as recurring, trying normal retrieval"
        )
        return self.get_task(task_id_or_uuid)

    def get_recurring_instances(
        self, task_id_or_uuid: str | int | UUID
    ) -> list[TaskOutputDTO]:
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
            raise TaskNotFound(f"Invalid response from TaskWarrior: {result.stdout}") from e

    def delete_task(self, task_id_or_uuid: str | int | UUID) -> None:
        """Mark a task as deleted."""
        task_ref = str(task_id_or_uuid)
        logger.info(f"Deleting task: {task_ref}")

        result = self.run_task_command([task_ref, "delete"])

        if result.returncode != 0:
            error_msg = f"Failed to delete task: {result.stderr}"
            logger.error(error_msg)
            raise TaskNotFound(error_msg)

        logger.info(f"Successfully deleted task: {task_ref}")

    def purge_task(self, task_id_or_uuid: str | int | UUID) -> None:
        """Permanently remove a task."""
        task_ref = str(task_id_or_uuid)
        logger.info(f"Purging task: {task_ref}")

        result = self.run_task_command([task_ref, "purge"])

        if result.returncode != 0:
            error_msg = f"Failed to purge task: {result.stderr}"
            logger.error(error_msg)
            raise TaskNotFound(error_msg)

        logger.info(f"Successfully purged task: {task_ref}")

    def done_task(self, task_id_or_uuid: str | int | UUID) -> None:
        """Mark a task as completed."""
        task_ref = str(task_id_or_uuid)
        logger.info(f"Completing task: {task_ref}")

        result = self.run_task_command([task_ref, "done"])

        if result.returncode != 0:
            error_msg = f"Failed to mark task as done: {result.stderr}"
            logger.error(error_msg)
            raise TaskNotFound(error_msg)

        logger.info(f"Successfully completed task: {task_ref}")

    def start_task(self, task_id_or_uuid: str | int | UUID) -> None:
        """Start working on a task."""
        task_ref = str(task_id_or_uuid)
        logger.info(f"Starting task: {task_ref}")

        result = self.run_task_command([task_ref, "start"])

        if result.returncode != 0:
            error_msg = f"Failed to start task: {result.stderr}"
            logger.error(error_msg)
            raise TaskNotFound(error_msg)

        logger.info(f"Successfully started task: {task_ref}")

    def stop_task(self, task_id_or_uuid: str | int | UUID) -> None:
        """Stop working on a task."""
        task_ref = str(task_id_or_uuid)
        logger.info(f"Stopping task: {task_ref}")

        result = self.run_task_command([task_ref, "stop"])

        if result.returncode != 0:
            error_msg = f"Failed to stop task: {result.stderr}"
            logger.error(error_msg)
            raise TaskNotFound(error_msg)

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
            raise TaskNotFound(error_msg)

        logger.info(f"Successfully annotated task: {task_ref}")

    def get_info(self) -> dict[str, object]:
        """Get TaskWarrior configuration and version info."""
        info = {
            "task_cmd": self.task_cmd,
            "taskrc_file": self.taskrc_file,
            "options": self._options,
        }

        try:
            version_result = self.run_task_command(["--version"], no_opt=True)
            if version_result.returncode == 0 and version_result.stdout:
                version = version_result.stdout.strip()
                info["version"] = version
        except Exception:
            info["version"] = "unknown"
        return info

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
            result = self.run_task_command(["calc", date_str, "+ P1D"])
            if result.returncode:
                return False
            is_valid: bool = result.stdout.strip() != date_str.strip() + "P1D"
            return is_valid
        except subprocess.CalledProcessError:
            return False
