"""Core data models for BlindSpot."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class InspectConfig:
    """Configuration for a website inspection session."""

    url: str
    context: str


@dataclass(frozen=True)
class ValidationResult:
    """Result of validating an input field."""

    is_valid: bool
    error_message: Optional[str] = None
    suggestion: Optional[str] = None
