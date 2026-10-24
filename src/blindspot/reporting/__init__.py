"""BlindSpot UX reporting, evidence aggregation, prioritization, and JSON/HTML export."""

from blindspot.reporting.analysis import (
    AIUXAnalyzer,
    DeduplicatorAndPrioritizer,
    EvidenceAggregator,
)
from blindspot.reporting.generator import generate_ux_report
from blindspot.reporting.html_renderer import render_html_report
from blindspot.reporting.models import (
    BlindSpotReport,
    FindingCategory,
    SeverityLevel,
    TaskMetricSummary,
    UXFinding,
)
from blindspot.reporting.sarif import build_sarif_report, write_sarif_file

__all__ = [
    "BlindSpotReport",
    "FindingCategory",
    "SeverityLevel",
    "TaskMetricSummary",
    "UXFinding",
    "EvidenceAggregator",
    "AIUXAnalyzer",
    "DeduplicatorAndPrioritizer",
    "render_html_report",
    "generate_ux_report",
    "build_sarif_report",
    "write_sarif_file",
]

