"""Configuration schema models for BlindSpot and AI providers."""

from typing import Optional, Tuple
from pydantic import BaseModel, Field, field_validator


VALID_PROVIDERS: Tuple[str, ...] = ("ollama", "openai_compatible")


class AIConfig(BaseModel):
    """Configuration for AI model inference and provider connection."""

    provider: str = Field(
        default="ollama",
        description="AI provider identifier ('ollama' or 'openai_compatible')",
    )
    model: str = Field(
        default="gemma4",
        description="Model name or identifier (e.g. 'gemma4', 'gpt-4o-mini')",
    )
    base_url: Optional[str] = Field(
        default=None,
        description="Custom base URL for the provider endpoint",
    )
    api_key_env: Optional[str] = Field(
        default="OPENAI_API_KEY",
        description="Name of the environment variable storing the API key",
    )
    api_key: Optional[str] = Field(
        default=None,
        description="Direct API key (optional; environment variable preferred)",
    )
    timeout: float = Field(
        default=60.0,
        description="API request timeout in seconds",
        ge=1.0,
    )

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        clean = v.strip().lower()
        if clean not in VALID_PROVIDERS:
            raise ValueError(
                f"Unsupported AI provider '{v}'. Supported options: {', '.join(VALID_PROVIDERS)}"
            )
        return clean

    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Model name cannot be empty.")
        return v.strip()


class BlindSpotConfig(BaseModel):
    """Root application configuration schema."""

    ai: AIConfig = Field(default_factory=AIConfig)
