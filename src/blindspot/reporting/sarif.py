"""SARIF 2.1.0 output for BlindSpot accessibility and UX violation reports.

Builds a GitHub Code Scanning compatible SARIF document from BlindSpot findings
so CI pipelines can upload findings via `github/codeql-action/upload-sarif`,
view annotations directly in Pull Request diffs, or ingest into developer dashboards.

Schema: SARIF 2.1.0 (OASIS standard)
Compatible with: GitHub Code Scanning, VS Code SARIF Viewer, GitLab Security
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

SARIF_SCHEMA_URL = "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json"
SARIF_VERSION = "2.1.0"

# Standard WCAG 2.2 rules catalog
WCAG_RULES_CATALOG: Dict[str, Dict[str, Any]] = {
    "WCAG-1.1.1": {
        "name": "NonTextContent",
        "shortDescription": "All non-text content presented to the user has a text alternative (Level A).",
        "helpUri": "https://www.w3.org/WAI/WCAG22/Understanding/non-text-content.html",
        "defaultLevel": "error",
    },
    "WCAG-1.3.1": {
        "name": "InfoAndRelationships",
        "shortDescription": "Information, structure, and relationships conveyed through presentation can be programmatically determined (Level A).",
        "helpUri": "https://www.w3.org/WAI/WCAG22/Understanding/info-and-relationships.html",
        "defaultLevel": "error",
    },
    "WCAG-1.4.3": {
        "name": "ContrastMinimum",
        "shortDescription": "Visual presentation of text and images of text has a contrast ratio of at least 4.5:1 (Level AA).",
        "helpUri": "https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html",
        "defaultLevel": "error",
    },
    "WCAG-1.4.11": {
        "name": "NonTextContrast",
        "shortDescription": "Visual presentation of user interface components and graphical objects has a contrast ratio of at least 3:1 against adjacent colors (Level AA).",
        "helpUri": "https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html",
        "defaultLevel": "warning",
    },
    "WCAG-2.1.1": {
        "name": "KeyboardAccessible",
        "shortDescription": "All functionality of the content is operable through a keyboard interface without requiring specific timings for individual keystrokes (Level A).",
        "helpUri": "https://www.w3.org/WAI/WCAG22/Understanding/keyboard.html",
        "defaultLevel": "error",
    },
    "WCAG-2.1.2": {
        "name": "NoKeyboardTrap",
        "shortDescription": "If keyboard focus can be moved to a component using a keyboard, then focus can be moved away from that component using only a keyboard (Level A).",
        "helpUri": "https://www.w3.org/WAI/WCAG22/Understanding/no-keyboard-trap.html",
        "defaultLevel": "error",
    },
    "WCAG-2.4.3": {
        "name": "FocusOrder",
        "shortDescription": "If a Web page can be navigated sequentially, focusable components receive focus in an order that preserves meaning and operability (Level A).",
        "helpUri": "https://www.w3.org/WAI/WCAG22/Understanding/focus-order.html",
        "defaultLevel": "warning",
    },
    "WCAG-2.4.7": {
        "name": "FocusVisible",
        "shortDescription": "Any keyboard operable user interface has a mode of operation where the keyboard focus indicator is visible (Level AA).",
        "helpUri": "https://www.w3.org/WAI/WCAG22/Understanding/focus-visible.html",
        "defaultLevel": "error",
    },
    "WCAG-2.5.8": {
        "name": "TargetSizeMinimum",
        "shortDescription": "The size of the target for pointer inputs is at least 24 by 24 CSS pixels (WCAG 2.2 Level AA).",
        "helpUri": "https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html",
        "defaultLevel": "warning",
    },
    "WCAG-3.3.1": {
        "name": "ErrorIdentification",
        "shortDescription": "If an input error is automatically detected, the item that is in error is identified and the error is described to the user in text (Level A).",
        "helpUri": "https://www.w3.org/WAI/WCAG22/Understanding/error-identification.html",
        "defaultLevel": "error",
    },
    "WCAG-3.3.2": {
        "name": "LabelsOrInstructions",
        "shortDescription": "Labels or instructions are provided when content requires user input (Level A).",
        "helpUri": "https://www.w3.org/WAI/WCAG22/Understanding/labels-or-instructions.html",
        "defaultLevel": "warning",
    },
    "WCAG-4.1.2": {
        "name": "NameRoleValue",
        "shortDescription": "For all user interface components, the name and role can be programmatically determined (Level A).",
        "helpUri": "https://www.w3.org/WAI/WCAG22/Understanding/name-role-value.html",
        "defaultLevel": "error",
    },
}


def build_sarif_report(
    findings: List[Dict[str, Any]],
    target_url: str = "https://target-website.local",
    tool_version: str = "0.1.0",
) -> Dict[str, Any]:
    """Convert BlindSpot accessibility and usability findings into a standard SARIF 2.1.0 document."""
    rules_used: Dict[str, Dict[str, Any]] = {}
    results: List[Dict[str, Any]] = []

    for item in findings:
        criterion_code = item.get("wcag_criterion") or item.get("code")
        rule_id = f"WCAG-{criterion_code}" if criterion_code else item.get("issue_id", "UX-FRICTION")

        # Map severity to SARIF level
        severity = str(item.get("severity") or item.get("impact", "moderate")).lower()
        level = "error" if severity in ("critical", "serious") else "warning" if severity == "moderate" else "note"

        # Register rule in tool driver rules list
        if rule_id not in rules_used:
            cat = WCAG_RULES_CATALOG.get(rule_id, {})
            rules_used[rule_id] = {
                "id": rule_id,
                "name": cat.get("name", rule_id.replace("-", "_")),
                "shortDescription": {
                    "text": cat.get("shortDescription", item.get("title") or "Accessibility / UX finding"),
                },
                "helpUri": cat.get("helpUri", "https://www.w3.org/WAI/WCAG22/"),
                "defaultConfiguration": {
                    "level": cat.get("defaultLevel", level),
                },
            }

        title = item.get("title") or item.get("failure_summary") or "Accessibility barrier observed"
        description = item.get("description") or item.get("failure_summary") or title
        selector = item.get("element_selector") or item.get("selector") or "body"
        url = item.get("page_url") or target_url

        sarif_result: Dict[str, Any] = {
            "ruleId": rule_id,
            "level": level,
            "message": {
                "text": f"[{rule_id}] {title}\n\nDetails: {description}\nElement: `{selector}`",
            },
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {
                            "uri": url,
                        },
                        "region": {
                            "snippet": {
                                "text": item.get("html_snippet") or f"Selector: {selector}",
                            }
                        },
                    }
                }
            ],
            "properties": {
                "elementSelector": selector,
                "suggestedFix": item.get("suggested_fix") or item.get("remediation_suggestion"),
                "severity": severity,
            },
        }
        results.append(sarif_result)

    return {
        "$schema": SARIF_SCHEMA_URL,
        "version": SARIF_VERSION,
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "BlindSpot",
                        "version": tool_version,
                        "informationUri": "https://github.com/harshit-dev-on/BlindSpot",
                        "rules": list(rules_used.values()),
                    }
                },
                "results": results,
            }
        ],
    }


def write_sarif_file(
    findings: List[Dict[str, Any]],
    output_path: Path,
    target_url: str = "https://target-website.local",
    tool_version: str = "0.1.0",
) -> Path:
    """Generate and write SARIF 2.1.0 output file (e.g. findings.sarif)."""
    sarif_doc = build_sarif_report(
        findings=findings,
        target_url=target_url,
        tool_version=tool_version,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(sarif_doc, f, indent=2)

    return output_path
