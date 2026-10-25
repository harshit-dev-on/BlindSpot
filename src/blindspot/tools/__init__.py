"""BlindSpot Agent Tools suite.

Provides specialized capabilities for persona simulation, cognitive tracking,
UX friction logging, and WCAG accessibility audits.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


@dataclass
class ToolResult:
    """Standardized result returned by any BlindSpot agent tool."""

    success: bool
    output: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "output": self.output,
            "data": self.data or {},
            "error": self.error,
        }

    def __str__(self) -> str:
        return self.output


class BaseTool(ABC):
    """Abstract base class for all callable tools."""

    name: str = ""
    description: str = ""

    @abstractmethod
    def get_parameters_schema(self) -> Dict[str, Any]:
        """Return the JSON schema describing input arguments."""
        pass

    @abstractmethod
    def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the tool logic and return a ToolResult."""
        pass

    def to_openai_tool(self) -> Dict[str, Any]:
        """Convert to OpenAI / LiteLLM function calling schema."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.get_parameters_schema(),
            },
        }


# ─── Cognitive Tracking ───────────────────────────────────────────────────────


@dataclass
class PersonaThoughtRecord:
    persona_name: str
    observation: str
    expectation: str
    frustration_level: int
    confusion_points: List[str]
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class UserThoughtTool(BaseTool):
    """Logs internal cognitive reactions and frustration levels during simulation."""

    name = "log_user_thought"
    description = "Record internal cognitive reactions, expectations, and frustration level (1-10)."

    def __init__(self) -> None:
        self.thought_history: List[PersonaThoughtRecord] = []

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "persona_name": {"type": "string"},
                "observation": {"type": "string"},
                "expectation": {"type": "string"},
                "frustration_level": {"type": "integer"},
                "confusion_points": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["persona_name", "observation", "expectation", "frustration_level"],
        }

    def execute(self, **kwargs: Any) -> ToolResult:
        pname = str(kwargs.get("persona_name", "Anonymous"))
        obs = str(kwargs.get("observation", ""))
        exp = str(kwargs.get("expectation", ""))
        frust = int(kwargs.get("frustration_level", 1))
        conf = list(kwargs.get("confusion_points", []))

        record = PersonaThoughtRecord(
            persona_name=pname,
            observation=obs,
            expectation=exp,
            frustration_level=frust,
            confusion_points=conf,
        )
        self.thought_history.append(record)
        return ToolResult(
            success=True,
            output=f"Logged thought for {pname}. Frustration: {frust}/10.",
            data={"record_index": len(self.thought_history) - 1},
        )


# ─── UX Friction ─────────────────────────────────────────────────────────────


class UsabilityHeuristic(str, Enum):
    VISIBILITY_OF_STATUS = "1. Visibility of system status"
    MATCH_REAL_WORLD = "2. Match between system and real world"
    USER_CONTROL = "3. User control and freedom"
    CONSISTENCY_STANDARDS = "4. Consistency and standards"
    ERROR_PREVENTION = "5. Error prevention"
    RECOGNITION_NOT_RECALL = "6. Recognition rather than recall"
    FLEXIBILITY_EFFICIENCY = "7. Flexibility and efficiency of use"
    AESTHETIC_MINIMALIST = "8. Aesthetic and minimalist design"
    HELP_RECOGNIZE_ERRORS = "9. Help users recognize, diagnose, and recover from errors"
    HELP_DOCUMENTATION = "10. Help and documentation"


@dataclass
class UXFrictionRecord:
    issue_id: str
    title: str
    description: str
    heuristic: UsabilityHeuristic
    severity: str
    element_selector: Optional[str] = None
    page_url: Optional[str] = None
    remediation_suggestion: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class RecordUXFrictionTool(BaseTool):
    """Logs observed UX friction points mapped to usability heuristics."""

    name = "record_ux_friction"
    description = "Log observed UX defects and usability barriers with severity."

    def __init__(self) -> None:
        self.friction_records: List[UXFrictionRecord] = []
        self._counter = 1

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "description": {"type": "string"},
                "heuristic": {"type": "string"},
                "severity": {"type": "string"},
            },
            "required": ["title", "description", "heuristic", "severity"],
        }

    def execute(self, **kwargs: Any) -> ToolResult:
        issue_id = f"UX-{self._counter:03d}"
        self._counter += 1

        raw_heur = str(kwargs.get("heuristic", ""))
        heur = UsabilityHeuristic.VISIBILITY_OF_STATUS
        for h in UsabilityHeuristic:
            if h.value.lower() in raw_heur.lower() or raw_heur.lower() in h.value.lower():
                heur = h
                break

        rec = UXFrictionRecord(
            issue_id=issue_id,
            title=str(kwargs.get("title", "")),
            description=str(kwargs.get("description", "")),
            heuristic=heur,
            severity=str(kwargs.get("severity", "medium")).lower(),
            element_selector=kwargs.get("element_selector"),
            page_url=kwargs.get("page_url"),
            remediation_suggestion=kwargs.get("remediation_suggestion"),
        )
        self.friction_records.append(rec)
        return ToolResult(
            success=True,
            output=f"Recorded {issue_id}: '{rec.title}' ({rec.severity}).",
            data={"issue_id": issue_id},
        )


# ─── Accessibility Barriers ──────────────────────────────────────────────────


COMMON_WCAG_CRITERIA = {
    "1.1.1": "Non-text Content",
    "1.3.1": "Info and Relationships",
    "1.4.3": "Contrast (Minimum)",
    "2.1.1": "Keyboard Accessible",
    "2.4.3": "Focus Order",
    "2.4.7": "Focus Visible",
    "2.5.8": "Target Size (Minimum)",
    "3.3.2": "Labels or Instructions",
    "4.1.2": "Name, Role, Value",
}


@dataclass
class AccessibilityBarrierRecord:
    barrier_id: str
    wcag_criterion: str
    impact: str
    element_selector: str
    html_snippet: Optional[str] = None
    failure_summary: Optional[str] = None
    suggested_fix: Optional[str] = None
    page_url: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def criterion_name(self) -> str:
        return COMMON_WCAG_CRITERIA.get(self.wcag_criterion, "Accessibility Criterion")

    def to_sarif_result(self) -> Dict[str, Any]:
        level_map = {"critical": "error", "serious": "error", "moderate": "warning", "minor": "note"}
        return {
            "ruleId": f"WCAG-{self.wcag_criterion}",
            "level": level_map.get(self.impact, "warning"),
            "message": {
                "text": f"[{self.wcag_criterion} {self.criterion_name}] {self.failure_summary or ''}"
            },
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {"uri": self.page_url or "target-website"},
                        "region": {"snippet": {"text": self.html_snippet or self.element_selector}},
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
    """Logs verified WCAG 2.2 Level AA accessibility defects."""

    name = "record_accessibility_barrier"
    description = "Log a verified WCAG 2.2 accessibility barrier with criterion number and suggested fix."

    def __init__(self) -> None:
        self.barriers: List[AccessibilityBarrierRecord] = []
        self._counter = 1

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "wcag_criterion": {"type": "string"},
                "impact": {"type": "string"},
                "element_selector": {"type": "string"},
            },
            "required": ["wcag_criterion", "impact", "element_selector"],
        }

    def execute(self, **kwargs: Any) -> ToolResult:
        bid = f"A11Y-{self._counter:03d}"
        self._counter += 1

        rec = AccessibilityBarrierRecord(
            barrier_id=bid,
            wcag_criterion=str(kwargs.get("wcag_criterion", "4.1.2")),
            impact=str(kwargs.get("impact", "moderate")).lower(),
            element_selector=str(kwargs.get("element_selector", "")),
            html_snippet=kwargs.get("html_snippet"),
            failure_summary=kwargs.get("failure_summary"),
            suggested_fix=kwargs.get("suggested_fix"),
            page_url=kwargs.get("page_url"),
        )
        self.barriers.append(rec)
        return ToolResult(
            success=True,
            output=f"Recorded accessibility barrier {bid} (WCAG {rec.wcag_criterion}).",
            data={"barrier_id": bid},
        )


# ─── Journey Todos ────────────────────────────────────────────────────────────


class TodoStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"


@dataclass
class JourneyTodoItem:
    item_id: str
    description: str
    status: TodoStatus = TodoStatus.PENDING
    notes: Optional[str] = None
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class JourneyTodoTool(BaseTool):
    """Tracks persona milestones and objectives throughout test runs."""

    name = "journey_todo"
    description = "Manage step-by-step persona journey objectives (add, complete, block, list)."

    def __init__(self) -> None:
        self.todos: Dict[str, JourneyTodoItem] = {}
        self._counter = 1

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {"type": "string"},
                "description": {"type": "string"},
                "item_id": {"type": "string"},
            },
            "required": ["action"],
        }

    def execute(self, **kwargs: Any) -> ToolResult:
        act = str(kwargs.get("action", "list")).lower().strip()
        if act == "add":
            tid = f"TODO-{self._counter}"
            self._counter += 1
            desc = str(kwargs.get("description", ""))
            self.todos[tid] = JourneyTodoItem(item_id=tid, description=desc)
            return ToolResult(success=True, output=f"Added {tid}: {desc}", data={"item_id": tid})
        elif act in ("complete", "block"):
            tid = str(kwargs.get("item_id", ""))
            if tid not in self.todos:
                return ToolResult(success=False, output=f"Item {tid} not found.", error="NOT_FOUND")
            new_st = TodoStatus.COMPLETED if act == "complete" else TodoStatus.BLOCKED
            self.todos[tid].status = new_st
            self.todos[tid].notes = kwargs.get("notes")
            self.todos[tid].updated_at = datetime.now(timezone.utc).isoformat()
            return ToolResult(success=True, output=f"Marked {tid} as {new_st.value}.")
        else:
            lines = []
            for tid, item in self.todos.items():
                mark = "[X] " if item.status == TodoStatus.COMPLETED else ("[!] " if item.status == TodoStatus.BLOCKED else "[ ] ")
                lines.append(f"{mark}{tid}: {item.description}")
            return ToolResult(success=True, output="\n".join(lines) or "No todos.")


# ─── Session Notes ────────────────────────────────────────────────────────────


class SessionNotesTool(BaseTool):
    """Key-value scratchpad for persisting state across persona journey steps."""

    name = "session_notes"
    description = "Store, retrieve, or list context variables (set, get, list, delete)."

    def __init__(self) -> None:
        self.notes: Dict[str, str] = {}

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {"type": "string"},
                "key": {"type": "string"},
                "value": {"type": "string"},
            },
            "required": ["action"],
        }

    def execute(self, **kwargs: Any) -> ToolResult:
        act = str(kwargs.get("action", "list")).lower().strip()
        key = kwargs.get("key")
        val = kwargs.get("value")

        if act == "set" and key:
            self.notes[key] = str(val or "")
            return ToolResult(success=True, output=f"Stored note '{key}'.", data={"key": key, "value": val})
        elif act == "get" and key:
            if key in self.notes:
                return ToolResult(success=True, output=f"{key}: {self.notes[key]}", data={"key": key, "value": self.notes[key]})
            return ToolResult(success=False, output=f"Key '{key}' not found.", error="NOT_FOUND")
        elif act == "delete" and key:
            removed = self.notes.pop(key, None)
            return ToolResult(success=True, output=f"Deleted '{key}'.", data={"deleted": removed is not None})
        else:
            lines = [f"{k}: {v}" for k, v in sorted(self.notes.items())]
            return ToolResult(success=True, output="\n".join(lines) or "No notes stored.")


# ─── Browser Action ──────────────────────────────────────────────────────────


class BrowserActionTool(BaseTool):
    """Tool allowing persona agents to perform browser actions against the target page."""

    name = "browser_act"
    description = "Interact with the target web page using Playwright actions."

    def __init__(self, page: Optional[Any] = None) -> None:
        self.page = page

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {"type": "string"},
                "selector": {"type": "string"},
                "value": {"type": "string"},
            },
            "required": ["action"],
        }

    def execute(self, **kwargs: Any) -> ToolResult:
        action = str(kwargs.get("action", "click")).lower().strip()
        selector = kwargs.get("selector")
        value = kwargs.get("value")

        if self.page is None:
            return ToolResult(
                success=True,
                output=f"[Simulated] Executed '{action}' on '{selector}'.",
                data={"simulated": True, "action": action, "selector": selector, "value": value},
            )

        try:
            if action == "click" and selector:
                self.page.click(selector, timeout=kwargs.get("timeout_ms", 5000))
            elif action == "fill" and selector:
                self.page.fill(selector, str(value or ""), timeout=kwargs.get("timeout_ms", 5000))
            elif action == "navigate" and value:
                self.page.goto(str(value), timeout=kwargs.get("timeout_ms", 15000))
            elif action == "scroll":
                self.page.evaluate("window.scrollBy(0, 500)")
            return ToolResult(success=True, output=f"Performed {action}.")
        except Exception as exc:
            return ToolResult(success=False, output=f"Failed {action}: {exc}", error=str(exc))


__all__ = [
    "BaseTool",
    "ToolResult",
    "BrowserActionTool",
    "UserThoughtTool",
    "PersonaThoughtRecord",
    "RecordUXFrictionTool",
    "UXFrictionRecord",
    "UsabilityHeuristic",
    "RecordAccessibilityBarrierTool",
    "AccessibilityBarrierRecord",
    "COMMON_WCAG_CRITERIA",
    "JourneyTodoTool",
    "JourneyTodoItem",
    "TodoStatus",
    "SessionNotesTool",
]
