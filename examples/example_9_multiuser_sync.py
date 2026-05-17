#!/usr/bin/env python3
"""
Multi-user sync demo: Alice (in-memory) and Bob (on-disk) with a shared master.
- Master: examples/task_data/master (persistent)
- Bob:    examples/task_data/bob    (persistent)
- Alice:  in-memory (ephemeral)

You can run this script multiple times; Bob and master persist, Alice is always fresh.
"""
import os
from pathlib import Path

from taskwarrior.adapters.taskchampion_adapter import TaskChampionAdapter
from taskwarrior.dto.task_dto import TaskInputDTO
from taskwarrior.enums import Priority

EXAMPLES = Path(__file__).parent
DATA = EXAMPLES / "task_data"
MASTER = DATA / "master"
BOB = DATA / "bob"

os.makedirs(MASTER, exist_ok=True)
os.makedirs(BOB, exist_ok=True)

# --- Helper to print tasks ---
def print_tasks(label, adapter):
    print(f"\n--- {label} ---")
    tasks = adapter.get_tasks()
    if not tasks:
        print("(no tasks)")
    for t in tasks:
        print(f"- {t.description} [status={t.status}] (uuid={str(t.uuid)[:8]})")

# --- Create adapters ---
master_dir = str(MASTER)
bob_dir = str(BOB)

bob = TaskChampionAdapter(data_location=bob_dir, sync_local_server_dir=master_dir)
alice = TaskChampionAdapter(data_location=None, sync_local_server_dir=master_dir)  # in-memory
master = TaskChampionAdapter(data_location=master_dir)

# --- Show initial state ---
print("Initial state (before any sync):")
print_tasks("Master", master)
print_tasks("Bob", bob)
print_tasks("Alice", alice)

# --- Bob adds a task if none exist ---
if not bob.get_tasks():
    t = TaskInputDTO(description="Bob's first persistent task", priority=Priority.HIGH)
    bob.add_task(t)
    print("\nBob added a task.")

# --- Alice adds a task (always fresh) ---
alice.add_task(TaskInputDTO(description="Alice's ephemeral task", priority=Priority.MEDIUM))
print("\nAlice added a task.")

# --- Bob completes his first task if any exist and not completed ---
bob_tasks = bob.get_tasks()
if bob_tasks:
    t = bob_tasks[0]
    if t.status != "completed":
        bob.done_task(t.uuid)
        print(f"\nBob completed: {t.description}")

# --- Print all before sync ---
print("\nState before sync:")
print_tasks("Master", master)
print_tasks("Bob", bob)
print_tasks("Alice", alice)

# --- Sync ---
print("\nSyncing...")
bob.synchronize()
alice.synchronize()

# --- Print all after sync ---
print("\nState after sync:")
print_tasks("Master", master)
print_tasks("Bob", bob)
print_tasks("Alice", alice)

print("\nDone. You can rerun this script to see persistent changes for Bob and master. Alice is always fresh.")
