"""Journey Todo Tool for managing dynamic task lists during persona user journeys."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from blindspot.tools.base import BaseTool, ToolResult


class TodoStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"


@dataclass
class JourneyTodoItem:
    """A single checkpoint or goal in a persona's test journey."""

    item_id: str
    description: str
    status: TodoStatus = TodoStatus.PENDING
    notes: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class JourneyTodoTool(BaseTool):
    """Tool allowing agents to manage a dynamic checklist of journey checkpoints."""

    name = "manage_journey_todos"
    description = (
        "Manage the persona's checklist of steps and checkpoints in their test journey. "
        "Actions: 'add', 'list', 'update', 'complete', 'block'."
    )

    def __init__(self) -> None:
        self.todos: Dict[str, JourneyTodoItem] = {}
        self._counter = 1

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["add", "list", "update", "complete", "block"],
                    "description": "Action to perform on the todo list.",
                },
                "item_id": {
                    "type": "string",
                    "description": "Identifier of the item (required for update, complete, block).",
                },
                "description": {
                    "type": "string",
                    "description": "Description of the journey checkpoint (required for add).",
                },
                "notes": {
                    "type": "string",
                    "description": "Optional notes or outcome summary for this checkpoint.",
                },
            },
            "required": ["action"],
            "additionalProperties": False,
        }

    def execute(self, **kwargs: Any) -> ToolResult:
        action = str(kwargs.get("action", "list")).lower()
        item_id = kwargs.get("item_id")
        desc = kwargs.get("description")
        notes = kwargs.get("notes")

        if action == "add":
            if not desc:
                return ToolResult(success=False, output="Description required to add todo.", error="missing_description")
            tid = f"TODO-{self._counter}"
            self._counter += 1
            item = JourneyTodoItem(item_id=tid, description=desc, notes=notes)
            self.todos[tid] = item
            return ToolResult(
                success=True,
                output=f"Added checkpoint [{tid}]: {desc}",
                data={"item_id": tid, "status": item.status.value},
            )

        elif action == "complete":
            if not item_id or item_id not in self.todos:
                return ToolResult(success=False, output=f"Item '{item_id}' not found.", error="item_not_found")
            self.todos[item_id].status = TodoStatus.COMPLETED
            if notes:
                self.todos[item_id].notes = notes
            return ToolResult(
                success=True,
                output=f"Checkpoint [{item_id}] marked COMPLETED.",
                data={"item_id": item_id, "status": "completed"},
            )

        elif action == "block":
            if not item_id or item_id not in self.todos:
                return ToolResult(success=False, output=f"Item '{item_id}' not found.", error="item_not_found")
            self.todos[item_id].status = TodoStatus.BLOCKED
            if notes:
                self.todos[item_id].notes = notes
            return ToolResult(
                success=True,
                output=f"Checkpoint [{item_id}] marked BLOCKED: {notes or 'No reason provided.'}",
                data={"item_id": item_id, "status": "blocked"},
            )

        elif action == "update":
            if not item_id or item_id not in self.todos:
                return ToolResult(success=False, output=f"Item '{item_id}' not found.", error="item_not_found")
            if desc:
                self.todos[item_id].description = desc
            if notes:
                self.todos[item_id].notes = notes
            return ToolResult(
                success=True,
                output=f"Checkpoint [{item_id}] updated.",
                data={"item_id": item_id},
            )

        # Default: list
        summary_lines = []
        for tid, t in self.todos.items():
            box = "[X]" if t.status == TodoStatus.COMPLETED else "[!]" if t.status == TodoStatus.BLOCKED else "[ ]"
            summary_lines.append(f"{box} {tid}: {t.description} ({t.status.value})")

        list_output = "\n".join(summary_lines) if summary_lines else "Todo list is empty."
        return ToolResult(
            success=True,
            output=list_output,
            data={
                "total_items": len(self.todos),
                "completed": sum(1 for t in self.todos.values() if t.status == TodoStatus.COMPLETED),
                "pending": sum(1 for t in self.todos.values() if t.status == TodoStatus.PENDING),
                "blocked": sum(1 for t in self.todos.values() if t.status == TodoStatus.BLOCKED),
            },
        )
