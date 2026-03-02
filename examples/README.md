# pytaskwarrior Examples

This directory contains isolated examples demonstrating different features of pytaskwarrior. All examples use the bundled `taskrc_example` configuration and `task_data` directory, so they won't interfere with your personal TaskWarrior setup.

## Quick Start

Run any example from the repository root:

```bash
cd /path/to/pytaskwarrior
python examples/example_1_basic.py
```

To use the TaskWarrior CLI with the same configuration:

```bash
task rc:examples/taskrc_example rc.data.location=examples/task_data <command>
```

## Examples Overview

### example_0_querying.py — Querying and Filtering Tasks
**Features:**
- Single task retrieval by ID and UUID (`get_task()`)
- Filtering with TaskWarrior expressions (`get_tasks()`)
- Listing all projects (`get_projects()`)
- Soft delete vs permanent purge (`delete_task()`, `purge_task()`)

**Use case:** Learn how to query, filter, and manage task lifecycle.

---

### example_1_basic.py — Basic Task Operations
**Features:**
- Initialize TaskWarrior
- Add a simple task (`add_task()`)
- Retrieve all tasks (`get_tasks()`)
- Display task details

**Use case:** Get started with basic CRUD operations.

---

### example_2_task_operations.py — Task Modifications
**Features:**
- Add multiple tasks
- Modify existing tasks (`modify_task()`)
- Mark tasks as completed (`done_task()`)
- Filter and list tasks

**Use case:** Understand how to update and complete tasks.

---

### example_3_contexts.py — Context Management
**Features:**
- Define contexts with read and write filters (`define_context()`)
- Apply and switch contexts (`apply_context()`)
- Unset context filters (`unset_context()`)
- List all defined contexts (`get_contexts()`)
- Check current context (`get_current_context()`)

**Use case:** Organize tasks using named filters (e.g., "work", "personal").

---

### example_4_recurring_tasks.py — Recurring Tasks
**Features:**
- Create daily, weekly, monthly recurring tasks
- Custom recurrence periods (e.g., "2weeks")
- Retrieve parent recurring task template (`get_recurring_task()`)
- List all instances (`get_recurring_instances()`)
- Complete recurring task instances

**Use case:** Automate repeating tasks (standups, reviews, billing).

---

### example_5_time_tracking.py — Time Tracking and Annotations
**Features:**
- Start and stop work on tasks (`start_task()`, `stop_task()`)
- Add timestamped notes to tasks (`annotate_task()`)
- Retrieve task details with timestamps
- View task history through annotations

**Use case:** Track active work and add progress notes.

---

### example_6_advanced_features.py — Date Calculations, UDAs, and Projects
**Features:**
- Calculate dates using TaskWarrior expressions (`task_calc()`)
- Validate date expressions (`date_validator()`)
- List all projects (`get_projects()`)
- Access UDA definitions (`reload_udas()`, `get_uda_names()`, `get_uda_config()`)
- Use UDAs in tasks (`TaskInputDTO(udas={...})`)

**Use case:** Advanced scheduling, custom attributes, and project organization.

---

## Feature Matrix

| Feature | Example |
|---------|---------|
| Task CRUD (Create, Read, Update, Delete) | 1, 2, 0 |
| Querying and filtering | 0 |
| Task lifecycle (delete vs purge) | 0 |
| Contexts | 3 |
| Recurring tasks | 4 |
| Time tracking (start/stop) | 5 |
| Annotations | 5 |
| Date calculations | 6 |
| User Defined Attributes (UDAs) | 6 |
| Projects | 6 |

## Isolation from Your TaskWarrior

All examples are **isolated** from your personal TaskWarrior configuration:

- They use `examples/taskrc_example` (not `~/.taskrc`)
- They use `examples/task_data` (not `~/.task`)
- No data is created or modified in your home directory
- You can run examples safely without affecting your tasks

After running examples, delete or clear `examples/task_data` to start fresh.

## Running Examples Interactively

Each example prints the TaskWarrior command needed to interact with the example's data:

```
Use the task CLI with the same resources: /usr/bin/task rc:... rc.data.location=... <command>
```

Copy that command and replace `<command>` with what you want to do:

```bash
/usr/bin/task rc:examples/taskrc_example rc.data.location=examples/task_data status:pending
```

## Customizing Examples

All examples follow the same pattern:

```python
import os
from taskwarrior import TaskWarrior, ...

# Initialize with local config
base_dir = os.path.dirname(__file__)
taskrc_path = os.path.join(base_dir, "taskrc_example")
data_dir = os.path.join(base_dir, "task_data")
tw = TaskWarrior(taskrc_file=taskrc_path, data_location=data_dir)

# ... your code ...
```

You can modify any example to experiment with different features. Changes are safe because you're not touching your real TaskWarrior data.

## Learning Path

If you're new to pytaskwarrior, follow this order:

1. **example_1_basic.py** — Understand initialization and basic operations
2. **example_0_querying.py** — Learn how to retrieve and filter tasks
3. **example_2_task_operations.py** — Practice modifying tasks
4. **example_3_contexts.py** — Organize tasks with contexts
5. **example_4_recurring_tasks.py** — Automate recurring tasks
6. **example_5_time_tracking.py** — Track time and add annotations
7. **example_6_advanced_features.py** — Explore advanced features

## Troubleshooting

**Error: "TaskWarrior command 'task' not found in PATH"**

Ensure TaskWarrior 3.4+ is installed:

```bash
task --version  # Should print version 3.4 or higher
which task      # Should show the path to the task binary
```

**Error: "No such file or directory: taskrc_example"**

Run examples from the repository root, not from within the examples directory.

**Data persists between example runs**

This is intentional. To start fresh, clear the `task_data` directory:

```bash
rm -rf examples/task_data/*
```

## Contributing New Examples

If you'd like to add an example, follow these guidelines:

1. Use the isolation pattern shown above
2. Add comprehensive docstrings and comments
3. Print the TaskWarrior command for manual testing
4. Update this README with your new example
5. Include a feature matrix entry

## License

All examples are part of pytaskwarrior and are licensed under the MIT License.
