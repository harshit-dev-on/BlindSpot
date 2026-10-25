"""Reporting module for BlindSpot.

Provides UX report writers, SARIF generation, and heuristic analyzers.
"""

from blindspot.report.analysis import (
    AIUXAnalyzer,
    DeduplicatorAndPrioritizer,
    EvidenceAggregator,
)
from blindspot.report.models import (
    BlindSpotReport,
    FindingCategory,
    FindingItem,
    SeverityLevel,
    TaskMetricSummary,
    UXFinding,
)
from blindspot.report.sarif import build_sarif_report, generate_sarif_log, write_sarif_file
from blindspot.report.writer import generate_ux_report, render_html_report

__all__ = [
    "AIUXAnalyzer",
    "BlindSpotReport",
    "DeduplicatorAndPrioritizer",
    "EvidenceAggregator",
    "FindingCategory",
    "FindingItem",
    "SeverityLevel",
    "TaskMetricSummary",
    "UXFinding",
    "build_sarif_report",
    "generate_sarif_log",
    "generate_ux_report",
    "render_html_report",
    "write_sarif_file",
]
