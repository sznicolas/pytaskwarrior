from __future__ import annotations
from pydantic import BaseModel


class ContextDTO(BaseModel):
    """Data Transfer Object for task contexts."""
    
    name: str
    filter: str | None = None
    active: bool = False
