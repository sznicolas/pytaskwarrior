"""Data Transfer Object for TaskWarrior contexts.

Contexts are named filters that can be applied globally to focus
on a subset of tasks.
"""

from __future__ import annotations

from pydantic import BaseModel


class ContextDTO(BaseModel):
    """Data Transfer Object for task contexts.

    Contexts allow you to define named filters that can be applied
    globally. When a context is active, all task queries are automatically
    filtered by the context's filter expression.

    Attributes:
        name: The unique name of the context.
        filter: The TaskWarrior filter expression for this context.
        active: Whether this context is currently active.

    Example:
        List and inspect contexts::

            contexts = tw.get_contexts()
            for ctx in contexts:
                print(f"{ctx.name}: {ctx.filter}")
    """

    name: str
    filter: str | None = None
    active: bool = False
