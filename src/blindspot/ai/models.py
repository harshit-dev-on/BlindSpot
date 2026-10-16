"""Data models for AI provider responses and metadata."""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class AIResponse(BaseModel):
    """Container for AI model output and execution metadata."""

    content: str = Field(..., description="Generated text response from the model")
    model: str = Field(..., description="Model identifier used for generation")
    provider: str = Field(..., description="Provider name (e.g. 'ollama', 'openai_compatible')")
    usage: Optional[Dict[str, Any]] = Field(default=None, description="Token usage statistics if provided")
    raw_response: Optional[Dict[str, Any]] = Field(default=None, description="Raw provider response payload")


class ProviderStatus(BaseModel):
    """Health check and connectivity status for a provider."""

    provider: str
    model: str
    base_url: str
    is_reachable: bool
    model_available: bool
    latency_ms: Optional[float] = None
    message: str = ""
    available_models: Optional[list[str]] = None
