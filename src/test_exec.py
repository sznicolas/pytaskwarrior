"""
PyTaskWarrior: A Simple Demo Script

This script demonstrates the usage of PyTaskWarrior library.
"""

import logging
from datetime import datetime, timedelta
from pprint import pp

from taskwarrior import Priority, TaskWarrior, Task

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Demonstrate PyTaskWarrior functionality."""
    
    # Define a TaskWarrior object, which verify if taskwarrior is installed
    logger.info("Initializing TaskWarrior...")
    tw = TaskWarrior()

    # Create a new task
    logger.info("Creating documentation task...")
    task = Task(
        description="🆘 Write PyTaskwarrior API documentation",
        due=datetime.now() + timedelta(days=7),
        priority=Priority.HIGH,
        project="SecretProject",
        tags=["docs", "dev"]
    )
    
    doc_task = tw.add_task(task)
    print("Added task (full object):")
    pp(doc_task.model_dump())

    # Update task
    logger.info("Updating task project...")
    doc_task.project = "Development"
    tw.modify_task(doc_task)
    print(f"\nUpdated task: {doc_task.description}\n")

    # Filter tasks
    logger.info("Filtering tasks...")
    filtered_tasks = tw.get_tasks(['status:pending', 'project:Development'])
    print(f"Filtered tasks: {[f.description for f in filtered_tasks]}\n")

    # Add recurring task
    logger.info("Creating recurring task...")
    recurring_task = Task(
        description="Weekly team meeting 🍺",
        due=datetime.now() + timedelta(days=7),
        tags=["meeting"],
        recur="weekly"
    )
    tw.add_task(recurring_task)
    print(f"Added recurring task: {recurring_task.description}\n")

    # Set and apply context
    logger.info("Setting up context...")
    try:
        tw.set_context("work", "project:Development")
        #tw.apply_context("work")  # Uncomment to apply context
    except Exception as e:
        logger.warning(f"Could not set context: {e}")

    print(f'Work on "{doc_task.description}...')
    tw.start_task(doc_task.uuid)
    
    # Mark task as done
    logger.info("Completing task...")
    print(f'Wow! It was easy! Mark task "{doc_task.description}"({doc_task.uuid}) as done')
    tw.done_task(doc_task.uuid)
    
    print("You can now check your tasks with `task`, `task all`, ...")

if __name__ == "__main__":
    main()
