#!/usr/bin/env python3
"""Recurring tasks example.

This example is isolated from the user's TaskWarrior configuration. It uses the bundled examples/taskrc_example and examples/task_data to avoid touching ~/.taskrc or your TaskWarrior data.

Demonstrates:
  - Creating recurring tasks
  - Retrieving parent recurring task template
  - Listing all instances of a recurring task
  - Managing recurring task periods
"""

import os
from taskwarrior import TaskWarrior, TaskInputDTO, Priority, RecurrencePeriod

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

# === Create a daily recurring task ===
print("=== Creating a daily recurring task ===")
daily_standup = TaskInputDTO(
    description="Team standup meeting",
    priority=Priority.HIGH,
    project="work",
    tags=["meeting", "daily"],
    recur=RecurrencePeriod.DAILY,
    due="09:00",  # TaskWarrior will interpret this as 9 AM
)
added_daily = tw.add_task(daily_standup)
print(f"Created recurring task #{added_daily.index}: {added_daily.description}")
print(f"  UUID: {added_daily.uuid}")
print(f"  Recurrence: {added_daily.recur}")
print(f"  Due: {added_daily.due}")

# === Create a weekly recurring task ===
print("\n=== Creating a weekly recurring task ===")
weekly_review = TaskInputDTO(
    description="Weekly project review",
    priority=Priority.MEDIUM,
    project="work",
    tags=["review", "weekly"],
    recur=RecurrencePeriod.WEEKLY,
    due="friday",
)
added_weekly = tw.add_task(weekly_review)
print(f"Created recurring task #{added_weekly.index}: {added_weekly.description}")
print(f"  UUID: {added_weekly.uuid}")
print(f"  Recurrence: {added_weekly.recur}")
print(f"  Due: {added_weekly.due}")

# === Create a monthly recurring task ===
print("\n=== Creating a monthly recurring task ===")
monthly_billing = TaskInputDTO(
    description="Pay monthly bills",
    priority=Priority.MEDIUM,
    project="personal",
    tags=["billing", "monthly"],
    recur=RecurrencePeriod.MONTHLY,
    due="1st",
)
added_monthly = tw.add_task(monthly_billing)
print(f"Created recurring task #{added_monthly.index}: {added_monthly.description}")
print(f"  UUID: {added_monthly.uuid}")
print(f"  Recurrence: {added_monthly.recur}")
print(f"  Due: {added_monthly.due}")

# Custom recurrence is not implemented yet
## === Create a custom recurrence period ===
#print("\n=== Creating a custom recurrence period (bi-weekly) ===")
#biweekly_report = TaskInputDTO(
#    description="Bi-weekly progress report",
#    priority=Priority.MEDIUM,
#    project="work",
#    tags=["report"],
#    recur="2weeks",  # Custom recurrence: not in the enum
#    due="wednesday",
#)
#added_biweekly = tw.add_task(biweekly_report)
#print(f"Created recurring task #{added_biweekly.index}: {added_biweekly.description}")
#print(f"  UUID: {added_biweekly.uuid}")
#print(f"  Recurrence: {added_biweekly.recur}")

# === Get the parent recurring task template ===
print(f"\n=== Retrieving parent recurring task template ===")
parent_daily = tw.get_recurring_task(added_daily.uuid)
print(f"Parent task: {parent_daily.description}")
print(f"  Status: {parent_daily.status}")
print(f"  Recur: {parent_daily.recur}")
print(f"  Rtype: {parent_daily.rtype}")  # Recurring task type

# === Get all instances of a recurring task ===
print(f"\n=== Instances of the daily standup recurring task ===")
instances = tw.get_recurring_instances(added_daily.uuid)
print(f"Found {len(instances)} instance(s) of the recurring task")
for instance in instances:
    print(f"  - #{instance.index}: {instance.description}")
    print(f"      Due: {instance.due}")
    print(f"      Parent: {instance.parent}")
    print(f"      Status: {instance.status}")

# === Complete one instance of a recurring task ===
print(f"\n=== Completing an instance of a recurring task ===")
if instances:
    first_instance = instances[0]
    print(f"Completing task #{first_instance.index}")
    tw.done_task(first_instance.uuid)
    print(f"Task marked as completed")
    
    # The parent task template remains and will generate new instances
    parent_after = tw.get_recurring_task(added_daily.uuid)
    print(f"Parent task still exists: {parent_after.description}")

# === List all recurring tasks ===
print(f"\n=== All recurring task templates ===")
all_tasks = tw.get_tasks()
print(f"Total pending tasks: {len(all_tasks)}")

# Filter for tasks that have recur set
recurring_templates = [t for t in all_tasks if t.recur]
print(f"Recurring task templates: {len(recurring_templates)}")
for task in recurring_templates:
    print(f"  - #{task.index}: {task.description} (recur: {task.recur}, due: {task.due})")

print("\nNote: TaskWarrior creates instances automatically as the due date approaches.")
print("You can see instances with 'get_recurring_instances(parent_uuid)'.")
