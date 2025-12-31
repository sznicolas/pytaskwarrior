#!/usr/bin/env python3

"""
Demo script for pytaskwarrior functionality.
This script demonstrates adding tasks, inspecting them, and then deleting them.
"""

import tempfile
import os
from pathlib import Path
from src.taskwarrior import Task, TaskWarrior, Priority

def main():
    # Create a temporary directory for our demo
    with tempfile.TemporaryDirectory() as tmpdir:
        # Set up taskrc path
        taskrc_path = os.path.join(tmpdir, ".taskrc")
        
        # Create a basic taskrc file
        with open(taskrc_path, 'w') as f:
            f.write("# Demo configuration\n")
            f.write("confirmation=off\n")
            f.write("json.array=TRUE\n")
            f.write("verbose=nothing\n")
        
        # Create TaskWarrior instance
        tw = TaskWarrior(taskrc_path=taskrc_path)
        
        print("=== PyTaskwarrior Demo ===\n")
        
        # Create some sample tasks
        print("1. Creating sample tasks...")
        
        task1 = Task(
            description="Demo task 1",
            priority=Priority.HIGH,
            project="demo",
            tags=["work", "important"]
        )
        
        task2 = Task(
            description="Demo task 2",
            priority=Priority.MEDIUM,
            project="demo",
            tags=["personal", "todo"]
        )
        
        # Add tasks
        added_task1 = tw.add_task(task1)
        added_task2 = tw.add_task(task2)
        
        print(f"   Created task 1: {added_task1.uuid}")
        print(f"   Created task 2: {added_task2.uuid}")
        
        # List all tasks
        print("\n2. Listing all tasks...")
        all_tasks = tw.get_tasks([])
        for task in all_tasks:
            print(f"   - {task.description} (ID: {task.uuid}, Status: {task.status})")
        
        # Get specific tasks
        print("\n3. Retrieving individual tasks...")
        retrieved_task1 = tw.get_task(added_task1.uuid)
        print(f"   Retrieved task 1: {retrieved_task1.description} (Status: {retrieved_task1.status})")
        
        # Modify a task
        print("\n4. Modifying a task...")
        modified_task = retrieved_task1.copy()
        modified_task.description = "Modified demo task 1"
        modified_task.priority = Priority.LOW
        tw.modify_task(modified_task)
        
        # Verify modification
        updated_task = tw.get_task(added_task1.uuid)
        print(f"   Updated task: {updated_task.description} (Priority: {updated_task.priority})")
        
        # Delete a task
        print("\n5. Deleting a task...")
        tw.delete_task(added_task1.uuid)
        deleted_task = tw.get_task(added_task1.uuid)
        print(f"   Task status after delete: {deleted_task.status}")
        
        # List tasks again to see the deleted task
        print("\n6. Listing all tasks (including deleted)...")
        all_tasks = tw.get_tasks([])
        for task in all_tasks:
            print(f"   - {task.description} (ID: {task.uuid}, Status: {task.status})")
        
        # Purge the deleted task
        print("\n7. Purging the deleted task...")
        tw.purge_task(added_task1.uuid)
        
        # Try to get the purged task (should fail)
        print("\n8. Attempting to retrieve purged task...")
        try:
            tw.get_task(added_task1.uuid)
        except Exception as e:
            print(f"   Expected error: {e}")
        
        # Show final state
        print("\n9. Final task list...")
        remaining_tasks = tw.get_tasks([])
        if not remaining_tasks:
            print("   No tasks remaining")
        else:
            for task in remaining_tasks:
                print(f"   - {task.description} (ID: {task.uuid}, Status: {task.status})")
        
        print("\n=== Demo Complete ===")

if __name__ == "__main__":
    main()
