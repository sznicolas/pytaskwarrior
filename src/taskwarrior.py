from __future__ import annotations
from datetime import timedelta
from uuid import UUID
import json
from os import environ, getenv, path
import subprocess
import shutil
from typing import List

import isodate

from twmodels import Task, TWTask
"""
A taskrc must exist for `task`, by default ~/.taskrc.
As we are in a non interactive mode, we better use a custom taskrc file to set our conf
especially `confirmation=off`
This is the default, overridable by TASKRC env, and next by taskrc_path in TaskWarrior.__init()"""
DEFAULT_TASKRCPATH = '/tmp/pytaskrc'
DEFAULT_TASKRC_CONTENT = """
# Default configuration set by pytaskwarrior
confirmation=0
news.version=99.99.99 # disable news output
"""
DEFAULT_CONFIG_OVERRIDES = { # we must at least have confirmation off. !!! Not implemented yet. To be improved and simplified.
    "confirmation": "off",
    "json.array": "TRUE",
    "verbose": "nothing"
}


def parse_datetime_or_timedelta(val):
    """Returns a string, date time or iso 8601 duration"""
    if isinstance(val, timedelta):
        return isodate.duration_isoformat(val)
    else:
        return str(val)


class TaskWarrior:
    """A Python API wrapper for TaskWarrior, interacting via CLI commands."""
    def __init__(
            self,
            taskrc_path: str = None,
            #            config_overrides: dict[str, str] = None,
            task_cmd: str = None
            ):
        """
        Initialize the TaskWarrior API.

        Args:
            taskrc_path: Optional path to the .taskrc file. If None, uses default.
            TODO: implement this: config_overrides: Optional dict passed to `task`. As it overrides the defauts, should have at least `confirmation: off
            task_cmd: Optional path to the command.
        """
        if taskrc_path:
            self.taskrc_path = taskrc_path
        else:
            self.taskrc_path = getenv('TASKRC', path.join(path.dirname(__file__), DEFAULT_TASKRCPATH))
        environ['TASKRC'] = self.taskrc_path
        try:
            with open(self.taskrc_path, 'x') as file:
                print(f'Warning; taskrc file "{self.taskrc_path}" not found. Create it')
                file.write(DEFAULT_TASKRC_CONTENT)
        except FileExistsError:
            ...
