from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class ContextDTO(BaseModel):
    """Data Transfer Object for task contexts."""
    
    name: str
    filter: Optional[str] = None
