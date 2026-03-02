#!/usr/bin/env python3
"""Context management example.

This example is isolated from the user's TaskWarrior configuration. It uses the bundled examples/taskrc_example and examples/task_data to avoid touching ~/.taskrc or your TaskWarrior data.
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
print(f"Use the task CLI with the same resources: {task_cmd} {options} <command>")

# Define contexts
tw.define_context("work", read_filter="project:work", write_filter="project:work")
tw.define_context("personal", read_filter="project:personal", write_filter="project:personal")

# Apply work context
tw.apply_context("work")
print(f"Current context: {tw.get_current_context()}")

# Add task in current context
task = TaskInputDTO(
    description="Complete project proposal",
    priority=Priority.HIGH,
    project="work"
)
added_task = tw.add_task(task)
print(f"Added task in work context: {added_task.description}")

# Apply personal context
tw.apply_context("personal")
print(f"Current context: {tw.get_current_context()}")

# Add another task
task2 = TaskInputDTO(
    description="Buy groceries",
    priority=Priority.MEDIUM,
    project="personal"
)
added_task2 = tw.add_task(task2)
print(f"Added task in personal context: {added_task2.description}")

# List contexts
contexts = tw.get_contexts()
print("\nDefined contexts:")
for ctx in contexts:
    print(f"- {ctx.name}: read={ctx.read_filter} write={ctx.write_filter}")

# Show tasks in current context (should be personal)
current_tasks = tw.get_tasks()
print(f"\nTasks in current context: {len(current_tasks)}")
for task in current_tasks:
    print(f"  - {task.description} (project: {task.project})")

# Unset context
tw.unset_context()
print(f"\nUnset context. Current context: {tw.get_current_context()}")

# Show all tasks
all_tasks = tw.get_tasks()
print(f"Total tasks: {len(all_tasks)}")
for task in all_tasks:
    print(f"  - {task.description} (project: {task.project})")
