#!/usr/bin/env python3

from src.taskwarrior import Priority, RecurrencePeriod, TaskDTO, TaskWarrior
import json

# Create a new task warrior instance
tw = TaskWarrior()

# Create a simple task using the DTO
task_dto = TaskDTO(
    description="Buy groceries",
    priority=Priority.HIGH,
    tags=["shopping", "personal"]
)

# Add the task
task = tw.add(task_dto)
print(f"Created task: {task}")

# List all tasks
tasks = tw.list()
print("All tasks:")
for t in tasks:
    print(f"  {t}")

# Complete the task
tw.done(task.uuid)
print("Task completed")

# List tasks again to see completion
tasks = tw.list()
print("All tasks after completion:")
for t in tasks:
    print(f"  {t}")
