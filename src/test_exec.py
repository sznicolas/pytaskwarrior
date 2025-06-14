from datetime import datetime, timedelta

from taskwarrior import *

def main():
    # Example usage
    api = TaskWarrior()

    # Create a new task
    task = Task(
        description="Write Taskwarrior API documentation",
        due=datetime.now() + timedelta(days=7),
        priority=TaskPriority.HIGH,
        project="Work",
        tags=["docs", "api"]
    )
    added_task = api.task_add(task)
    print(f"Added task: {added_task}")

    # Update task
    added_task.project = "Development"
    api.task_update(added_task)
    print(f"Updated task: {added_task}")

    # Filter tasks
    filtered_tasks = api.filter_tasks(status="pending", project="Development")
    print(f"Filtered tasks: {filtered_tasks}")

    # Add recurring task
    recurring_task = Task(
        description="Weekly team meeting",
        due=datetime.now() + timedelta(days=7),
        tags=["meeting"]
    )
    api.add_recurring_task(recurring_task, recur="weekly")
    print(f"Added recurring task: {recurring_task}")

    # Set and apply context
    api.set_context("work", "project:Development")
    api.apply_context("work")

    # Mark task as done
    api.task_done(added_task.uuid)
    print(f"Marked task {added_task.uuid} as done")

if __name__ == "__main__":
    main()
