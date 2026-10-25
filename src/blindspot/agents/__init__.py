"""Agents module for BlindSpot.

Provides autonomous agent factories, persona testing loops, and prompts.
"""

from blindspot.agents.factory import create_persona_agent, create_test_runner
from blindspot.agents.prompt import build_agent_step_prompt, build_agent_system_prompt
from blindspot.execution.agent import PersonaTaskAgent
from blindspot.execution.runner import PersonaTestRunner, execute_persona_tasks

__all__ = [
    "PersonaTaskAgent",
    "PersonaTestRunner",
    "build_agent_step_prompt",
    "build_agent_system_prompt",
    "create_persona_agent",
    "create_test_runner",
    "execute_persona_tasks",
]
