#!/usr/bin/env python3
"""Advanced features: date calculations, UDAs, and projects.

This example is isolated from the user's TaskWarrior configuration. It uses the bundled examples/taskrc_example and examples/task_data to avoid touching ~/.taskrc or your TaskWarrior data.

Demonstrates:
  - Date calculations using TaskWarrior expressions (task_calc)
  - Date validation for TaskWarrior formats
  - User Defined Attributes (UDAs) configuration
  - Retrieving UDA metadata
  - Getting all defined projects
  - Tasks with custom UDA values
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

# === Date calculations ===
print("=== Date calculations using TaskWarrior expressions ===")

# Calculate dates relative to today
tomorrow = tw.task_calc("tomorrow")
print(f"Tomorrow: {tomorrow}")

next_week = tw.task_calc("today + 1week")
print(f"Today + 1 week: {next_week}")

next_month = tw.task_calc("eom")  # End of month
print(f"End of month: {next_month}")

next_monday = tw.task_calc("monday")
print(f"Next Monday: {next_monday}")

# Custom expression
custom = tw.task_calc("today + 2weeks - 3days")
print(f"Today + 2 weeks - 3 days: {custom}")

# === Date validation ===
print("\n=== Validating date expressions ===")

dates_to_test = [
    ("tomorrow", True),
    ("next monday", True),
    ("friday", True),
    ("eom", True),  # End of month
    ("today + 1week", True),
    ("2024-12-31", True),
    ("invalid date xyz", False),
    ("blah blah", False),
]

for date_expr, expected_valid in dates_to_test:
    is_valid = tw.date_validator(date_expr)
    status = "✓" if is_valid == expected_valid else "✗"
    print(f"  {status} '{date_expr}': {is_valid}")

# === Create tasks with calculated due dates ===
print("\n=== Creating tasks with calculated due dates ===")

# Use calculated date for a task
due_tomorrow = tw.task_calc("tomorrow")
task1 = TaskInputDTO(
    description="Complete urgent report",
    priority=Priority.HIGH,
    project="work",
    due=due_tomorrow
)
added1 = tw.add_task(task1)
print(f"Created task with due='tomorrow': {added1.description}")
print(f"  Due: {added1.due}")

# Use expression directly
task2 = TaskInputDTO(
    description="Quarterly planning meeting",
    priority=Priority.MEDIUM,
    project="work",
    due="friday"  # TaskWarrior will interpret as next Friday
)
added2 = tw.add_task(task2)
print(f"Created task with due='friday': {added2.description}")
print(f"  Due: {added2.due}")

# Schedule for later
task3 = TaskInputDTO(
    description="Vacation planning",
    priority=Priority.LOW,
    project="personal",
    scheduled=tw.task_calc("today + 1month")
)
added3 = tw.add_task(task3)
print(f"Created task with scheduled date: {added3.description}")
print(f"  Scheduled: {added3.scheduled}")

# === Projects ===
print("\n=== Working with projects ===")

# Create tasks in different projects
projects_to_demo = [
    ("dmc.fil.aretordre", "Process queue"),
    ("dmc.fil.adérouler", "Ongoing tasks"),
    ("perso", "Personal item"),
    ("perso.orl", "ORL appointment"),
    ("pro", "Professional task"),
]

for project_name, desc in projects_to_demo:
    task = TaskInputDTO(
        description=desc,
        project=project_name,
        priority=Priority.LOW
    )
    tw.add_task(task)
    print(f"  Created task in project '{project_name}'")

# Get all projects
print(f"\nAll defined projects:")
all_projects = tw.get_projects()
for proj in sorted(all_projects):
    print(f"  - {proj}")

# === User Defined Attributes (UDAs) ===
print("\n=== User Defined Attributes (UDAs) ===")

# Reload UDAs from taskrc (in case they were modified externally)
tw.reload_udas()
print("Reloaded UDAs from taskrc")

# Get all UDA names
uda_names = tw.get_uda_names()
print(f"\nDefined UDAs: {uda_names if uda_names else '(none defined)'}")

# Get configuration for a specific UDA (if any exist)
if uda_names:
    for uda_name in sorted(uda_names):
        uda_config = tw.get_uda_config(uda_name)
        if uda_config:
            print(f"\nUDA '{uda_name}':")
            print(f"  Type: {uda_config.type}")
            print(f"  Label: {uda_config.label}")
            if hasattr(uda_config, 'values') and uda_config.values:
                print(f"  Values: {uda_config.values}")
else:
    print("\nNo custom UDAs defined in this taskrc.")
    print("You can add UDAs by defining them in .taskrc, e.g.:")
    print("  report.next.labels=ID,Active,P,Project,Tag,Recur,S,Due,Until,Description,Urgency")
    print("  uda.severity.label=Severity")
    print("  uda.severity.type=string")
    print("  uda.severity.values=low,medium,high,critical")

# === Using UDAs in tasks ===
print("\n=== Creating tasks with UDA values ===")

# If UDAs are defined, demonstrate using them
if uda_names:
    # Create task with UDA values
    task_with_uda = TaskInputDTO(
        description="Complex task requiring severity tracking",
        priority=Priority.HIGH,
        project="work",
        udas={
            "severity": "high",
            "estimate": 8,  # if estimate is defined
        }
    )
    try:
        added_uda = tw.add_task(task_with_uda)
        print(f"Created task with UDAs: {added_uda.description}")
        
        # Retrieve and show UDA values
        retrieved = tw.get_task(added_uda.uuid)
        print(f"  Severity: {retrieved.get_uda('severity')}")
        print(f"  Estimate: {retrieved.get_uda('estimate')}")
    except Exception as e:
        print(f"  (Could not create task with UDAs: {e})")
else:
    print("Skipping UDA task creation (no UDAs defined)")

# === Summary ===
print("\n=== Feature Summary ===")
print("✓ Date calculations: task_calc()")
print("✓ Date validation: date_validator()")
print("✓ Project management: get_projects()")
print("✓ UDA configuration: get_uda_names(), get_uda_config()")
print("✓ Task UDAs: TaskInputDTO(udas={...}), task.get_uda(name)")
print("\nThese features enable:")
print("  - Dynamic scheduling based on complex date expressions")
print("  - Project organization and filtering")
print("  - Custom attributes for domain-specific task metadata")
