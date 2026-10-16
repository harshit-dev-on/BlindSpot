"""AI provider integration layer for BlindSpot."""

from blindspot.ai.base import BaseAIProvider, extract_json_string
from blindspot.ai.exceptions import (
    AIAuthenticationError,
    AIConnectionError,
    AIModelNotFoundError,
    AIProviderError,
    AIStructuredOutputError,
    AITimeoutError,
)
from blindspot.ai.factory import PROVIDER_REGISTRY, create_provider
from blindspot.ai.models import AIResponse, ProviderStatus
from blindspot.ai.providers.ollama import OllamaProvider
from blindspot.ai.providers.openai_compatible import OpenAICompatibleProvider

__all__ = [
    "AIAuthenticationError",
    "AIConnectionError",
    "AIModelNotFoundError",
    "AIProviderError",
    "AIResponse",
    "AIStructuredOutputError",
    "AITimeoutError",
    "BaseAIProvider",
    "OllamaProvider",
    "OpenAICompatibleProvider",
    "PROVIDER_REGISTRY",
    "ProviderStatus",
    "create_provider",
    "extract_json_string",
]
