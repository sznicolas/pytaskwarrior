"""DTO ↔ taskchampion conversion layer (Eval 1, taskchampion-py 2.0.2).

Converts between pytaskwarrior's Pydantic DTOs and the taskchampion-py
Task / Operations API. All date fields are handled as UTC datetimes; TW
date expressions (``"tomorrow"``, ``"eom"``, …) cannot be resolved here
and are silently skipped with a warning.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import UUID

from taskchampion import Annotation, Operations, Status, Tag, Task, WorkingSet

from ..dto.annotation_dto import AnnotationDTO
from ..dto.task_dto import TaskInputDTO, TaskOutputDTO
from ..enums import Priority, RecurrencePeriod, TaskStatus
from ..utils.date_resolver import resolve_date

logger = logging.getLogger(__name__)

# Properties stored as raw key-value pairs in taskchampion that correspond to
# known TaskWarrior fields.  They must be excluded from the UDA dict when
# building a TaskOutputDTO to avoid duplicates.
_TC_KNOWN_GENERIC_PROPS: frozenset[str] = frozenset(
    {
        "project",
        "recur",
        "scheduled",
        "until",
        "start",
        "end",
        "parent",
        "imask",
        "rtype",
    }
)

def _tc_to_tw_status(tc_status: object, is_waiting: bool) -> TaskStatus:
    """Map a taskchampion Status value to a TaskStatus enum member."""
    if is_waiting:
        return TaskStatus.WAITING
    if tc_status == Status.Completed:
        return TaskStatus.COMPLETED
    if tc_status == Status.Deleted:
        return TaskStatus.DELETED
    if tc_status == Status.Recurring:
        return TaskStatus.RECURRING
    return TaskStatus.PENDING


def _tw_to_tc_status(tw_status: str) -> object:
    """Map a TaskStatus string value to a taskchampion Status object.

    WAITING maps to ``Status.Pending`` (wait date is set separately).
    """
    if tw_status in (TaskStatus.COMPLETED, TaskStatus.COMPLETED.value):
        return Status.Completed
    if tw_status in (TaskStatus.DELETED, TaskStatus.DELETED.value):
        return Status.Deleted
    if tw_status in (TaskStatus.RECURRING, TaskStatus.RECURRING.value):
        return Status.Recurring
    return Status.Pending

_PRIORITY_TC_TO_TW: dict[str, Priority | None] = {
    "": None,
    "H": Priority.HIGH,
    "M": Priority.MEDIUM,
    "L": Priority.LOW,
}


# ---------------------------------------------------------------------------
# Date helpers
# ---------------------------------------------------------------------------


def _ts_to_dt(ts: str | int | None) -> datetime | None:
    """Convert a Unix timestamp string or int to a UTC-aware datetime."""
    if ts is None:
        return None
    try:
        return datetime.fromtimestamp(int(ts), tz=UTC)
    except (ValueError, OSError):
        logger.debug("_ts_to_dt: cannot convert %r to datetime", ts)
        return None


def _dt_to_ts(dt: datetime | None) -> str | None:
    """Convert a datetime to a Unix timestamp string (for ``set_value``)."""
    if dt is None:
        return None
    return str(int(dt.timestamp()))


def _parse_input_date(date_str: str | None) -> datetime | None:
    """Parse a date string coming from a TaskInputDTO field.

    Supports ISO 8601 strings directly and the most common TaskWarrior date
    expressions (``"today"``, ``"tomorrow"``, ``"eom"``, ``"now+2w"``, …) via
    :func:`~taskwarrior.utils.date_resolver.resolve_date`.

    Compound TW arithmetic (``"today + 2weeks"``) and natural-language
    expressions (``"next friday"``) cannot be resolved and are logged at
    WARNING level and skipped.
    """
    if date_str is None:
        return None
    result = resolve_date(date_str)
    if result is not None:
        return result
    logger.warning(
        "TaskChampionAdapter: cannot resolve date expression %r — "
        "field will be skipped. "
        "Supported: ISO 8601, today/tomorrow/yesterday, eod/eow/eom/eoy, "
        "now+Nd/Nw/Nh/Nm, P2W/P3D/P1M/P1Y, weekday names.",
        date_str,
    )
    return None


# ---------------------------------------------------------------------------
# Task → TaskOutputDTO
# ---------------------------------------------------------------------------


def tc_task_to_output_dto(task: Task, working_set: WorkingSet) -> TaskOutputDTO:
    """Convert a taskchampion :class:`Task` to a :class:`TaskOutputDTO`."""
    uuid_str = task.get_uuid()

    # Status — waiting = Pending + future wait date
    tc_status = task.get_status()
    tw_status = _tc_to_tw_status(tc_status, task.is_waiting())

    # Working-set index (0 for tasks not in the working set)
    index = working_set.by_uuid(uuid_str) or 0

    # Priority
    raw_prio = task.get_priority()
    priority = _PRIORITY_TC_TO_TW.get(raw_prio)

    # Recurrence (raw string → enum, non-standard values become None)
    recur_raw = task.get_value("recur")
    recur: RecurrencePeriod | None = None
    if recur_raw:
        try:
            recur = RecurrencePeriod(recur_raw)
        except ValueError:
            logger.debug("Non-standard recur value %r — mapping to None", recur_raw)

    # Generic properties stored as raw key-value pairs
    parent_str = task.get_value("parent")

    # UDAs: exclude known generic fields to avoid duplicates
    udas: dict[str, object] = {}
    for (ns, key), val in task.get_udas():
        full_key = f"{ns}.{key}" if ns else key
        if full_key not in _TC_KNOWN_GENERIC_PROPS:
            udas[full_key] = val

    # User tags only (filter synthetic tags like PENDING, ACTIVE, …)
    tags = [str(t) for t in task.get_tags() if t.is_user()]

    # Annotations
    annotations = [
        AnnotationDTO(entry=ann.entry, description=ann.description)
        for ann in task.get_annotations()
    ]

    # Dependencies
    depends = [UUID(dep) for dep in task.get_dependencies()]

    return TaskOutputDTO.model_validate(
        {
            "id": index,
            "uuid": UUID(uuid_str),
            "description": task.get_description(),
            "status": tw_status.value,
            "priority": priority.value if priority else None,
            "entry": task.get_entry(),
            "modified": task.get_modified(),
            "due": task.get_due(),
            "wait": task.get_wait(),
            "start": _ts_to_dt(task.get_value("start")),
            "end": _ts_to_dt(task.get_value("end")),
            "scheduled": _ts_to_dt(task.get_value("scheduled")),
            "until": _ts_to_dt(task.get_value("until")),
            "recur": recur.value if recur else None,
            "project": task.get_value("project"),
            "parent": UUID(parent_str) if parent_str else None,
            "imask": task.get_value("imask"),
            "rtype": task.get_value("rtype"),
            "tags": tags,
            "annotations": annotations,
            "depends": depends,
            "udas": udas,
            "urgency": None,
        }
    )


# ---------------------------------------------------------------------------
# TaskInputDTO → Operations
# ---------------------------------------------------------------------------


def apply_input_dto_to_task(
    task: Task,
    dto: TaskInputDTO,
    ops: Operations,
) -> None:
    """Apply the fields of a :class:`TaskInputDTO` to a taskchampion *task*.

    Only fields that were explicitly set in the DTO (``exclude_unset=True``)
    are written.  For list-typed fields (``tags``, ``depends``) the current
    task state is diffed against the desired state so that unmentioned items
    are preserved.
    """
    data = dto.model_dump(exclude_unset=True)

    for field, value in data.items():
        match field:
            case "description":
                task.set_description(value, ops)

            case "priority":
                task.set_priority(value if value is not None else "", ops)

            case "due":
                task.set_due(_parse_input_date(value), ops)

            case "wait":
                task.set_wait(_parse_input_date(value), ops)

            case "scheduled":
                task.set_value("scheduled", _dt_to_ts(_parse_input_date(value)), ops)

            case "until":
                task.set_value("until", _dt_to_ts(_parse_input_date(value)), ops)

            case "project":
                task.set_value("project", value, ops)

            case "recur":
                if isinstance(value, RecurrencePeriod):
                    task.set_value("recur", value.value, ops)
                else:
                    task.set_value("recur", value, ops)

            case "parent":
                task.set_value("parent", str(value) if value else None, ops)

            case "tags":
                _sync_tags(task, value, ops)

            case "depends":
                _sync_depends(task, [str(d) for d in value], ops)

            case "annotations":
                _add_annotations(task, value, ops)

            case "udas":
                _apply_udas(task, value, ops)

            case _:
                # uuid / imask / rtype are read-only; skip silently
                pass


# ---------------------------------------------------------------------------
# Tag / dependency / UDA helpers
# ---------------------------------------------------------------------------


def _sync_tags(task: Task, new_tags: list[str], ops: Operations) -> None:
    """Diff and sync user tags."""
    current = {str(t) for t in task.get_tags() if t.is_user()}
    desired = set(new_tags)
    for tag in desired - current:
        task.add_tag(Tag(tag), ops)
    for tag in current - desired:
        task.remove_tag(Tag(tag), ops)


def _sync_depends(task: Task, new_deps: list[str], ops: Operations) -> None:
    """Diff and sync dependencies."""
    current = set(task.get_dependencies())
    desired = set(new_deps)
    for dep in desired - current:
        task.add_dependency(dep, ops)
    for dep in current - desired:
        task.remove_dependency(dep, ops)


def _add_annotations(task: Task, texts: list[str], ops: Operations) -> None:
    """Add each string as a new annotation, ensuring unique timestamps."""
    existing_ts = {int(ann.entry.timestamp()) for ann in task.get_annotations()}
    next_ts = int(datetime.now(tz=UTC).timestamp())
    for text in texts:
        while next_ts in existing_ts:
            next_ts += 1
        existing_ts.add(next_ts)
        entry = datetime.fromtimestamp(next_ts, tz=UTC)
        task.add_annotation(Annotation(entry, text), ops)
        next_ts += 1


def _apply_udas(task: Task, udas: dict[str, object], ops: Operations) -> None:
    """Write UDA values.  Keys containing a dot are treated as ``ns.key``."""
    for key, val in udas.items():
        if val is None:
            continue
        str_val = str(val)
        if "." in key:
            ns, _, k = key.partition(".")
            task.set_uda(ns, k, str_val, ops)
        else:
            task.set_uda("", key, str_val, ops)
