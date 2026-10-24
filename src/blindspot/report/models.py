"""Report data models (re-exported from blindspot.reporting.models)."""

from blindspot.reporting.models import (
    BlindSpotReport,
    FindingCategory,
    SeverityLevel,
    TaskMetricSummary,
    UXFinding,
)

# Alias for generic naming
FindingItem = UXFinding

__all__ = [
    "BlindSpotReport",
    "FindingCategory",
    "FindingItem",
    "SeverityLevel",
    "TaskMetricSummary",
    "UXFinding",
]
