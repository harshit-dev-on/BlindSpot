"""Base classes and interfaces for BlindSpot Agent Tools."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import json
from typing import Any, Dict, Optional


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
