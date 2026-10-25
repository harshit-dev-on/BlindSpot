"""BlindSpot Agent Tools suite.

Provides specialized capabilities for persona simulation, cognitive tracking,
UX friction logging, and WCAG accessibility audits.
"""

from blindspot.tools.accessibility import (
    AccessibilityBarrierRecord,
    COMMON_WCAG_CRITERIA,
    RecordAccessibilityBarrierTool,
)
from blindspot.tools.base import BaseTool, ToolResult
from blindspot.tools.browser import BrowserActionTool
from blindspot.tools.friction import (
    RecordUXFrictionTool,
    UsabilityHeuristic,
    UXFrictionRecord,
)
from blindspot.tools.notes import SessionNotesTool
from blindspot.tools.thought import PersonaThoughtRecord, UserThoughtTool
from blindspot.tools.todo import JourneyTodoItem, JourneyTodoTool, TodoStatus

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
