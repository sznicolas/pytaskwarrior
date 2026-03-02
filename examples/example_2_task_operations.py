#!/usr/bin/env python3
"""Task operations example.

This example is isolated from the user's TaskWarrior configuration. It uses the bundled examples/taskrc_example and examples/task_data to avoid touching ~/.taskrc or your TaskWarrior data.

Demonstrates:
  - Adding multiple tasks with different attributes
  - Modifying an existing task
  - Completing a task
  - Filtering tasks by status
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

# === Add multiple tasks ===
print("=== Creating multiple tasks ===")
tasks_data = [
    {
        "description": "Complete project proposal",
        "priority": Priority.HIGH,
        "project": "work",
        "tags": ["work", "urgent"]
    },
    {
        "description": "Buy groceries",
        "priority": Priority.MEDIUM,
        "project": "personal",
        "tags": ["shopping", "personal"]
    },
    {
        "description": "Call mom",
        "priority": Priority.LOW,
        "project": "personal",
        "tags": ["family", "personal"]
    }
]

added_tasks = []
for task_data in tasks_data:
    task = TaskInputDTO(**task_data)
    added_task = tw.add_task(task)
    added_tasks.append(added_task)
    print(f"Added #{added_task.index}: {added_task.description}")

# === Modify a task ===
print("\n=== Modifying a task ===")
if added_tasks:
    task_to_modify = added_tasks[0]
    print(f"Before: {task_to_modify.description}")
    print(f"  Priority: {task_to_modify.priority}")
    print(f"  Tags: {task_to_modify.tags}")

    # Update the task with new values
    updated_task = TaskInputDTO(
        description="Complete project proposal - UPDATED",
        priority=Priority.HIGH,
        project="work",
        tags=["work", "urgent", "completed"]
    )

    modified_task = tw.modify_task(updated_task, task_to_modify.uuid)
    print(f"\nAfter: {modified_task.description}")
    print(f"  Priority: {modified_task.priority}")
    print(f"  Tags: {modified_task.tags}")

# === Complete a task ===
print("\n=== Completing a task ===")
if added_tasks:
    task_to_complete = added_tasks[1]
    print(f"Completing: {task_to_complete.description}")
    tw.done_task(task_to_complete.uuid)
    print("Status changed to: completed")

# === List all pending tasks ===
print("\n=== Pending tasks ===")
pending_tasks = tw.get_tasks()
print(f"Total pending tasks: {len(pending_tasks)}\n")
for task in pending_tasks:
    print(f"  #{task.index}: {task.description}")
    print(f"        Status: {task.status}, Priority: {task.priority}, Project: {task.project}\n")
