"""SARIF report exporter (re-exported from blindspot.reporting.sarif)."""

from blindspot.reporting.sarif import build_sarif_report, write_sarif_file

generate_sarif_log = build_sarif_report

__all__ = ["build_sarif_report", "generate_sarif_log", "write_sarif_file"]
