"""Tests for the undo/snapshot flow used by poc_taskchampion_undo_interactive_fr.py.

Root-cause regression guard:
    ``snapshot_ops_set()`` must commit an ``Operation.UndoPoint`` so that
    ``Replica.get_undo_operations()`` only returns operations recorded *after*
    the snapshot.  Without an undo point every committed operation is returned,
    and ``commit_reversed_operations()`` wipes the entire task history.
"""

from __future__ import annotations

import os
import sys

import pytest

# The POC lives in examples/ — add it to the path so we can import helpers.
_EXAMPLES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "examples")
sys.path.insert(0, os.path.abspath(_EXAMPLES_DIR))

from poc_taskchampion_undo_interactive_fr import (
    add_task,
    create_initial_tasks,
    delete_task,
    gather_candidates,
    mark_done,
    snapshot_ops_set,
)
from taskchampion import Replica

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mem() -> Replica:
    """Fresh in-memory replica for each test."""
    return Replica.new_in_memory()


@pytest.fixture
def replica_with_tasks(mem: Replica):
    """In-memory replica with 3 default tasks already created."""
    uuids = create_initial_tasks(mem)
    return mem, uuids


# ---------------------------------------------------------------------------
# snapshot_ops_set — must commit an UndoPoint
# ---------------------------------------------------------------------------


class TestSnapshotOpsSet:
    def test_snapshot_increments_undo_points(self, mem: Replica) -> None:
        """snapshot_ops_set must commit an Operation.UndoPoint."""
        create_initial_tasks(mem)
        before = mem.num_undo_points()
        snapshot_ops_set(mem)
        assert mem.num_undo_points() == before + 1

    def test_get_undo_ops_empty_right_after_snapshot(self, mem: Replica) -> None:
        """Immediately after snapshot, no session *mutation* ops are in the undo queue.

        The UndoPoint marker itself may appear but must not be confused with
        task-mutation operations.
        """
        create_initial_tasks(mem)
        snapshot_ops_set(mem)
        undo_ops = mem.get_undo_operations()
        # At most the UndoPoint marker — no task Create/Update/Delete ops
        non_undo_point_ops = [o for o in undo_ops if not o.is_undo_point()]
        assert len(non_undo_point_ops) == 0

    def test_get_undo_ops_only_session_ops_after_snapshot(self, mem: Replica) -> None:
        """After snapshot + one session op, only that op is returned."""
        uuids = create_initial_tasks(mem)
        snapshot_ops_set(mem)
        mark_done(mem, uuids[0])
        undo_ops = mem.get_undo_operations()
        # There must be at least one op — but NOT the 3-task creation ops
        assert len(undo_ops) > 0
        assert len(undo_ops) < 15  # 15 = 3 tasks × 5 ops each (creation baseline)


# ---------------------------------------------------------------------------
# Undo restores tasks — core regression guard
# ---------------------------------------------------------------------------


class TestUndoRestoresTasks:
    def test_undo_mark_done_restores_pending(self, replica_with_tasks) -> None:
        """Undoing mark_done must restore the task to Pending, not erase it."""
        mem, uuids = replica_with_tasks
        snapshot_ops_set(mem)
        mark_done(mem, uuids[0])

        undo_ops = mem.get_undo_operations()
        assert len(undo_ops) > 0

        ok = mem.commit_reversed_operations(undo_ops)
        assert ok is True

        tasks = mem.all_tasks()
        assert uuids[0] in tasks, "Task must still exist after undo — not be erased"
        t = tasks[uuids[0]]
        status = str(t.get_status())
        assert "Pending" in status or "pending" in status.lower()

    def test_delete_task_sets_status_deleted(self, replica_with_tasks) -> None:
        """delete_task must mark the task as Status.Deleted (not silently fail)."""
        mem, uuids = replica_with_tasks
        delete_task(mem, uuids[1])
        t = mem.all_tasks()[uuids[1]]
        status = str(t.get_status())
        assert "Deleted" in status or "deleted" in status.lower()

    def test_undo_delete_restores_task(self, replica_with_tasks) -> None:
        """Undoing delete_task must restore the task to Pending status."""
        mem, uuids = replica_with_tasks
        snapshot_ops_set(mem)
        delete_task(mem, uuids[1])

        undo_ops = mem.get_undo_operations()
        mem.commit_reversed_operations(undo_ops)

        tasks = mem.all_tasks()
        assert uuids[1] in tasks, "Deleted task must be restored after undo"
        status = str(tasks[uuids[1]].get_status())
        assert "Pending" in status or "pending" in status.lower(), (
            "Restored task must be Pending, not still Deleted"
        )

    def test_baseline_tasks_survive_undo(self, replica_with_tasks) -> None:
        """Baseline (pre-snapshot) tasks must all still exist after undoing session ops."""
        mem, uuids = replica_with_tasks
        snapshot_ops_set(mem)

        # Perform several session operations
        mark_done(mem, uuids[0])
        delete_task(mem, uuids[1])
        add_task(mem, desc="session task")

        undo_ops = mem.get_undo_operations()
        ok = mem.commit_reversed_operations(undo_ops)
        assert ok is True

        tasks = mem.all_tasks()
        # All 3 baseline tasks must still be present
        for u in uuids:
            assert u in tasks, f"Baseline task {u[:8]} must survive undo"

    def test_undo_does_not_erase_entire_task_history(self, replica_with_tasks) -> None:
        """The critical regression: without UndoPoint, undo used to wipe all tasks."""
        mem, uuids = replica_with_tasks
        snapshot_ops_set(mem)
        mark_done(mem, uuids[0])

        undo_ops = mem.get_undo_operations()
        mem.commit_reversed_operations(undo_ops)

        # Must have at least the 3 baseline tasks
        assert len(mem.all_tasks()) >= 3


# ---------------------------------------------------------------------------
# gather_candidates — only session ops shown
# ---------------------------------------------------------------------------


class TestGatherCandidates:
    def test_candidates_empty_before_session_ops(self, replica_with_tasks) -> None:
        """Right after snapshot, the global undo candidate has no informative session ops.

        Note: per-task candidates from ``get_task_operations()`` may still surface
        pre-snapshot creation ops; only the 'global' candidate (``get_undo_operations``)
        is anchored by the UndoPoint and is guaranteed to be clean.
        """
        mem, uuids = replica_with_tasks
        baseline = snapshot_ops_set(mem)
        display = gather_candidates(mem, baseline)
        global_candidates = [filtered for typ, _, _, filtered in display if typ == "global"]
        for filtered in global_candidates:
            # The global candidate must have no informative session ops
            # (only the UndoPoint marker, which op_is_informative may pass but is harmless)
            non_undo_point_shown = [(o, s) for o, s in filtered if "UndoPoint" not in s]
            assert len(non_undo_point_shown) == 0

    def test_candidates_show_session_ops_after_mark_done(self, replica_with_tasks) -> None:
        """After mark_done, at least one informative candidate op must appear."""
        mem, uuids = replica_with_tasks
        baseline = snapshot_ops_set(mem)
        mark_done(mem, uuids[0])
        display = gather_candidates(mem, baseline)
        total_shown = sum(len(filtered) for _, _, _, filtered in display)
        assert total_shown > 0
