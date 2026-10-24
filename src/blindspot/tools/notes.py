"""Session Notes Tool for persistent memory and data sharing during tests."""

from __future__ import annotations

from typing import Any, Dict, Optional

from blindspot.tools.base import BaseTool, ToolResult


class SessionNotesTool(BaseTool):
    """Tool allowing agents to store and retrieve key-value notes (credentials, URLs, observed data)."""

    name = "manage_notes"
    description = (
        "Store, retrieve, or list persistent notes across the testing session. "
        "Useful for remembering generated test emails, form values, and discovered routes. "
        "Actions: 'set', 'get', 'list', 'delete'."
    )

    def __init__(self, initial_notes: Optional[Dict[str, str]] = None) -> None:
        self.notes: Dict[str, str] = dict(initial_notes or {})

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["set", "get", "list", "delete"],
                    "description": "Action to perform on session notes.",
                },
                "key": {
                    "type": "string",
                    "description": "Note key / identifier (required for set, get, delete).",
                },
                "value": {
                    "type": "string",
                    "description": "Note text content (required for set).",
                },
            },
            "required": ["action"],
            "additionalProperties": False,
        }

    def execute(self, **kwargs: Any) -> ToolResult:
        action = str(kwargs.get("action", "list")).lower()
        key = str(kwargs.get("key", "")).strip()
        value = str(kwargs.get("value", "")).strip()

        if action == "set":
            if not key or not value:
                return ToolResult(success=False, output="Key and value required for 'set'.", error="missing_args")
            self.notes[key] = value
            return ToolResult(
                success=True,
                output=f"Note stored: [{key}] = '{value}'",
                data={"key": key, "value": value},
            )

        elif action == "get":
            if not key:
                return ToolResult(success=False, output="Key required for 'get'.", error="missing_key")
            val = self.notes.get(key)
            if val is None:
                return ToolResult(success=False, output=f"Note '{key}' not found.", error="key_not_found")
            return ToolResult(
                success=True,
                output=f"[{key}] = '{val}'",
                data={"key": key, "value": val},
            )

        elif action == "delete":
            if not key:
                return ToolResult(success=False, output="Key required for 'delete'.", error="missing_key")
            deleted = self.notes.pop(key, None)
            if deleted is None:
                return ToolResult(success=False, output=f"Note '{key}' not found.", error="key_not_found")
            return ToolResult(
                success=True,
                output=f"Note '{key}' deleted.",
                data={"key": key},
            )

        # Default: list
        if not self.notes:
            return ToolResult(success=True, output="No notes currently stored.", data={"notes": {}})

        lines = [f"• {k}: {v}" for k, v in sorted(self.notes.items())]
        return ToolResult(
            success=True,
            output="\n".join(lines),
            data={"notes": dict(self.notes)},
        )
