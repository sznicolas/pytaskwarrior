#!/usr/bin/env python3
"""Time tracking and annotations example.

This example is isolated from the user's TaskWarrior configuration. It uses the bundled examples/taskrc_example and examples/task_data to avoid touching ~/.taskrc or your TaskWarrior data.

Demonstrates:
  - Starting and stopping work on tasks (time tracking)
  - Adding annotations (timestamped notes)
  - Retrieving task details with timestamps
  - Viewing task history via annotations
"""

import os
from taskwarrior import TaskWarrior, TaskInputDTO, Priority

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

# === Create a task ===
print("=== Creating a task ===")
task_input = TaskInputDTO(
    description="Implement user authentication feature",
    priority=Priority.HIGH,
    project="work",
    tags=["feature", "backend"]
)
task = tw.add_task(task_input)
print(f"Created task #{task.index}: {task.description}")
print(f"  UUID: {task.uuid}")
print(f"  Status: {task.status}")
print(f"  Start time: {task.start}")

# === Add initial annotation ===
print("\n=== Adding annotations ===")
tw.annotate_task(task.uuid, "Started implementation with OAuth2")
print(f"Added annotation: 'Started implementation with OAuth2'")

tw.annotate_task(task.uuid, "Found legacy code to refactor")
print(f"Added annotation: 'Found legacy code to refactor'")

tw.annotate_task(task.uuid, "Pair programming session with Alice")
print(f"Added annotation: 'Pair programming session with Alice'")

# === Start working on the task ===
print("\n=== Starting work on the task ===")
tw.start_task(task.uuid)
print(f"Task started (time-tracking enabled)")

# Retrieve updated task to see start time
task_started = tw.get_task(task.uuid)
print(f"Task details after start:")
print(f"  Description: {task_started.description}")
print(f"  Status: {task_started.status}")
print(f"  Start time: {task_started.start}")

# === Add annotation while working ===
print("\n=== Adding progress annotation ===")
tw.annotate_task(task.uuid, "Completed authentication middleware")
print(f"Added annotation: 'Completed authentication middleware'")

# === Stop working on the task ===
print("\n=== Stopping work on the task ===")
tw.stop_task(task.uuid)
print(f"Task stopped (time-tracking paused)")

task_stopped = tw.get_task(task.uuid)
print(f"Task details after stop:")
print(f"  Status: {task_stopped.status}")
print(f"  Start time: {task_stopped.start}")

# === Retrieve task with all annotations ===
print("\n=== Task with all annotations ===")
final_task = tw.get_task(task.uuid)
print(f"Task: {final_task.description}")
print(f"  UUID: {final_task.uuid}")
print(f"  Status: {final_task.status}")
print(f"  Priority: {final_task.priority}")
print(f"  Created: {final_task.entry}")
print(f"  Modified: {final_task.modified}")
print(f"  Started: {final_task.start}")
print(f"  Tags: {final_task.tags}")
print(f"  Urgency: {final_task.urgency}")

print(f"\nAnnotations ({len(final_task.annotations)}):")
for i, ann in enumerate(final_task.annotations, 1):
    print(f"  {i}. [{ann.entry}] {ann.description}")

# === Create another task and track it ===
print("\n\n=== Another task with different workflow ===")
task2_input = TaskInputDTO(
    description="Code review: Pull request #456",
    priority=Priority.MEDIUM,
    project="work",
    tags=["review", "code"],
    annotations=["Needs focus on error handling"]
)
task2 = tw.add_task(task2_input)
print(f"Created task #{task2.index}: {task2.description}")

# Start work
tw.start_task(task2.uuid)
print(f"Started working on task #{task2.index}")

tw.annotate_task(task2.uuid, "Reviewed first 10 files")
tw.annotate_task(task2.uuid, "Found 3 issues to address")
tw.annotate_task(task2.uuid, "Left feedback on GitHub")

# Stop work
tw.stop_task(task2.uuid)
print(f"Stopped working on task #{task2.index}")

# Retrieve final state
task2_final = tw.get_task(task2.uuid)
print(f"\nTask details:")
print(f"  {task2_final.description}")
print(f"  Status: {task2_final.status}")
print(f"  Annotations: {len(task2_final.annotations)}")

# === List all tasks with their start status ===
print("\n=== All tasks with active tracking status ===")
all_tasks = tw.get_tasks()
for t in all_tasks:
    tracking_status = "🟢 Active" if t.start else "⏸️  Idle"
    print(f"  {tracking_status} #{t.index}: {t.description}")

print("\nTime tracking workflow:")
print("  1. Create task")
print("  2. Add annotations as you work")
print("  3. Call start_task() when you begin")
print("  4. Call stop_task() when you pause/finish")
print("  5. View progress via annotations and timestamps")
