#!/usr/bin/env python3

from src.taskwarrior import Priority, RecurrencePeriod, TaskWarrior
from src.taskwarrior.dto.task_dto import Priority, RecurrencePeriod, TaskInputDTO, TaskOutputDTO, TaskWarrior

# Create a new task warrior instance
tw = TaskWarrior()

# Create tasks with different date formats to test TaskWarrior's date handling
task_dto = TaskInputDTO(
    description="Buy groceries",
    priority=Priority.HIGH,
    tags=["shopping", "personal"]
)

# Add the task
task = tw.add_task(task_dto)
print(f"Created task: {task}")

# Create a task with a due date
task_with_due = TaskInputDTO(
    description="Submit report",
    priority=Priority.MEDIUM,
    tags=["work", "urgent"],
    due="tomorrow"
)

task2 = tw.add_task(task_with_due)
print(f"Created task with due date: {task2}")

# Create a task with scheduled date
task_with_scheduled = TaskInputDTO(
    description="Team meeting",
    priority=Priority.LOW,
    tags=["work", "meeting"],
    scheduled="next monday"
)

task3 = tw.add_task(task_with_scheduled)
print(f"Created task with scheduled date: {task3}")

# List all tasks to see how dates are handled
tasks = tw.get_tasks([])
print("All tasks:")
for t in tasks:
    print(f"  {t}")

# Complete the task
tw.done_task(task.uuid)
print("Task completed")

# List tasks again to see completion
tasks = tw.get_tasks([])
print("All tasks after completion:")
for t in tasks:
    print(f"  {t}")

# Test date parsing by creating a task with specific dates
task_with_dates = TaskInputDTO(
    description="Project deadline",
    priority=Priority.HIGH,
    tags=["work", "deadline"],
    due="2026-12-31",
    scheduled="2026-01-15"
)

task4 = tw.add_task(task_with_dates)
print(f"Created task with specific dates: {task4}")

# List all tasks again to see the date handling
tasks = tw.get_tasks([])
print("All tasks with dates:")
for t in tasks:
    print(f"  {t}")