#        self.config_overrides = config_overrides or DEFAULT_CONFIG_OVERRIDES
        if not task_cmd:
            self.task_cmd = shutil.which('task')
            if self.task_cmd is None:
                raise RuntimeError("Taskwarrior is not found in PATH.")
        else:
            self.task_cmd = task_cmd
        self._validate_taskwarrior()

    def _validate_taskwarrior(self) -> None:
        """Ensure Taskwarrior is installed and accessible."""
        try:
            subprocess.run([self.task_cmd, "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError("Taskwarrior is not installed or not found in PATH.")

    def _build_args(self, task: Task) -> dict:
        args = []
        if task.description:
            args.extend(task.description.split())
        if task.priority:
            args.extend(["priority:" + task.priority])
        if task.due:
            args.extend(["due:" + parse_datetime_or_timedelta(task.due)])
        if task.until:
            args.extend(["until:" + parse_datetime_or_timedelta(task.until)])
        if task.scheduled:
            args.extend(["scheduled:" + parse_datetime_or_timedelta(task.scheduled)])
        if task.wait:
            args.extend(["wait:" + parse_datetime_or_timedelta(task.wait)])
        if task.project:
            args.extend(["project:" + task.project])
        if task.tags:
            args.extend([f"+{tag}" for tag in task.tags])
        if task.recur:
            args.extend(["recur:" + task.recur])
        if task.depends:
            args.extend(["depends:" + ",".join(str(uuid) for uuid in task.depends)])
        if task.context:
            args.extend(["context:" + task.context])
        return args

    def _run_task_command(self, args: list[str]) -> subprocess.CompletedProcess:
        """
        Execute a TaskWarrior command via subprocess.

        Args:
            args: List of command arguments to append to the base task command.

        Returns:
            subprocess.CompletedProcess: Result of the command execution.

        Raises:
            RuntimeError: If the command fails.
        """
#        ' '.join([ f'rc.{k}={v}' for k, v in self.config_overrides.items()])

        command = [self.task_cmd] + args
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True,
                env={**environ}
            )
            return result
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"TaskWarrior command failed: {e.stderr}")


    def add_task(self, task: Task) -> TWTask:
        # TODO: if exists annotation, must be set after the task creation.
        args = ['add']
        args += self._build_args(task)
        result = self._run_task_command(args)
        task_id = None
        for line in result.stdout.splitlines():
            if 'Created task' in line:
                task_id = int(line.removeprefix('Created task ').split()[0].strip("."))
        return self.get_task(task_id)

    def modify_task(self, task: Task) -> TWTask:
        """
        Modify an existing task in TaskWarrior.

        Args:
            task: Task object with updated fields.

        Returns:
            Task: Updated task object.

        Raises:
            ValueError: If task ID or UUID is missing.
        """
        try:
            self.get_task(task.uuid)
        except RuntimeError:
            raise ValueError("Task UUID required to modify a task")
        args = [str(task.uuid), 'modify']
        args += self._build_args(task)
        self._run_task_command(args)
        return self.get_task(task.uuid)

    def get_task(self, task_id_or_uuid: str) -> TWTask:
        """
        Retrieve a task by ID or UUID.

        Args:
            task_id_or_uuid: Task ID or UUID.

        Returns:
            TWTask: Task object.

        Raises:
            RuntimeError: If task is not found.
        """
        result = self._run_task_command([str(task_id_or_uuid), "export"])
        tasks_data = json.loads(result.stdout)
        if not tasks_data:
            raise RuntimeError(f"Task {task_id_or_uuid} not found.")
        return TWTask(**tasks_data[0])

    def get_tasks(self, filter_args: list[str]) -> list[TWTask]:
        """
        Retrieves all tasks matching.

        Args:
            filter_args: filter list as accepted by task

        Returns:
            list[Task]: matching tasks
        """
        # sanitize
        args = []
        for arg in filter_args:
            args.append(str(arg))
        result = self._run_task_command(args + ["export"])
        tasks = json.loads(result.stdout)
        return [TWTask(**task) for task in tasks]

    def delete_task(self, uuid: UUID) -> None:
        """Delete a task by UUID."""
        self._run_task_command([str(uuid), "delete"])

    def purge_task(self, uuid: UUID) -> None:
        """Delete a task by UUID."""
        self._run_task_command([str(uuid), "purge"])

    def done_task(self, uuid: UUID) -> None:
        """Mark a task as done by UUID."""
        self._run_task_command([str(uuid), "done"])

    def start_task(self, uuid: UUID) -> None:
        """Start a task by UUID."""
        self._run_task_command([str(uuid), "start"])

    def stop_task(self, uuid: UUID) -> None:
        """Stop a task by UUID."""
        self._run_task_command([str(uuid), "stop"])

    def annotate_task(self, uuid: UUID, annotation: str) -> None:
        """Add an annotation to a task."""
        self._run_task_command([str(uuid), "annotate", annotation])

    def get_projects(self) -> List[str]:
        """Returns a project list"""
        projects = []
        result = self._run_task_command(['_projects'])
        for proj in result.stdout.splitlines():
            projects.append(proj)
        return projects

    def get_tags(self) -> List[str]:
        """Get a list of user's tags"""
        tags = []
        result = self._run_task_command(['tags'])
        lines = result.stdout.splitlines()
        if 'Tag' not in lines[1]:
            raise ValueError('Output format not matching')
        for tag in lines[3:]:
            if tag:
                tags.append(tag.split()[0])
            else:
                return tags

    def calc(self, expr: str) -> str:
        """Calculator, especially useful for dates calculations. See TaskWarrior documentation"""
        result = self._run_task_command(['calc', expr])
        return result.stdout.strip()
#    def define_context(self, context: str, filter_str: str) -> None:
#        """Define a context with a filter."""
#        self._run_task_command(["context", "define", context, filter_str])
#
#    def apply_context(self, context: str) -> None:
#        """Apply a context to filter tasks."""
#        self._run_task_command(["context", context])
#
#    def remove_context(self) -> None:
#        """Remove the current context."""
#        self._run_task_command(["context", "none"])
