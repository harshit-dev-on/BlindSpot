"""Factory function and registry for AI providers."""

from typing import Dict, Optional, Type
from blindspot.ai.base import BaseAIProvider
from blindspot.ai.exceptions import AIProviderError
from blindspot.ai.providers.ollama import OllamaProvider
from blindspot.ai.providers.openai_compatible import OpenAICompatibleProvider
from blindspot.config.models import AIConfig


PROVIDER_REGISTRY: Dict[str, Type[BaseAIProvider]] = {
    "ollama": OllamaProvider,
    "openai_compatible": OpenAICompatibleProvider,
}


def create_provider(config: AIConfig) -> BaseAIProvider:
    """Instantiate an AI provider from an AIConfig object."""
    provider_name = config.provider.lower().strip()
    provider_cls = PROVIDER_REGISTRY.get(provider_name)

    if provider_cls is None:
        raise AIProviderError(
            f"Unsupported provider '{config.provider}'. Available: {', '.join(PROVIDER_REGISTRY.keys())}",
            provider=config.provider,
            suggestion=f"Set provider to one of: {', '.join(PROVIDER_REGISTRY.keys())}.",
        )

    if provider_name == "ollama":
        return OllamaProvider(
            model=config.model,
            base_url=config.base_url,
            timeout=config.timeout,
        )

    if provider_name == "openai_compatible":
        return OpenAICompatibleProvider(
            model=config.model,
            base_url=config.base_url,
            api_key=config.api_key,
            api_key_env=config.api_key_env,
            timeout=config.timeout,
        )

    raise AIProviderError(f"Unhandled provider '{provider_name}'.")
