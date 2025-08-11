from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .base import User as User  # SQLAlchemy model


@dataclass
class Feature:
    name: str
    enabled: bool = True
    description: Optional[str] = None


__all__ = ["User", "Feature"]