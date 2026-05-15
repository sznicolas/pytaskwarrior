#!/usr/bin/env python3
"""Local sync example.

Uses a temporary directory as a local sync server — no remote server needed.
Simulates two independent TaskWarrior clients (different data directories)
exchanging tasks through a shared local server directory.

Nothing is written to ~/.task or ~/.taskrc.

Demonstrates:
  - Setting up a local sync server directory
  - Two clients (Alice and Bob) sharing tasks via local sync
  - Adding tasks on one client and seeing them on another after sync
  - Completing a task on the second client and propagating the change back
"""

import tempfile
from pathlib import Path

from taskwarrior import Priority, TaskInputDTO, TaskWarrior
from taskwarrior.adapters.taskchampion_adapter import TaskChampionAdapter

# ---------------------------------------------------------------------------
# Setup: one shared server dir, two independent client data dirs
# ---------------------------------------------------------------------------

with tempfile.TemporaryDirectory(prefix="pytw_sync_demo_") as tmpdir:
    server_dir = Path(tmpdir) / "sync_server"
    alice_dir  = Path(tmpdir) / "alice"
    bob_dir    = Path(tmpdir) / "bob"

    server_dir.mkdir()
    alice_dir.mkdir()
    bob_dir.mkdir()

    print(f"Temporary workspace: {tmpdir}")
    print(f"  Sync server : {server_dir}")
    print(f"  Alice data  : {alice_dir}")
    print(f"  Bob data    : {bob_dir}\n")

    def make_client(data_dir: Path, name: str) -> TaskWarrior:
        adapter = TaskChampionAdapter(
            data_location=str(data_dir),
            sync_local_server_dir=str(server_dir),
        )
        return TaskWarrior(adapter=adapter)

    alice = make_client(alice_dir, "Alice")
    bob   = make_client(bob_dir,   "Bob")

    # -----------------------------------------------------------------------
    # Step 1 — Alice adds tasks and syncs to the local server
    # -----------------------------------------------------------------------
    print("=== Step 1: Alice adds tasks and syncs ===\n")

    tasks_alice = [
        TaskInputDTO(
            description="Write release notes",
            project="docs",
            priority=Priority.HIGH,
            tags=["writing"],
        ),
        TaskInputDTO(
            description="Fix flaky CI test",
            project="infra",
            priority=Priority.MEDIUM,
            tags=["ci", "bug"],
        ),
        TaskInputDTO(
            description="Update dependencies",
            project="infra",
            priority=Priority.LOW,
        ),
    ]

    added_by_alice = [alice.add_task(t) for t in tasks_alice]
    print("Alice's tasks before sync:")
    for t in alice.get_tasks():
        print(f"  #{t.index}  [{t.project}]  {t.description}")

    print("\nAlice syncs to local server …")
    alice.synchronize()
    print("Alice: sync done.\n")

    # -----------------------------------------------------------------------
    # Step 2 — Bob syncs and receives Alice's tasks
    # -----------------------------------------------------------------------
    print("=== Step 2: Bob syncs and receives Alice's tasks ===\n")

    bob.synchronize()
    print("Bob: sync done.\n")

    bobs_tasks = bob.get_tasks()
    print(f"Bob's tasks after sync ({len(bobs_tasks)} task(s)):")
    for t in bobs_tasks:
        print(f"  #{t.index}  [{t.project}]  {t.description}")

    # -----------------------------------------------------------------------
    # Step 3 — Bob completes a task and syncs back
    # -----------------------------------------------------------------------
    print("\n=== Step 3: Bob completes 'Fix flaky CI test' and syncs ===\n")

    ci_task = next(t for t in bobs_tasks if "CI" in t.description)
    print(f"Bob completes: #{ci_task.index}  {ci_task.description}")
    bob.done_task(ci_task.uuid)

    bob.synchronize()
    print("Bob: sync done.\n")

    # -----------------------------------------------------------------------
    # Step 4 — Alice syncs and sees the completion
    # -----------------------------------------------------------------------
    print("=== Step 4: Alice syncs and sees Bob's completion ===\n")

    alice.synchronize()
    print("Alice: sync done.\n")

    pending = alice.get_tasks()
    completed = alice.get_tasks(filter="status:completed", include_completed=True)

    print(f"Alice — pending tasks ({len(pending)}):")
    for t in pending:
        print(f"  #{t.index}  {t.description}")

    print(f"\nAlice — completed tasks ({len(completed)}):")
    for t in completed:
        ts = t.end.strftime("%Y-%m-%d %H:%M UTC") if t.end else "?"
        print(f"  {t.description}  (completed at {ts})")

    # -----------------------------------------------------------------------
    # Step 5 — Alice modifies a task and Bob receives the change
    # -----------------------------------------------------------------------
    print("\n=== Step 5: Alice updates 'Update dependencies' priority → HIGH ===\n")

    dep_task = next(t for t in alice.get_tasks() if "dependencies" in t.description)
    alice.modify_task(
        TaskInputDTO(
            description=dep_task.description,
            project=dep_task.project,
            priority=Priority.HIGH,
            tags=dep_task.tags,
        ),
        dep_task.uuid,
    )
    alice.synchronize()
    print("Alice: modified + synced.\n")

    bob.synchronize()
    print("Bob: sync done.\n")

    updated = next(t for t in bob.get_tasks() if "dependencies" in t.description)
    print(f"Bob sees: '{updated.description}'  priority={updated.priority}")

    # -----------------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------------
    print("\n=== Final state ===\n")
    print("Alice — pending:")
    for t in alice.get_tasks():
        print(f"  #{t.index}  priority={t.priority}  {t.description}")

    print("\nBob — pending:")
    for t in bob.get_tasks():
        print(f"  #{t.index}  priority={t.priority}  {t.description}")

print("\nTemporary directory cleaned up. Done.")
