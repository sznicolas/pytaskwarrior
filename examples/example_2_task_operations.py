#!/usr/bin/env python3
"""Task operations example."""

from taskwarrior import TaskWarrior, TaskInputDTO, Priority

# Initialize TaskWarrior with local config
tw = TaskWarrior(
    taskrc_file="./taskrc_example",
    data_location="./task_data"
)

# Add multiple tasks
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
    print(f"Added: {added_task.description}")

# Modify a task
if added_tasks:
    task_to_modify = added_tasks[0]
    print(f"\nModifying task: {task_to_modify.description}")
    
    # Update the task
    updated_task = TaskInputDTO(
        description="Complete project proposal - UPDATED",
        priority=Priority.HIGH,
        project="work",
        tags=["work", "urgent", "completed"]
    )
    
    modified_task = tw.modify_task(updated_task, task_to_modify.uuid)
    print(f"Modified: {modified_task.description}")

# Mark a task as done
if added_tasks:
    task_to_complete = added_tasks[1]
    print(f"\nCompleting task: {task_to_complete.description}")
    tw.done_task(task_to_complete.uuid)
    print("Task marked as done")

# Get all pending tasks
pending_tasks = tw.get_tasks()
print(f"\nPending tasks: {len(pending_tasks)}")
for task in pending_tasks:
    print(f"  - {task.description} ({task.status})")
