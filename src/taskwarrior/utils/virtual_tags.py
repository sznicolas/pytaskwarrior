"""Known TaskWarrior virtual tag names.

Virtual tags are synthetic tags computed from task state at query time.
They are never stored in the task data and cannot be set directly.
"""

TASKWARRIOR_VIRTUAL_TAGS: tuple[str, ...] = (
    "BLOCKED",
    "UNBLOCKED",
    "BLOCKING",
    "DUE",
    "DUETODAY",
    "TODAY",
    "OVERDUE",
    "WEEK",
    "MONTH",
    "QUARTER",
    "YEAR",
    "ACTIVE",
    "SCHEDULED",
    "PARENT",
    "CHILD",
    "UNTIL",
    "WAITING",
    "ANNOTATED",
    "READY",
    "YESTERDAY",
    "TOMORROW",
    "TAGGED",
    "PENDING",
    "COMPLETED",
    "DELETED",
    "UDA",
    "ORPHAN",
    "PRIORITY",
    "PROJECT",
    "LATEST",
)

TASKWARRIOR_VIRTUAL_TAG_SET: frozenset[str] = frozenset(TASKWARRIOR_VIRTUAL_TAGS)
