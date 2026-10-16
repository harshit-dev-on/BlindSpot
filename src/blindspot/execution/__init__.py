"""Automated persona-based browser task execution module for BlindSpot."""

from blindspot.execution.models import (
    ActionExecutionRecord,
    ActionType,
    AgentAction,
    ExecutionRunResult,
    PersonaExecutionResult,
    TaskExecutionResult,
    TaskStatus,
)
from blindspot.execution.agent import PersonaTaskAgent
from blindspot.execution.runner import PersonaTestRunner, execute_persona_tasks
from blindspot.execution.safety import (
    is_action_destructive,
    is_ip_private_or_restricted,
    mask_sensitive_input,
    validate_navigation_url,
)

__all__ = [
    "ActionExecutionRecord",
    "ActionType",
    "AgentAction",
    "ExecutionRunResult",
    "PersonaExecutionResult",
    "TaskExecutionResult",
    "TaskStatus",
    "PersonaTaskAgent",
    "PersonaTestRunner",
    "execute_persona_tasks",
    "is_action_destructive",
    "is_ip_private_or_restricted",
    "mask_sensitive_input",
    "validate_navigation_url",
]
