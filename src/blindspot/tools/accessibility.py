"""Record Accessibility Barrier Tool for logging WCAG 2.2 violations."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from blindspot.tools.base import BaseTool, ToolResult


# Core WCAG 2.2 AA Criteria commonly evaluated in web testing
COMMON_WCAG_CRITERIA = {
    "1.1.1": "Non-text Content (A)",
    "1.3.1": "Info and Relationships (A)",
    "1.4.3": "Contrast (Minimum) (AA)",
    "1.4.11": "Non-text Contrast (AA)",
    "2.1.1": "Keyboard (A)",
    "2.1.2": "No Keyboard Trap (A)",
    "2.4.3": "Focus Order (A)",
    "2.4.7": "Focus Visible (AA)",
    "2.5.3": "Label in Name (A)",
    "2.5.8": "Target Size (Minimum) (AA)",  # Key WCAG 2.2 criteria
    "3.3.1": "Error Identification (A)",
    "3.3.2": "Labels or Instructions (A)",
    "4.1.2": "Name, Role, Value (A)",
}


@dataclass
class AccessibilityBarrierRecord:
    """Record of a verified accessibility barrier violating WCAG 2.2 Level AA."""

    barrier_id: str
    wcag_criterion: str
    criterion_name: str
    impact: str  # "critical", "serious", "moderate", "minor"
    element_selector: str
    html_snippet: Optional[str] = None
    failure_summary: str = ""
    suggested_fix: Optional[str] = None
    page_url: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_sarif_result(self) -> Dict[str, Any]:
        """Convert barrier into a SARIF 2.1.0 result entry."""
        level_map = {
            "critical": "error",
            "serious": "error",
            "moderate": "warning",
            "minor": "note",
        }
        return {
            "ruleId": f"WCAG-{self.wcag_criterion}",
            "level": level_map.get(self.impact, "warning"),
            "message": {
                "text": f"[{self.wcag_criterion} {self.criterion_name}] {self.failure_summary}"
            },
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {
                            "uri": self.page_url or "target-website",
                        },
                        "region": {
                            "snippet": {
                                "text": self.html_snippet or self.element_selector
                            }
                        },
                    }
                }
            ],
            "properties": {
                "impact": self.impact,
                "elementSelector": self.element_selector,
                "suggestedFix": self.suggested_fix,
            },
        }


class RecordAccessibilityBarrierTool(BaseTool):
    """Tool allowing agents to systematically record WCAG 2.2 Level AA accessibility defects."""

    name = "record_accessibility_barrier"
    description = (
        "Log a verified WCAG 2.2 accessibility barrier with criterion number (e.g. 1.4.3, 2.1.1, 2.5.8), "
        "impact level, offending element selector, and suggested developer fix."
    )

    def __init__(self) -> None:
        self.barriers: List[AccessibilityBarrierRecord] = []

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "wcag_criterion": {
                    "type": "string",
                    "description": "WCAG 2.2 criterion code (e.g. '1.4.3', '2.1.1', '2.5.8', '4.1.2').",
                },
                "impact": {
                    "type": "string",
                    "enum": ["critical", "serious", "moderate", "minor"],
                    "description": "Impact of barrier on users with disabilities (critical completely blocks access).",
                },
                "element_selector": {
                    "type": "string",
                    "description": "CSS selector or element description of the inaccessible element.",
                },
                "failure_summary": {
                    "type": "string",
                    "description": "Description of why the element fails accessibility standards.",
                },
                "html_snippet": {
                    "type": "string",
                    "description": "HTML snippet of the offending element if available.",
                },
                "suggested_fix": {
                    "type": "string",
                    "description": "Recommended code or markup modification to achieve compliance.",
                },
                "page_url": {
                    "type": "string",
                    "description": "URL of the page where the barrier was detected.",
                },
            },
            "required": ["wcag_criterion", "impact", "element_selector", "failure_summary"],
            "additionalProperties": False,
        }

    def execute(self, **kwargs: Any) -> ToolResult:
        code = str(kwargs.get("wcag_criterion", "")).strip()
        impact = str(kwargs.get("impact", "moderate")).lower()
        element = str(kwargs.get("element_selector", "")).strip()
        summary = str(kwargs.get("failure_summary", "")).strip()
        snippet = kwargs.get("html_snippet")
        fix = kwargs.get("suggested_fix")
        page_url = kwargs.get("page_url")

        criterion_name = COMMON_WCAG_CRITERIA.get(code, f"WCAG Criterion {code}")
        barrier_id = f"A11Y-{len(self.barriers) + 1:03d}"

        record = AccessibilityBarrierRecord(
            barrier_id=barrier_id,
            wcag_criterion=code,
            criterion_name=criterion_name,
            impact=impact,
            element_selector=element,
            html_snippet=snippet,
            failure_summary=summary,
            suggested_fix=fix,
            page_url=page_url,
        )
        self.barriers.append(record)

        return ToolResult(
            success=True,
            output=f"[{barrier_id}] ({impact.upper()}) Logged: WCAG {code} ({criterion_name}) on `{element}`: {summary}",
            data={
                "barrier_id": barrier_id,
                "wcag_criterion": code,
                "criterion_name": criterion_name,
                "impact": impact,
                "element_selector": element,
                "total_barriers_logged": len(self.barriers),
            },
        )
