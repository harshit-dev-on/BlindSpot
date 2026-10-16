"""Data models for automated browser task execution, actions, and evidence collection."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ActionType(str, Enum):
    """Supported browser actions for the controlled execution agent."""

    NAVIGATE = "navigate"
    CLICK = "click"
    FILL = "fill"
    SELECT = "select"
    SCROLL = "scroll"
    WAIT = "wait"
    CHECK_SUCCESS = "check_success"
    FINISH = "finish"


class TaskStatus(str, Enum):
    """Outcome status of an executed persona task."""

    SUCCESS = "success"
    FAILURE = "failure"
    INCONCLUSIVE = "inconclusive"


class AgentAction(BaseModel):
    """Structured action response returned by the AI agent."""

    action: ActionType = Field(
        ...,
        description="The browser action to perform ('navigate', 'click', 'fill', 'select', 'scroll', 'wait', 'check_success', 'finish')",
    )
    target: Optional[str] = Field(
        default=None,
        description="Target selector, element ID, or text identifier to interact with",
    )
    value: Optional[str] = Field(
        default=None,
        description="Input text for 'fill', option value for 'select', or direction ('up'/'down') for 'scroll'",
    )
    reasoning: str = Field(
        ...,
        description="Short rationale explaining how this action advances the persona's task",
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
