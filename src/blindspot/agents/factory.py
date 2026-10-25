"""Agent factory for instantiating persona test agents."""

from typing import Optional

from blindspot.ai.base import BaseAIProvider
from blindspot.ai.factory import create_provider
from blindspot.config.models import AIConfig, BlindSpotConfig
from blindspot.execution.agent import PersonaTaskAgent
from blindspot.execution.runner import PersonaTestRunner


def create_persona_agent(
    provider: Optional[BaseAIProvider] = None,
    ai_config: Optional[AIConfig] = None,
    max_actions: int = 8,
    action_timeout_ms: int = 8000,
    allow_local: bool = False,
) -> PersonaTaskAgent:
    """Instantiate a PersonaTaskAgent with the given configuration or provider."""
    if provider is None:
        if ai_config is None:
            from blindspot.config.loader import load_config
            ai_config = load_config().ai
        provider = create_provider(ai_config)

    return PersonaTaskAgent(
        provider=provider,
        max_actions=max_actions,
        action_timeout_ms=action_timeout_ms,
        allow_local=allow_local,
    )


def create_test_runner(
    provider: Optional[BaseAIProvider] = None,
    ai_config: Optional[AIConfig] = None,
    browser_type: str = "chromium",
    headless: bool = True,
    max_actions_per_task: int = 8,
    action_timeout_ms: int = 8000,
    allow_local: bool = False,
) -> PersonaTestRunner:
    """Instantiate a PersonaTestRunner configured for end-to-end UX audits."""
    if provider is None:
        if ai_config is None:
            from blindspot.config.loader import load_config
            ai_config = load_config().ai
        provider = create_provider(ai_config)

    return PersonaTestRunner(
        provider=provider,
        browser_type=browser_type,
        headless=headless,
        max_actions_per_task=max_actions_per_task,
        action_timeout_ms=action_timeout_ms,
        allow_local=allow_local,
    )
