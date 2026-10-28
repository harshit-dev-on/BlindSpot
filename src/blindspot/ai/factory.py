"""Factory function and registry for universal AI providers."""

from typing import Dict, Optional, Type
from blindspot.ai.adapter import (
    DEFAULT_KEY_ENVS,
    DEFAULT_PROVIDER_MODELS,
    UnifiedAIAdapter,
)
from blindspot.ai.base import BaseAIProvider
from blindspot.ai.exceptions import AIProviderError
from blindspot.config.models import AIConfig


def create_provider(config: AIConfig) -> BaseAIProvider:
    """Instantiate a universal AI provider from an AIConfig object."""
    provider_name = config.provider.lower().strip()
    if provider_name in ("antigravity", "agy"):
        from blindspot.ai.providers.antigravity import AntigravityProvider
        return AntigravityProvider(
            model=config.model or "antigravity-brain",
            base_url=config.base_url,
            timeout=config.timeout,
        )

    if provider_name == "openai_compatible":
        provider_name = "custom"

    return UnifiedAIAdapter(
        provider=provider_name,
        model=config.model,
        base_url=config.base_url,
        api_key=config.api_key,
        api_key_env=config.api_key_env,
        timeout=config.timeout,
    )
