#!/usr/bin/env python3
"""Context management example."""

from taskwarrior import TaskWarrior, TaskInputDTO, Priority

# Initialize TaskWarrior with local config
tw = TaskWarrior(
    taskrc_path="./taskrc_example",
    data_location="./task_data"
)

# Define contexts
tw.define_context("work", "project:work")
tw.define_context("personal", "project:personal")

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
    print(f"- {ctx.name}: {ctx.filter}")

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
