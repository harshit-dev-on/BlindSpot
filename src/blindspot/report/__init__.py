"""Reporting module for BlindSpot.

Provides UX report writers, SARIF generation, and heuristic analyzers.
"""

from blindspot.reporting import (
    AIUXAnalyzer,
    BlindSpotReport,
    DeduplicatorAndPrioritizer,
    EvidenceAggregator,
    FindingCategory,
    SeverityLevel,
    TaskMetricSummary,
    UXFinding,
    generate_ux_report,
    render_html_report,
)
from blindspot.reporting.sarif import build_sarif_report, write_sarif_file

FindingItem = UXFinding
generate_sarif_log = build_sarif_report

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
