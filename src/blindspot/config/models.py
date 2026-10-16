"""Configuration schema models for BlindSpot and universal AI providers."""

from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel, Field, field_validator


VALID_CATEGORIES: Tuple[str, ...] = ("local", "cloud", "custom", "hybrid")

VALID_PROVIDERS: Tuple[str, ...] = (
    "ollama",
    "gemini",
    "openai",
    "anthropic",
    "openrouter",
    "custom",
    "openai_compatible",  # alias for custom
)


class TaskModelsConfig(BaseModel):
    """Optional task-specific model overrides for future pipeline stages."""

    persona_generation: Optional[str] = Field(
        default=None, description="Model to use for synthesizing user personas"
    )
    task_planning: Optional[str] = Field(
        default=None, description="Model to use for website task planning"
    )
    ux_analysis: Optional[str] = Field(
        default=None, description="Model to use for analyzing UX findings"
    )
    report_generation: Optional[str] = Field(
        default=None, description="Model to use for consolidating final UX reports"
    )


class AIConfig(BaseModel):
    """Configuration for AI model inference and provider connectivity."""

    category: str = Field(
        default="local",
        description="Deployment category: 'local', 'cloud', 'custom', or 'hybrid'",
    )
    provider: str = Field(
        default="ollama",
        description="AI provider identifier ('ollama', 'gemini', 'openai', 'anthropic', 'openrouter', 'custom')",
    )
    model: str = Field(
        default="gemma4",
        description="Model name or identifier (e.g. 'gemma4', 'gemini-2.5-flash', 'gpt-4o-mini')",
    )
    base_url: Optional[str] = Field(
        default=None,
        description="Custom base URL for the provider endpoint",
    )
    api_key_env: Optional[str] = Field(
        default=None,
        description="Name of the environment variable storing the API key",
    )
    api_key: Optional[str] = Field(
        default=None,
        description="Direct API key (prefer environment variable for security)",
    )
    timeout: float = Field(
        default=60.0,
        description="API request timeout in seconds",
        ge=1.0,
    )
    tasks: TaskModelsConfig = Field(
        default_factory=TaskModelsConfig,
        description="Task-specific model overrides",
    )

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        clean = v.strip().lower()
        if clean not in VALID_CATEGORIES:
            raise ValueError(
                f"Unsupported AI category '{v}'. Supported: {', '.join(VALID_CATEGORIES)}"
            )
        return clean

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
