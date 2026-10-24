"""Unit tests for SARIF 2.1.0 report generation."""

import json
from pathlib import Path
import pytest
from blindspot.reporting.sarif import build_sarif_report, write_sarif_file, SARIF_SCHEMA_URL, SARIF_VERSION


def test_build_sarif_report_empty():
    doc = build_sarif_report([], target_url="https://example.com")
    assert doc["version"] == SARIF_VERSION
    assert doc["$schema"] == SARIF_SCHEMA_URL
    assert len(doc["runs"]) == 1
    assert doc["runs"][0]["tool"]["driver"]["name"] == "BlindSpot"
    assert doc["runs"][0]["results"] == []


def test_build_sarif_report_with_findings():
    findings = [
        {
            "wcag_criterion": "1.4.3",
            "impact": "serious",
            "title": "Low text contrast on navigation link",
            "description": "Contrast ratio is 2.9:1, failing AA requirement 4.5:1",
            "element_selector": "nav a.nav-link",
            "html_snippet": "<a class='nav-link' href='/about'>About</a>",
            "page_url": "https://example.com/about",
            "suggested_fix": "Increase text color lightness",
        },
        {
            "issue_id": "UX-001",
            "severity": "critical",
            "title": "Broken checkout flow submit button",
            "description": "Button does not provide visual confirmation",
            "element_selector": "#submit-order",
            "page_url": "https://example.com/checkout",
        },
    ]

    doc = build_sarif_report(findings, target_url="https://example.com")
    assert len(doc["runs"][0]["results"]) == 2

    # Check WCAG finding
    r1 = doc["runs"][0]["results"][0]
    assert r1["ruleId"] == "WCAG-1.4.3"
    assert r1["level"] == "error"
    assert "About" in r1["locations"][0]["physicalLocation"]["region"]["snippet"]["text"]
    assert r1["properties"]["elementSelector"] == "nav a.nav-link"

    # Check UX finding
    r2 = doc["runs"][0]["results"][1]
    assert r2["ruleId"] == "UX-001"
    assert r2["level"] == "error"


def test_write_sarif_file(tmp_path: Path):
    findings = [
        {
            "wcag_criterion": "2.5.8",
            "impact": "moderate",
            "title": "Touch target too small (18x18px)",
            "element_selector": "button.icon-close",
            "page_url": "https://example.com",
        }
    ]

    out_file = tmp_path / "findings.sarif"
    written = write_sarif_file(findings, out_file)
    assert written == out_file
    assert out_file.is_file()

    with open(out_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["version"] == "2.1.0"
    assert data["runs"][0]["results"][0]["ruleId"] == "WCAG-2.5.8"
    assert data["runs"][0]["results"][0]["level"] == "warning"
