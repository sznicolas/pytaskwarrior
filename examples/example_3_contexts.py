#!/usr/bin/env python3
"""Context management example."""

from taskwarrior import TaskWarrior, TaskInputDTO

tw = TaskWarrior(
    taskrc_path="./taskrc_example",
    data_location="./task_data"
)

# Define contexts
tw.define_context("work", "project:work")
tw.define_context("personal", "project:personal")

# Apply context
tw.apply_context("work")
print(f"Current context: {tw.get_current_context()}")

# Add task in current context
task = TaskInputDTO(
    description="Complete project proposal",
    project="work"
)
added_task = tw.add_task(task)
print(f"Added task in work context: {added_task.description}")

# List contexts
contexts = tw.get_contexts()
print("Defined contexts:")
for ctx in contexts:
    print(f"- {ctx.name}: {ctx.filter}")
