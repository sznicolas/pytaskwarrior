import logging
from typing import List, Optional, Union
from uuid import UUID

from .exceptions import TaskNotFound, TaskValidationError
from .task import Task
from .main import TaskWarrior as MainTaskWarrior

logger = logging.getLogger(__name__)

__version__ = "0.1.0"
__author__ = "TaskWarrior Python Team"

DEFAULT_TASKRC_PATH = 'pytaskrc'
DEFAULT_TASKRC_CONTENT = """
# Default configuration set by pytaskwarrior
confirmation=0
news.version=99.99.99 # disable news output
"""
DEFAULT_CONFIG_OVERRIDES = {
    "confirmation": "off",
    "json.array": "TRUE",
    "verbose": "nothing"
}


class TaskWarrior(MainTaskWarrior):
    """A Python API wrapper for TaskWarrior, interacting via CLI commands."""
    
    def __init__(
        self,
        taskrc_path: Optional[str] = None,
        task_cmd: Optional[str] = None
    ):
        super().__init__(taskrc_path, task_cmd)
        
        # Create default config if it doesn't exist
        try:
            with open(self.taskrc_path, 'r') as f:
                pass
        except FileNotFoundError:
            with open(self.taskrc_path, 'w') as f:
                f.write(DEFAULT_TASKRC_CONTENT)
        
        self._validate_taskwarrior()
    
    def _validate_taskwarrior(self) -> None:
        """Validate that taskwarrior is installed and working."""
        try:
            result = self._run_task_command(["version"])
            if result.returncode != 0:
                logger.error(f"TaskWarrior validation failed: {result.stderr}")
                raise RuntimeError("TaskWarrior is not properly configured")
        except FileNotFoundError:
            logger.error("TaskWarrior command not found in PATH")
            raise RuntimeError("TaskWarrior command not found. Please install taskwarrior.")
    
    def _run_task_command(self, args: List[str]) -> subprocess.CompletedProcess:
        """Run a taskwarrior command."""
        # Prepend the taskrc path to all commands
        cmd = [self.task_cmd, f"rc:{self.taskrc_path}"] + args
        logger.debug(f"Running command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False  # We'll handle the error checking ourselves
            )
            
            if result.returncode != 0:
                logger.warning(f"Task command failed with return code {result.returncode}: {result.stderr}")
            
            logger.debug(f"Command result - stdout: {result.stdout[:100]}... stderr: {result.stderr[:100]}...")
            return result
            
        except Exception as e:
            logger.error(f"Exception while running task command: {e}")
            raise
