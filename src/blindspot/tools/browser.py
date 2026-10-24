"""Browser Action Tool for executing UI interactions via Playwright."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from blindspot.tools.base import BaseTool, ToolResult


class BrowserActionTool(BaseTool):
    """Tool allowing persona agents to perform browser actions against the target page."""

    name = "browser_act"
    description = (
        "Interact with the target web page using Playwright. "
        "Supported actions: 'click', 'fill', 'hover', 'press', 'scroll', 'navigate'."
    )

    def __init__(self, page: Optional[Any] = None) -> None:
        self.page = page  # Playwright Page object (or None in standalone/mock mode)

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["click", "fill", "hover", "press", "scroll", "navigate"],
                    "description": "Browser action to execute.",
                },
                "selector": {
                    "type": "string",
                    "description": "CSS selector, text selector, or element ID (e.g. '#btn-submit', 'button:has-text(\"Sign In\")').",
                },
                "value": {
                    "type": "string",
                    "description": "Text to fill, key to press ('Enter', 'Tab'), or URL to navigate to.",
                },
                "timeout_ms": {
                    "type": "integer",
                    "description": "Action timeout in milliseconds (default: 5000).",
                },
            },
            "required": ["action"],
            "additionalProperties": False,
        }

    def execute(self, **kwargs: Any) -> ToolResult:
        action = str(kwargs.get("action", "click")).lower().strip()
        selector = kwargs.get("selector")
        value = kwargs.get("value")
        timeout_ms = int(kwargs.get("timeout_ms", 5000))

        if not self.page:
            # Standalone or mock simulation mode
            return ToolResult(
                success=True,
                output=f"[Simulated] Executed '{action}' on selector='{selector}' with value='{value}'.",
                data={"simulated": True, "action": action, "selector": selector, "value": value},
            )

        try:
            if action == "click":
                if not selector:
                    return ToolResult(success=False, output="Selector required for click.", error="missing_selector")
                self.page.click(selector, timeout=timeout_ms)
                return ToolResult(success=True, output=f"Clicked element `{selector}`.")

            elif action == "fill":
                if not selector or value is None:
                    return ToolResult(success=False, output="Selector and value required for fill.", error="missing_args")
                self.page.fill(selector, str(value), timeout=timeout_ms)
                return ToolResult(success=True, output=f"Filled `{selector}` with '{value}'.")

            elif action == "hover":
                if not selector:
                    return ToolResult(success=False, output="Selector required for hover.", error="missing_selector")
                self.page.hover(selector, timeout=timeout_ms)
                return ToolResult(success=True, output=f"Hovered over element `{selector}`.")

            elif action == "press":
                key = value or "Enter"
                if selector:
                    self.page.press(selector, key, timeout=timeout_ms)
                else:
                    self.page.keyboard.press(key)
                return ToolResult(success=True, output=f"Pressed key '{key}'.")

            elif action == "scroll":
                delta_y = int(value or 400)
                self.page.mouse.wheel(0, delta_y)
                return ToolResult(success=True, output=f"Scrolled window by {delta_y}px.")

            elif action == "navigate":
                if not value:
                    return ToolResult(success=False, output="URL value required for navigate.", error="missing_url")
                self.page.goto(str(value), timeout=timeout_ms)
                return ToolResult(success=True, output=f"Navigated to `{value}`.")

            return ToolResult(success=False, output=f"Unsupported action '{action}'.", error="unsupported_action")

        except Exception as exc:
            return ToolResult(
                success=False,
                output=f"Browser action '{action}' failed on `{selector}`: {exc}",
                error=str(exc),
            )
