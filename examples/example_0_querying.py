#!/usr/bin/env python3
"""Querying and filtering tasks example.

This example is isolated from the user's TaskWarrior configuration. It uses the bundled examples/taskrc_example and examples/task_data to avoid touching ~/.taskrc or your TaskWarrior data.

Demonstrates:
  - Single task retrieval by ID and UUID
  - Filtering tasks with TaskWarrior filter expressions
  - Listing projects
  - Soft delete vs permanent purge
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

# Create sample tasks
print("=== Creating sample tasks ===")
task1 = TaskInputDTO(
    description="Fix critical bug in authentication",
    priority=Priority.HIGH,
    project="work",
    tags=["bug", "urgent"]
)
added1 = tw.add_task(task1)
print(f"Added task #{added1.index} (UUID: {added1.uuid})")

task2 = TaskInputDTO(
    description="Review code changes",
    priority=Priority.MEDIUM,
    project="work",
    tags=["review"]
)
added2 = tw.add_task(task2)
print(f"Added task #{added2.index} (UUID: {added2.uuid})")

task3 = TaskInputDTO(
    description="Buy birthday gift",
    priority=Priority.LOW,
    project="personal",
    tags=["shopping"]
)
added3 = tw.add_task(task3)
print(f"Added task #{added3.index} (UUID: {added3.uuid})")

# === Retrieve single task by ID ===
print("\n=== Single task retrieval by ID ===")
task_by_id = tw.get_task(1)
print(f"Task #{task_by_id.index}: {task_by_id.description}")
print(f"  Status: {task_by_id.status}")
print(f"  Priority: {task_by_id.priority}")
print(f"  Tags: {task_by_id.tags}")

# === Retrieve single task by UUID ===
print("\n=== Single task retrieval by UUID ===")
task_by_uuid = tw.get_task(added2.uuid)
print(f"Task #{task_by_uuid.index}: {task_by_uuid.description}")
print(f"  Project: {task_by_uuid.project}")
print(f"  Urgency: {task_by_uuid.urgency}")

# === Filter by project ===
print("\n=== Filter by project (project:work) ===")
work_tasks = tw.get_tasks("project:work")
for task in work_tasks:
    print(f"  - {task.description} (priority: {task.priority})")

# === Filter by tag ===
print("\n=== Filter by tag (+urgent) ===")
urgent_tasks = tw.get_tasks("+urgent")
for task in urgent_tasks:
    print(f"  - {task.description}")

# === Filter by priority ===
print("\n=== Filter by priority (priority:H) ===")
high_priority = tw.get_tasks("priority:H")
for task in high_priority:
    print(f"  - {task.description}")

# === Complex filter ===
print("\n=== Complex filter (project:work or +shopping) ===")
complex_filter = tw.get_tasks("project:work or +shopping")
for task in complex_filter:
    print(f"  - {task.description} (project: {task.project})")

# === List all projects ===
print("\n=== All projects ===")
projects = tw.get_projects()
print(f"Projects: {projects}")

# === Demonstrate delete vs purge ===
print("\n=== Delete vs Purge ===")
task_to_delete = added3
print(f"Soft deleting task #{task_to_delete.index}: {task_to_delete.description}")
tw.delete_task(task_to_delete.uuid)

# After soft delete, the task is still in the database with status=deleted
all_tasks_including_deleted = tw.get_tasks(filter_args="status:deleted")
print(f"Tasks with status=deleted: {len(all_tasks_including_deleted)}")
if all_tasks_including_deleted:
    print(f"  - {all_tasks_including_deleted[0].description} (status: {all_tasks_including_deleted[0].status})")

# Permanently purge the task (cannot be undone)
print(f"\nPermanently purging task #{task_to_delete.index}")
tw.purge_task(task_to_delete.uuid)

# After purge, task is completely gone
all_remaining = tw.get_tasks("status.not:completed")
print(f"Remaining tasks after purge: {len(all_remaining)}")

# === Show all tasks in different statuses ===
print("\n=== All pending tasks ===")
pending = tw.get_tasks()
for task in pending:
    print(f"  - {task.description} (status: {task.status})")

print(f"\nTotal pending tasks: {len(pending)}")
