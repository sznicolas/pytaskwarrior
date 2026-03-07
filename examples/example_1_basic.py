#!/usr/bin/env python3
"""Basic TaskWarrior example.

This example is isolated from the user's TaskWarrior configuration. It uses the bundled examples/taskrc_example and examples/task_data to avoid touching ~/.taskrc or your TaskWarrior data.

Demonstrates:
  - Initializing TaskWarrior with custom configuration
  - Creating a task with priority and tags
  - Retrieving all tasks
  - Displaying task details
"""

import os

from taskwarrior import Priority, TaskInputDTO, TaskWarrior

# Initialize TaskWarrior with local config using example-local files
base_dir = os.path.dirname(__file__)
taskrc_path = os.path.join(base_dir, "taskrc_example")
data_dir = os.path.join(base_dir, "task_data")
tw = TaskWarrior(taskrc_file=taskrc_path, data_location=data_dir)
# Show how to run the task CLI with the same resources
info = tw.get_info()
task_cmd = str(info["task_cmd"])
options = " ".join(info["options"])
print(f"Use the task CLI with the same resources: {task_cmd} {options} <command>\n")

# === Create a simple task ===
print("=== Creating a task ===")
task = TaskInputDTO(
    description="Buy groceries",
    priority=Priority.HIGH,
    tags=["shopping", "personal"]
)

added_task = tw.add_task(task)
print(f"Added task: {added_task.description}")
print(f"  Task ID: {added_task.index}")
print(f"  Task UUID: {added_task.uuid}")
print(f"  Priority: {added_task.priority}")

# === Retrieve all tasks ===
print("\n=== Retrieving all tasks ===")
tasks = tw.get_tasks()
print(f"Total pending tasks: {len(tasks)}\n")

# === Show task details ===
print("=== Task details ===")
if tasks:
    task = tasks[-1]
    print(f"Task #{task.index}: {task.description}")
    print(f"  UUID: {task.uuid}")
    print(f"  Status: {task.status}")
    print(f"  Priority: {task.priority}")
    print(f"  Tags: {task.tags}")
    print(f"  Urgency: {task.urgency}")
    print(f"  Created: {task.entry}")
    print(f"  Modified: {task.modified}")
