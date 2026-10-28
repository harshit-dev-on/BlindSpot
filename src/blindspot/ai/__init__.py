"""Universal AI provider integration layer for BlindSpot."""

from blindspot.ai.adapter import (
    CURATED_MODELS,
    DEFAULT_BASE_URLS,
    DEFAULT_KEY_ENVS,
    DEFAULT_PROVIDER_MODELS,
    UnifiedAIAdapter,
    get_models_for_provider,
)
from blindspot.ai.base import BaseAIProvider, extract_json_string, mask_api_key
from blindspot.ai.exceptions import (
    AIAuthenticationError,
    AIConnectionError,
    AIModelNotFoundError,
    AIProviderError,
    AIStructuredOutputError,
    AITimeoutError,
)
from blindspot.ai.factory import create_provider
from blindspot.ai.models import AIResponse, ProviderStatus
from blindspot.ai.providers.antigravity import AntigravityProvider
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
    "AntigravityProvider",
    "BaseAIProvider",
    "CURATED_MODELS",
    "DEFAULT_BASE_URLS",
    "DEFAULT_KEY_ENVS",
    "DEFAULT_PROVIDER_MODELS",
    "OllamaProvider",
    "OpenAICompatibleProvider",
    "ProviderStatus",
    "UnifiedAIAdapter",
    "create_provider",
    "extract_json_string",
    "get_models_for_provider",
    "mask_api_key",
]
