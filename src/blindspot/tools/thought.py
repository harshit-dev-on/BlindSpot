"""User Thought Tool for recording persona cognitive state and frustration levels."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from blindspot.tools.base import BaseTool, ToolResult


@dataclass
class PersonaThoughtRecord:
    """A single record of a persona's internal thoughts during exploration."""

    persona_name: str
    observation: str
    expectation: str
    frustration_level: int  # 1 (completely smooth) to 10 (blocking rage / abandonment)
    confusion_points: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class UserThoughtTool(BaseTool):
    """Tool allowing a simulated persona to express thoughts, expectations, and frustration."""

    name = "user_thought"
    description = (
        "Express the persona's internal cognitive state, what they are trying to achieve, "
        "what they expected to happen, and their current frustration level (1-10)."
    )

    def __init__(self) -> None:
        self.thought_history: List[PersonaThoughtRecord] = []

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "persona_name": {
                    "type": "string",
                    "description": "Name of the persona currently executing the journey.",
                },
                "observation": {
                    "type": "string",
                    "description": "What the persona currently sees or experienced on the screen.",
                },
                "expectation": {
                    "type": "string",
                    "description": "What the persona expected to see or happen based on their mental model.",
                },
                "frustration_level": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10,
                    "description": "Frustration level from 1 (delighted/easy) to 10 (rage-quit / blocked).",
                },
                "confusion_points": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Specific UI elements, labels, or behaviors that caused confusion.",
                },
            },
            "required": ["persona_name", "observation", "expectation", "frustration_level"],
            "additionalProperties": False,
        }

    def execute(self, **kwargs: Any) -> ToolResult:
        persona_name = str(kwargs.get("persona_name", "Unknown Persona")).strip()
        observation = str(kwargs.get("observation", "")).strip()
        expectation = str(kwargs.get("expectation", "")).strip()
        frustration = int(kwargs.get("frustration_level", 1))
        confusion = [str(c) for c in kwargs.get("confusion_points", []) if c]

        record = PersonaThoughtRecord(
            persona_name=persona_name,
            observation=observation,
            expectation=expectation,
            frustration_level=max(1, min(10, frustration)),
            confusion_points=confusion,
        )
        self.thought_history.append(record)

        sentiment = (
            "delighted" if frustration <= 2
            else "smooth" if frustration <= 4
            else "irritated" if frustration <= 6
            else "frustrated" if frustration <= 8
            else "blocked/rage"
        )

        return ToolResult(
            success=True,
            output=f"[{persona_name}] Thought logged (Frustration: {frustration}/10 - {sentiment}): {observation}",
            data={
                "persona_name": persona_name,
                "frustration_level": frustration,
                "sentiment": sentiment,
                "total_thoughts_logged": len(self.thought_history),
            },
        )
