"""Record UX Friction Tool for logging Nielsen-Norman heuristic usability flaws."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from blindspot.tools.base import BaseTool, ToolResult


class UsabilityHeuristic(str, Enum):
    """The 10 Nielsen-Norman Usability Heuristics."""

    VISIBILITY_OF_STATUS = "1. Visibility of system status"
    MATCH_REAL_WORLD = "2. Match between system and real world"
    USER_CONTROL_FREEDOM = "3. User control and freedom"
    CONSISTENCY_STANDARDS = "4. Consistency and standards"
    ERROR_PREVENTION = "5. Error prevention"
    RECOGNITION_OVER_RECALL = "6. Recognition rather than recall"
    FLEXIBILITY_EFFICIENCY = "7. Flexibility and efficiency of use"
    AESTHETIC_MINIMALIST = "8. Aesthetic and minimalist design"
    ERROR_RECOVERY = "9. Help users recognize, diagnose, and recover from errors"
    HELP_DOCUMENTATION = "10. Help and documentation"
    OTHER = "General UX Friction"


@dataclass
class UXFrictionRecord:
    """Detailed record of an observed usability friction point."""

    issue_id: str
    title: str
    description: str
    heuristic: UsabilityHeuristic
    severity: str  # "minor", "moderate", "critical"
    element_selector: Optional[str] = None
    page_url: Optional[str] = None
    screenshot_ref: Optional[str] = None
    remediation_suggestion: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class RecordUXFrictionTool(BaseTool):
    """Tool allowing agents to systematically log verified UX flaws and usability barriers."""

    name = "record_ux_friction"
    description = (
        "Log a concrete usability issue or UX friction point observed on the page, "
        "categorized by Nielsen-Norman usability heuristic with severity and recommended remediation."
    )

    def __init__(self) -> None:
        self.friction_records: List[UXFrictionRecord] = []

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Short, clear summary of the usability issue (e.g., 'Unclear submit button feedback').",
                },
                "description": {
                    "type": "string",
                    "description": "Detailed explanation of why this creates friction for the user.",
                },
                "heuristic": {
                    "type": "string",
                    "enum": [h.value for h in UsabilityHeuristic],
                    "description": "Applicable Nielsen-Norman usability heuristic.",
                },
                "severity": {
                    "type": "string",
                    "enum": ["minor", "moderate", "critical"],
                    "description": "Severity of the issue from minor cosmetic to journey-blocking critical.",
                },
                "element_selector": {
                    "type": "string",
                    "description": "CSS selector or identifier of the offending UI element (if applicable).",
                },
                "page_url": {
                    "type": "string",
                    "description": "URL where the issue occurred.",
                },
                "remediation_suggestion": {
                    "type": "string",
                    "description": "Specific actionable suggestion for developer to fix the issue.",
                },
            },
            "required": ["title", "description", "heuristic", "severity"],
            "additionalProperties": False,
        }

    def execute(self, **kwargs: Any) -> ToolResult:
        title = str(kwargs.get("title", "")).strip()
        description = str(kwargs.get("description", "")).strip()
        raw_heuristic = str(kwargs.get("heuristic", UsabilityHeuristic.OTHER.value))
        severity = str(kwargs.get("severity", "moderate")).lower()
        element_selector = kwargs.get("element_selector")
        page_url = kwargs.get("page_url")
        suggestion = kwargs.get("remediation_suggestion")

        # Resolve heuristic safely
        heuristic = UsabilityHeuristic.OTHER
        for h in UsabilityHeuristic:
            if h.value == raw_heuristic or h.name.lower() == raw_heuristic.lower():
                heuristic = h
                break

        issue_id = f"UX-{len(self.friction_records) + 1:03d}"
        record = UXFrictionRecord(
            issue_id=issue_id,
            title=title,
            description=description,
            heuristic=heuristic,
            severity=severity,
            element_selector=element_selector,
            page_url=page_url,
            remediation_suggestion=suggestion,
        )
        self.friction_records.append(record)

        return ToolResult(
            success=True,
            output=f"[{issue_id}] ({severity.upper()}) Logged: {title} ({heuristic.value})",
            data={
                "issue_id": issue_id,
                "title": title,
                "severity": severity,
                "heuristic": heuristic.value,
                "total_issues_logged": len(self.friction_records),
            },
        )
