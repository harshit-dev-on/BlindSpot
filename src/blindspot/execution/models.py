"""Data models for automated browser task execution, actions, and evidence collection."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ActionType(str, Enum):
    """Supported browser actions for the vision-based execution agent."""

    CLICK = "click"
    TYPE = "type"
    FILL = "fill"
    PRESS = "press"
    SELECT = "select"
    SCROLL = "scroll"
    HOVER = "hover"
    WAIT = "wait"
    NAVIGATE = "navigate"
    CHECK_SUCCESS = "check_success"
    FINISH = "finish"


class TaskStatus(str, Enum):
    """Outcome status of an executed persona task."""

    SUCCESS = "success"
    FAILURE = "failure"
    INCONCLUSIVE = "inconclusive"


class AgentAction(BaseModel):
    """Structured action response returned by the vision agent."""

    action: ActionType = Field(
        ...,
        description="The browser action: 'click', 'type', 'fill', 'press', 'scroll', 'hover', 'wait', 'finish'",
    )
    mark: Optional[int] = Field(
        default=None,
        description="Mark badge number [N] to interact with",
    )
    x: Optional[int] = Field(
        default=None,
        description="Screen horizontal X coordinate (pixels) to click/hover",
    )
    y: Optional[int] = Field(
        default=None,
        description="Screen vertical Y coordinate (pixels) to click/hover",
    )
    text: Optional[str] = Field(
        default=None,
        description="Text to type into input field",
    )
    press_enter: Optional[bool] = Field(
        default=False,
        description="Whether to press Enter key immediately after typing",
    )
    key: Optional[str] = Field(
        default=None,
        description="Keyboard key to press (e.g. 'Enter', 'Tab', 'Escape', 'ArrowDown')",
    )
    direction: Optional[str] = Field(
        default="down",
        description="Scroll direction ('up', 'down', 'left', 'right')",
    )
    amount: Optional[int] = Field(
        default=400,
        description="Scroll amount in pixels (default: 400)",
    )
    target: Optional[str] = Field(
        default=None,
        description="Legacy target identifier, selector, or mark reference",
    )
    value: Optional[str] = Field(
        default=None,
        description="Legacy input text or scroll parameter",
    )
    reasoning: str = Field(
        ...,
        description="Visual reasoning: what you see on the screenshot and why you chose this action",
    )


class ActionExecutionRecord(BaseModel):
    """Detailed log record of an attempted action during task execution."""

    step: int
    action: AgentAction
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    success: bool
    error: Optional[str] = None
    page_url: str
    page_title: str
    screenshot_path: Optional[str] = None


class TaskExecutionResult(BaseModel):
    """Consolidated outcome, logs, and evidence for a single persona task."""

    task_id: str
    persona_id: str
    task_objective: str
    status: TaskStatus
    start_time: str
    end_time: str
    initial_url: str
    final_url: str
    actions_taken: List[ActionExecutionRecord] = Field(default_factory=list)
    evidence: List[str] = Field(default_factory=list)
    evidence_screenshots: List[str] = Field(default_factory=list)
    notes: Optional[str] = None
    error_message: Optional[str] = None


class PersonaExecutionResult(BaseModel):
    """Execution results for all tasks assigned to a specific persona."""

    persona_id: str
    persona_name: str
    task_results: List[TaskExecutionResult] = Field(default_factory=list)

    @property
    def passed_tasks(self) -> int:
        return sum(1 for t in self.task_results if t.status == TaskStatus.SUCCESS)

    @property
    def failed_tasks(self) -> int:
        return sum(1 for t in self.task_results if t.status == TaskStatus.FAILURE)

    @property
    def inconclusive_tasks(self) -> int:
        return sum(1 for t in self.task_results if t.status == TaskStatus.INCONCLUSIVE)


class ExecutionRunResult(BaseModel):
    """Complete summary of all personas and tasks executed in an inspection run."""

    target_url: str
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    browser: str
    headless: bool
    personas: List[PersonaExecutionResult] = Field(default_factory=list)
    results_file_path: Optional[str] = None

    @property
    def total_tasks(self) -> int:
        return sum(len(p.task_results) for p in self.personas)

    @property
    def passed_tasks(self) -> int:
        return sum(p.passed_tasks for p in self.personas)

    @property
    def failed_tasks(self) -> int:
        return sum(p.failed_tasks for p in self.personas)

    @property
    def inconclusive_tasks(self) -> int:
        return sum(p.inconclusive_tasks for p in self.personas)
