"""Data Transfer Object for TaskWarrior contexts.

Contexts are named filters that can be applied globally to focus
on a subset of tasks. Each context has separate read and write filters.
"""

from __future__ import annotations

from pydantic import BaseModel


class ContextDTO(BaseModel):
    """Data Transfer Object for task contexts.

    Contexts allow you to define named filters that can be applied
    globally. When a context is active, all task queries are automatically
    filtered by the context's read_filter, and new tasks inherit the
    write_filter constraints.

    Attributes:
        name: The unique name of the context.
        read_filter: TaskWarrior filter applied when reading/listing tasks.
        write_filter: TaskWarrior filter applied when creating/modifying tasks.
        active: Whether this context is currently active.

    Example:
        List and inspect contexts::

            contexts = tw.get_contexts()
            for ctx in contexts:
                print(f"{ctx.name}: read={ctx.read_filter} write={ctx.write_filter}")
    """

    name: str
    read_filter: str = ""
    write_filter: str = ""
    active: bool = False
