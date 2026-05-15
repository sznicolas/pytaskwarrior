"""Lightweight Python filter engine for taskchampion Tasks.

Implements a subset of the TaskWarrior filter syntax directly in Python,
applied as a post-query pass over the full task list returned by
``Replica.all_tasks()``.

Supported tokens
----------------
* ``+tag`` / ``-tag``           — include / exclude by user tag
* ``+VIRTUAL`` / ``-VIRTUAL``   — virtual tags (+OVERDUE, +DUE, +TODAY, …)
* ``status:X``                  — exact status match
* ``status.not:X``              — negate status match
* ``project:X``                 — exact or hierarchical prefix match
* ``uuid:X``                    — exact UUID match
* ``priority:X``                — exact priority match (H / M / L / "")
* ``parent:X``                  — exact parent UUID match
* ``+LATEST``                   — keep only the most recently created task
* ``due.before:X``              — date field < resolved date
* ``due.after:X``               — date field > resolved date
* ``due.by:X``                  — date field <= resolved date
* ``scheduled.after:X``         — same pattern for scheduled / wait / until / entry / modified
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from taskchampion import Status, Tag, Task

from ..utils.date_resolver import resolve_date
from ..utils.virtual_tags import TASKWARRIOR_VIRTUAL_TAG_SET

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DATE_FIELDS: frozenset[str] = frozenset(
    {"due", "wait", "scheduled", "until", "entry", "modified"}
)
_DATE_OPS: frozenset[str] = frozenset({"before", "after", "by", "not"})


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def apply_filter(
    tasks: list[Task],
    filter_str: str,
    include_completed: bool = False,
    include_deleted: bool = False,
    now: datetime | None = None,
) -> list[Task]:
    """Return the subset of *tasks* that match *filter_str*.

    Status filtering (include_completed / include_deleted) is applied first,
    then token-based filtering, then ``+LATEST`` selection if present.

    The optional *now* parameter pins the reference time for virtual-tag and
    date-range evaluation (useful in tests).
    """
    if now is None:
        now = datetime.now(UTC)

    result = _apply_status_filter(tasks, include_completed, include_deleted)

    filter_str = filter_str.strip()
    if filter_str:
        tokens = _parse_tokens(filter_str)
        want_latest = _pop_latest(tokens)
        if tokens:
            result = [t for t in result if _task_matches(t, tokens, now)]
        if want_latest:
            result = _keep_latest(result)

    return result


# ---------------------------------------------------------------------------
# Token types
# ---------------------------------------------------------------------------


@dataclass
class _TagToken:
    name: str
    include: bool


@dataclass
class _StatusToken:
    value: str
    negate: bool


@dataclass
class _UUIDToken:
    value: str


@dataclass
class _AttributeToken:
    key: str
    value: str


@dataclass
class _DateRangeToken:
    field: str  # e.g. "due", "scheduled"
    op: str     # "before" | "after" | "by" | "not"
    expr: str   # raw date expression passed to resolve_date()


_Token = _TagToken | _StatusToken | _UUIDToken | _AttributeToken | _DateRangeToken


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def _parse_tokens(filter_str: str) -> list[_Token]:
    tokens: list[_Token] = []
    parts = filter_str.split()
    i = 0
    while i < len(parts):
        part = parts[i]
        upper = part.upper()
        if upper == "+LATEST":
            tokens.append(_TagToken(name="LATEST", include=True))
        elif part.startswith("+"):
            tokens.append(_TagToken(name=part[1:], include=True))
        elif part.startswith("-"):
            tokens.append(_TagToken(name=part[1:], include=False))
        elif part.startswith("status.not:"):
            tokens.append(_StatusToken(value=part[len("status.not:"):], negate=True))
        elif part.startswith("status:"):
            tokens.append(_StatusToken(value=part[len("status:"):], negate=False))
        elif part.startswith("uuid:"):
            tokens.append(_UUIDToken(value=part[len("uuid:"):]))
        elif ":" in part:
            key, _, value = part.partition(":")
            # Detect field.op:expr patterns (date range)
            if "." in key:
                field, _, op = key.partition(".")
                if field in _DATE_FIELDS and op in _DATE_OPS:
                    # Consume a trailing arithmetic operator and operand so that
                    # compound expressions like "due.before:now + P7D" or
                    # "due.after:eom - P1W" are captured as a single expr.
                    expr = value
                    while i + 2 < len(parts) and parts[i + 1] in ("+", "-"):
                        expr += f" {parts[i + 1]} {parts[i + 2]}"
                        i += 2
                    tokens.append(_DateRangeToken(field=field, op=op, expr=expr))
                    i += 1
                    continue
            tokens.append(_AttributeToken(key=key, value=value))
        i += 1
    return tokens


def _pop_latest(tokens: list[_Token]) -> bool:
    """Remove any ``+LATEST`` token and return True if it was present."""
    indices = [
        i
        for i, t in enumerate(tokens)
        if isinstance(t, _TagToken) and t.name.upper() == "LATEST"
    ]
    for i in reversed(indices):
        tokens.pop(i)
    return bool(indices)


# ---------------------------------------------------------------------------
# Status filtering
# ---------------------------------------------------------------------------


def _apply_status_filter(
    tasks: list[Task],
    include_completed: bool,
    include_deleted: bool,
) -> list[Task]:
    result = []
    for task in tasks:
        status = task.get_status()
        if status == Status.Deleted and not include_deleted:
            continue
        if status == Status.Completed and not include_completed:
            continue
        result.append(task)
    return result


def _tc_status_str(task: Task) -> str:
    """Return a TaskWarrior-compatible status string for *task*."""
    status = task.get_status()
    if status == Status.Pending:
        return "waiting" if task.is_waiting() else "pending"
    if status == Status.Completed:
        return "completed"
    if status == Status.Deleted:
        return "deleted"
    if status == Status.Recurring:
        return "recurring"
    return "pending"


# ---------------------------------------------------------------------------
# Date helpers
# ---------------------------------------------------------------------------


def _ensure_utc(dt: datetime) -> datetime:
    """Return *dt* as a UTC-aware datetime; treat naive datetimes as UTC."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def _get_task_date(task: Task, field: str) -> datetime | None:
    """Return the date for *field* as a UTC-aware datetime, or None."""
    if field == "due":
        dt = task.get_due()
        return _ensure_utc(dt) if dt is not None else None
    if field == "wait":
        dt = task.get_wait()
        return _ensure_utc(dt) if dt is not None else None
    if field == "entry":
        dt = task.get_entry()
        return _ensure_utc(dt) if dt is not None else None
    if field == "modified":
        dt = task.get_modified()
        return _ensure_utc(dt) if dt is not None else None
    # scheduled and until are stored as Unix timestamp strings
    raw = task.get_value(field)
    if raw is None:
        return None
    try:
        return datetime.fromtimestamp(int(raw), tz=UTC)
    except (ValueError, OSError):
        return None


