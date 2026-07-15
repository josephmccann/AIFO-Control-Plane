"""Stable diagnostics shared by Engineering Operating System policies."""

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass(frozen=True)
class Violation:
    """A deterministic, machine-readable contract violation."""

    code: str
    message: str
    path: str = "$"
    details: Dict[str, Any] = field(default_factory=dict)


class EngineeringOSError(ValueError):
    """Base class for invalid Engineering Operating System input."""
