"""Custom exceptions for the AI provider layer."""

from typing import Optional


class AIProviderError(Exception):
    """Base exception for all AI provider errors."""

    def __init__(self, message: str, provider: Optional[str] = None, suggestion: Optional[str] = None) -> None:
        full_msg = f"{message} {suggestion}" if suggestion else message
        super().__init__(full_msg)
        self.message = message
        self.provider = provider
        self.suggestion = suggestion


class AIConnectionError(AIProviderError):
    """Raised when unable to reach the AI server or endpoint."""
    pass


class AIModelNotFoundError(AIProviderError):
    """Raised when the specified model is not found on the provider."""
    pass


class AIAuthenticationError(AIProviderError):
    """Raised when authentication fails (missing or invalid API key)."""
    pass


class AITimeoutError(AIProviderError):
    """Raised when the provider request exceeds the configured timeout."""
    pass


class AIStructuredOutputError(AIProviderError):
    """Raised when the model fails to return valid structured JSON matching the schema."""

    def __init__(
        self,
        message: str,
        raw_output: str,
        provider: Optional[str] = None,
        suggestion: Optional[str] = None,
    ) -> None:
        super().__init__(message, provider=provider, suggestion=suggestion)
        self.raw_output = raw_output