def _match_date_range(task: Task, token: _DateRangeToken, now: datetime) -> bool:
    """Return True if the task's date field satisfies the range constraint."""
    task_dt = _get_task_date(task, token.field)
    if task_dt is None:
        # "field.not:X" is vacuously true when field is absent (no date set)
        return token.op == "not"

    threshold = resolve_date(token.expr, now)
    if threshold is None:
        return False  # Unresolvable expression — conservative reject

    if token.op == "before":
        return task_dt < threshold
    if token.op == "after":
        return task_dt > threshold
    if token.op == "by":
        return task_dt <= threshold
    if token.op == "not":
        return task_dt != threshold
    return False


# ---------------------------------------------------------------------------
# Virtual tag computation
# ---------------------------------------------------------------------------


def _compute_virtual_tag(task: Task, name: str, now: datetime) -> bool | None:
    """Return True/False for known virtual tags, None to delegate to task.has_tag()."""
    status = task.get_status()
    is_pending_active = status == Status.Pending and not task.is_waiting()

    if name == "PENDING":
        return is_pending_active
    if name == "COMPLETED":
        return status == Status.Completed
    if name == "DELETED":
        return status == Status.Deleted
    if name == "WAITING":
        return task.is_waiting()
    if name == "ACTIVE":
        return task.is_active()
    if name == "BLOCKED":
        return task.is_blocked()
    if name == "UNBLOCKED":
        return not task.is_blocked()
    if name == "BLOCKING":
        return task.is_blocking()
    if name == "TAGGED":
        return any(tag.is_user() for tag in task.get_tags())
    if name == "ANNOTATED":
        return bool(task.get_annotations())
    if name == "PRIORITY":
        p = task.get_priority()
        return p is not None and p != ""
    if name == "PROJECT":
        return bool(task.get_value("project"))
    if name == "PARENT":
        return bool(task.get_value("recur"))
    if name == "CHILD":
        return bool(task.get_value("parent"))
    if name == "UNTIL":
        return task.get_value("until") is not None
    if name == "SCHEDULED":
        return task.get_value("scheduled") is not None
    if name == "UDA":
        return bool(list(task.get_udas()))

    # --- Date-based virtual tags ---
    due = _get_task_date(task, "due")
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start.replace(hour=23, minute=59, second=59, microsecond=999999)

    if name == "OVERDUE":
        return due is not None and due < now and (is_pending_active or task.is_waiting())
    if name == "DUE":
        return due is not None and due <= now + timedelta(days=7)
    if name == "DUETODAY":
        return due is not None and today_start <= due <= today_end
    if name == "TODAY":
        sched = _get_task_date(task, "scheduled")
        return (
            (due is not None and today_start <= due <= today_end)
            or (sched is not None and today_start <= sched <= today_end)
        )
    if name == "TOMORROW":
        tom_start = today_start + timedelta(days=1)
        tom_end = today_end + timedelta(days=1)
        return due is not None and tom_start <= due <= tom_end
    if name == "YESTERDAY":
        yes_start = today_start - timedelta(days=1)
        yes_end = today_end - timedelta(days=1)
        return due is not None and yes_start <= due <= yes_end
    if name == "WEEK":
        return due is not None and due <= today_start + timedelta(days=7)
    if name == "MONTH":
        if today_start.month == 12:
            month_end = today_start.replace(year=today_start.year + 1, month=1, day=1)
        else:
            month_end = today_start.replace(month=today_start.month + 1, day=1)
        return due is not None and due < month_end
    if name == "QUARTER":
        q_end_month = ((today_start.month - 1) // 3 + 1) * 3 + 1
        if q_end_month > 12:
            q_end = today_start.replace(year=today_start.year + 1, month=1, day=1)
        else:
            q_end = today_start.replace(month=q_end_month, day=1)
        return due is not None and due < q_end
    if name == "YEAR":
        year_end = today_start.replace(year=today_start.year + 1, month=1, day=1)
        return due is not None and due < year_end
    if name == "READY":
        sched = _get_task_date(task, "scheduled")
        return (
            is_pending_active
            and not task.is_blocked()
            and (sched is None or sched <= now)
        )

    return None  # Unknown virtual tag — delegate to task.has_tag()


# ---------------------------------------------------------------------------
# Token matching
# ---------------------------------------------------------------------------


def _task_matches(task: Task, tokens: list[_Token], now: datetime) -> bool:
    for token in tokens:
        if isinstance(token, _TagToken):
            name_upper = token.name.upper()
            if name_upper in TASKWARRIOR_VIRTUAL_TAG_SET and name_upper != "LATEST":
                computed = _compute_virtual_tag(task, name_upper, now)
                if computed is not None:
                    if token.include and not computed:
                        return False
                    if not token.include and computed:
                        return False
                    continue
            has = task.has_tag(Tag(token.name))
            if token.include and not has:
                return False
            if not token.include and has:
                return False

        elif isinstance(token, _StatusToken):
            matches = _tc_status_str(task) == token.value.lower()
            if token.negate and matches:
                return False
            if not token.negate and not matches:
                return False

        elif isinstance(token, _UUIDToken):
            if task.get_uuid() != token.value:
                return False

        elif isinstance(token, _DateRangeToken):
            if not _match_date_range(task, token, now):
                return False

        elif isinstance(token, _AttributeToken):
            if not _match_attribute(task, token):
                return False

    return True


def _match_attribute(task: Task, token: _AttributeToken) -> bool:
    key, value = token.key, token.value

    if key == "priority":
        return task.get_priority() == value

    raw = task.get_value(key)
    if raw is None:
        return False

    if key == "project":
        # Hierarchical prefix match: "work" matches "work" and "work.reports"
        return raw == value or raw.startswith(value + ".")

    return raw == value


# ---------------------------------------------------------------------------
# +LATEST helper
# ---------------------------------------------------------------------------


def _keep_latest(tasks: list[Task]) -> list[Task]:
    """Return a list containing only the most recently created task."""
    if not tasks:
        return []

    def _entry_ts(t: Task) -> float:
        entry = t.get_entry()
        return entry.timestamp() if entry is not None else 0.0

    return [max(tasks, key=_entry_ts)]
