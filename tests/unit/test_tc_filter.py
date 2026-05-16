"""Tests for tc_filter.py — date-range expressions and virtual tags.

Uses TaskChampionAdapter(in-memory) + apply_filter(now=...) for isolated,
deterministic tests without any filesystem or subprocess dependency.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from taskwarrior.adapters.taskchampion_adapter import TaskChampionAdapter
from taskwarrior.adapters.tc_filter import _DateRangeToken, _parse_tokens, apply_filter
from taskwarrior.dto.task_dto import TaskInputDTO

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

NOW = datetime(2026, 6, 10, 12, 0, 0, tzinfo=UTC)  # Wednesday


def _adapter():
    return TaskChampionAdapter()


def _tasks(adapter):
    return list(adapter._replica.all_tasks().values())


def _desc(task_list):
    return sorted(t.get_description() for t in task_list)


# ---------------------------------------------------------------------------
# Parsing: _parse_tokens recognises date-range expressions
# ---------------------------------------------------------------------------

class TestDateRangeParsing:
    def test_before_parsed(self):
        tokens = _parse_tokens("due.before:2026-01-01")
        assert len(tokens) == 1
        t = tokens[0]
        assert isinstance(t, _DateRangeToken)
        assert t.field == "due"
        assert t.op == "before"
        assert t.expr == "2026-01-01"

    def test_after_parsed(self):
        tokens = _parse_tokens("scheduled.after:tomorrow")
        assert len(tokens) == 1
        t = tokens[0]
        assert isinstance(t, _DateRangeToken)
        assert t.field == "scheduled"
        assert t.op == "after"
        assert t.expr == "tomorrow"

    def test_by_parsed(self):
        tokens = _parse_tokens("due.by:eom")
        t = tokens[0]
        assert isinstance(t, _DateRangeToken)
        assert t.op == "by"

    def test_compound_space_operator_consumed(self):
        """'due.before:now + P7D' — the '+ P7D' must be part of the expr."""
        tokens = _parse_tokens("due.before:now + P7D")
        assert len(tokens) == 1
        t = tokens[0]
        assert isinstance(t, _DateRangeToken)
        assert t.field == "due"
        assert t.op == "before"
        assert t.expr == "now + P7D"

    def test_compound_minus_operator_consumed(self):
        """'due.after:eom - P1W' — the '- P1W' must be part of the expr."""
        tokens = _parse_tokens("due.after:eom - P1W")
        assert len(tokens) == 1
        t = tokens[0]
        assert isinstance(t, _DateRangeToken)
        assert t.expr == "eom - P1W"

    def test_compound_with_following_token(self):
        """Compound date expr followed by another filter token."""
        from taskwarrior.adapters.tc_filter import _AttributeToken
        tokens = _parse_tokens("due.before:now + P7D priority:H")
        assert len(tokens) == 2
        assert isinstance(tokens[0], _DateRangeToken)
        assert tokens[0].expr == "now + P7D"
        assert isinstance(tokens[1], _AttributeToken)
        assert tokens[1].key == "priority"

    def test_tag_after_date_expr_not_consumed(self):
        """+OVERDUE after a date expr is NOT consumed as arithmetic."""
        from taskwarrior.adapters.tc_filter import _TagToken
        tokens = _parse_tokens("due.before:tomorrow +OVERDUE")
        assert len(tokens) == 2
        assert isinstance(tokens[0], _DateRangeToken)
        assert tokens[0].expr == "tomorrow"
        assert isinstance(tokens[1], _TagToken)
        assert tokens[1].name == "OVERDUE"

    def test_unknown_field_dot_op_falls_back_to_attribute(self):
        """Fields not in _DATE_FIELDS should not become _DateRangeToken."""
        tokens = _parse_tokens("description.has:foo")
        # Falls through to _AttributeToken with key="description.has"
        from taskwarrior.adapters.tc_filter import _AttributeToken
        assert isinstance(tokens[0], _AttributeToken)


# ---------------------------------------------------------------------------
# Feature 2: Date-range filter expressions
# ---------------------------------------------------------------------------

class TestDateRangeFilters:
    def setup_method(self):
        self.ad = _adapter()
        past = NOW - timedelta(days=5)
        near = NOW + timedelta(days=3)
        far = NOW + timedelta(days=30)
        self.ad.add_task(TaskInputDTO(description="past", due=past.isoformat()))
        self.ad.add_task(TaskInputDTO(description="near", due=near.isoformat()))
        self.ad.add_task(TaskInputDTO(description="far", due=far.isoformat()))
        self.ad.add_task(TaskInputDTO(description="nodule"))  # no due

    def _run(self, filter_str):
        return _desc(apply_filter(_tasks(self.ad), filter_str, now=NOW))

    def test_due_before_filters_past(self):
        result = self._run("due.before:today")
        assert "past" in result
        assert "near" not in result
        assert "nodule" not in result

    def test_due_after_filters_future(self):
        result = self._run(f"due.after:{NOW.isoformat()}")
        assert "near" in result
        assert "far" in result
        assert "past" not in result
        assert "nodule" not in result

    def test_due_by_includes_threshold(self):
        # 3 days from now; "near" is exactly 3 days out — should be included
        threshold = NOW + timedelta(days=3)
        result = self._run(f"due.by:{threshold.isoformat()}")
        assert "near" in result
        assert "past" in result
        assert "far" not in result

    def test_no_due_excluded_by_before_filter(self):
        result = self._run("due.before:2100-01-01")
        assert "nodule" not in result

    def test_no_due_included_by_not_filter(self):
        result = self._run("due.not:2100-01-01")
        assert "nodule" in result


# ---------------------------------------------------------------------------
# Feature 3: Virtual tags
# ---------------------------------------------------------------------------

class TestVirtualTagOVERDUE:
    def test_overdue_task_matches(self):
        ad = _adapter()
        past = NOW - timedelta(days=2)
        ad.add_task(TaskInputDTO(description="late", due=past.isoformat()))
        ad.add_task(TaskInputDTO(description="fine"))
        result = _desc(apply_filter(_tasks(ad), "+OVERDUE", now=NOW))
        assert result == ["late"]

    def test_not_overdue_excludes(self):
        ad = _adapter()
        future = NOW + timedelta(days=5)
        ad.add_task(TaskInputDTO(description="ok", due=future.isoformat()))
        result = apply_filter(_tasks(ad), "+OVERDUE", now=NOW)
        assert result == []

    def test_negate_overdue(self):
        ad = _adapter()
        past = NOW - timedelta(days=1)
        ad.add_task(TaskInputDTO(description="late", due=past.isoformat()))
        ad.add_task(TaskInputDTO(description="fine"))
        result = _desc(apply_filter(_tasks(ad), "-OVERDUE", now=NOW))
        assert "fine" in result
        assert "late" not in result


class TestVirtualTagDUE:
    def test_due_within_7_days(self):
        ad = _adapter()
        near = NOW + timedelta(days=5)
        far = NOW + timedelta(days=10)
        ad.add_task(TaskInputDTO(description="near", due=near.isoformat()))
        ad.add_task(TaskInputDTO(description="far", due=far.isoformat()))
        result = _desc(apply_filter(_tasks(ad), "+DUE", now=NOW))
        assert "near" in result
        assert "far" not in result

    def test_overdue_also_matches_due(self):
        ad = _adapter()
        past = NOW - timedelta(days=1)
        ad.add_task(TaskInputDTO(description="late", due=past.isoformat()))
        result = apply_filter(_tasks(ad), "+DUE", now=NOW)
        assert len(result) == 1


class TestVirtualTagTODAY:
    def test_due_today_matches(self):
        ad = _adapter()
        today_noon = NOW.replace(hour=14)
        ad.add_task(TaskInputDTO(description="today", due=today_noon.isoformat()))
        ad.add_task(TaskInputDTO(description="tomorrow", due=(NOW + timedelta(days=1)).isoformat()))
        result = _desc(apply_filter(_tasks(ad), "+TODAY", now=NOW))
        assert "today" in result
        assert "tomorrow" not in result


class TestVirtualTagWEEK:
    def test_due_within_7_days(self):
        ad = _adapter()
        in_week = NOW + timedelta(days=6)
        out_week = NOW + timedelta(days=8)
        ad.add_task(TaskInputDTO(description="soon", due=in_week.isoformat()))
        ad.add_task(TaskInputDTO(description="later", due=out_week.isoformat()))
        result = _desc(apply_filter(_tasks(ad), "+WEEK", now=NOW))
        assert "soon" in result
        assert "later" not in result


class TestVirtualTagSCHEDULED:
    def test_scheduled_tag_requires_scheduled_date(self):
        ad = _adapter()
        sched = NOW + timedelta(days=1)
        ad.add_task(TaskInputDTO(description="sched", scheduled=sched.isoformat()))
        ad.add_task(TaskInputDTO(description="plain"))
        result = _desc(apply_filter(_tasks(ad), "+SCHEDULED", now=NOW))
        assert "sched" in result
        assert "plain" not in result


class TestVirtualTagBLOCKED:
    def test_blocked_task_matches(self):
        ad = _adapter()
        dto_a = ad.add_task(TaskInputDTO(description="blocker"))
        ad.add_task(TaskInputDTO(description="blocked", depends=[str(dto_a.uuid)]))
        result = _desc(apply_filter(_tasks(ad), "+BLOCKED", now=NOW))
        assert "blocked" in result
        assert "blocker" not in result

    def test_unblocked_tag(self):
        ad = _adapter()
        dto_a = ad.add_task(TaskInputDTO(description="blocker"))
        ad.add_task(TaskInputDTO(description="blocked", depends=[str(dto_a.uuid)]))
        result = _desc(apply_filter(_tasks(ad), "+UNBLOCKED", now=NOW))
        assert "blocker" in result
        assert "blocked" not in result


class TestVirtualTagREADY:
    def test_pending_not_blocked_no_scheduled_is_ready(self):
        ad = _adapter()
        ad.add_task(TaskInputDTO(description="ready"))
        result = _desc(apply_filter(_tasks(ad), "+READY", now=NOW))
        assert "ready" in result

    def test_blocked_is_not_ready(self):
        ad = _adapter()
        dto_a = ad.add_task(TaskInputDTO(description="blocker"))
        ad.add_task(TaskInputDTO(description="blocked", depends=[str(dto_a.uuid)]))
        result = _desc(apply_filter(_tasks(ad), "+READY", now=NOW))
        assert "blocked" not in result
        assert "blocker" in result

    def test_scheduled_in_future_not_ready(self):
        ad = _adapter()
        future_sched = NOW + timedelta(days=5)
        ad.add_task(TaskInputDTO(description="notyet", scheduled=future_sched.isoformat()))
        result = _desc(apply_filter(_tasks(ad), "+READY", now=NOW))
        assert "notyet" not in result


class TestVirtualTagPROJECT:
    def test_task_with_project_matches(self):
        ad = _adapter()
        ad.add_task(TaskInputDTO(description="proj", project="work"))
        ad.add_task(TaskInputDTO(description="noproj"))
        result = _desc(apply_filter(_tasks(ad), "+PROJECT", now=NOW))
        assert "proj" in result
        assert "noproj" not in result


class TestVirtualTagPENDING:
    def test_pending_matches(self):
        ad = _adapter()
        ad.add_task(TaskInputDTO(description="pending"))
        result = apply_filter(_tasks(ad), "+PENDING", now=NOW)
        assert len(result) == 1

    def test_completed_excluded(self):
        ad = _adapter()
        dto = ad.add_task(TaskInputDTO(description="task"))
        ad.done_task(dto.uuid)
        result = apply_filter(_tasks(ad), "+PENDING", include_completed=True, now=NOW)
        assert result == []


class TestVirtualTagTAGGED:
    def test_tagged_task_matches(self):
        ad = _adapter()
        ad.add_task(TaskInputDTO(description="tagged", tags=["urgent"]))
        ad.add_task(TaskInputDTO(description="plain"))
        result = _desc(apply_filter(_tasks(ad), "+TAGGED", now=NOW))
        assert "tagged" in result
        assert "plain" not in result


class TestVirtualTagPRIORITY:
    def test_task_with_priority_matches(self):
        ad = _adapter()
        ad.add_task(TaskInputDTO(description="high", priority="H"))
        ad.add_task(TaskInputDTO(description="none"))
        result = _desc(apply_filter(_tasks(ad), "+PRIORITY", now=NOW))
        assert "high" in result
        assert "none" not in result


# ---------------------------------------------------------------------------
# Combined filter: date range + virtual tag
# ---------------------------------------------------------------------------

class TestCombinedFilters:
    def test_overdue_and_project(self):
        ad = _adapter()
        past = NOW - timedelta(days=1)
        ad.add_task(TaskInputDTO(description="late+work", due=past.isoformat(), project="work"))
        ad.add_task(TaskInputDTO(description="late+noproject", due=past.isoformat()))
        ad.add_task(TaskInputDTO(description="ok+work", project="work"))
        result = _desc(apply_filter(_tasks(ad), "+OVERDUE project:work", now=NOW))
        assert result == ["late+work"]

    def test_due_before_and_priority(self):
        ad = _adapter()
        past = NOW - timedelta(days=1)
        ad.add_task(TaskInputDTO(description="late+H", due=past.isoformat(), priority="H"))
        ad.add_task(TaskInputDTO(description="late+L", due=past.isoformat(), priority="L"))
        result = _desc(apply_filter(_tasks(ad), "due.before:today priority:H", now=NOW))
        assert result == ["late+H"]


class TestVirtualTagUDA:
    def test_task_with_uda_matches_plus_uda(self):
        ad = _adapter()
        ad.add_task(TaskInputDTO(description="with-uda", udas={"severity": "high"}))
        ad.add_task(TaskInputDTO(description="no-uda"))
        result = _desc(apply_filter(_tasks(ad), "+UDA", now=NOW))
        assert "with-uda" in result
        assert "no-uda" not in result

    def test_task_without_uda_matches_minus_uda(self):
        ad = _adapter()
        ad.add_task(TaskInputDTO(description="with-uda", udas={"severity": "low"}))
        ad.add_task(TaskInputDTO(description="no-uda"))
        result = _desc(apply_filter(_tasks(ad), "-UDA", now=NOW))
        assert "no-uda" in result
        assert "with-uda" not in result
