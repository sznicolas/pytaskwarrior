#!/usr/bin/env python3
"""Basic TaskWarrior example."""

from src.taskwarrior import TaskWarrior, TaskInputDTO, Priority

# Initialize TaskWarrior with local config
tw = TaskWarrior(
    taskrc_path="./taskrc_example",
    data_location="./task_data"
)

# Add a simple task
task = TaskInputDTO(
    description="Buy groceries",
    priority=Priority.HIGH,
    tags=["shopping", "personal"]
)

added_task = tw.add_task(task)
print(f"Added task: {added_task.description}")
print(f"Task ID: {added_task.index}")
print(f"Task UUID: {added_task.uuid}")

# Get all tasks
tasks = tw.get_tasks()
print(f"\nTotal tasks: {len(tasks)}")

# Show first task details
if tasks:
    task = tasks[0]
    print(f"Task details:")
    print(f"  Description: {task.description}")
    print(f"  Status: {task.status}")
    print(f"  Priority: {task.priority}")
    print(f"  Tags: {task.tags}")
