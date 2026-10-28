"""Startup environment validation and configuration preflight."""

from __future__ import annotations

import logging
import os
import sys
from rich.console import Console
from rich.text import Text

from blindspot.config.loader import load_config


from blindspot.config.models import BlindSpotConfig


logger = logging.getLogger(__name__)


def validate_environment(config: Optional[BlindSpotConfig] = None) -> None:
    """Validate that required environment variables or saved configuration are present.

    Provides instant, actionable feedback if model routes or API credentials are not yet configured.
    """
    logger.info("Validating environment and AI configuration")
    console = Console()
    missing_required_vars: list[str] = []
    missing_optional_vars: list[str] = []

    if config is None:
        config = load_config()
    ai = config.ai

    # Check model
    is_model_set = bool(ai.model and ai.model != "default")
    if not is_model_set:
        missing_required_vars.append("BLINDSPOT_LLM")

    # Check API key if cloud provider
    provider = (ai.provider or "").lower()
    if provider and provider not in ("ollama", "antigravity"):
        has_key = bool(
            ai.api_key
            or os.environ.get("LLM_API_KEY")
            or os.environ.get("BLINDSPOT_API_KEY")
            or (ai.api_key_env and os.environ.get(ai.api_key_env))
        )
        if not has_key:
            missing_optional_vars.append("LLM_API_KEY")

    if not ai.base_url and provider in ("ollama", "custom"):
        missing_optional_vars.append("LLM_API_BASE")

    if missing_required_vars:
        error_text = Text()
        error_text.append("MISSING REQUIRED ENVIRONMENT VARIABLES", style="bold red")
        error_text.append("\n\n", style="white")

        for var in missing_required_vars:
            error_text.append(f"• {var}", style="bold yellow")
            error_text.append(" is not set\n", style="white")

        if missing_optional_vars:
            error_text.append("\nOptional environment variables:\n", style="dim white")
            for var in missing_optional_vars:
                error_text.append(f"• {var}", style="dim yellow")
                error_text.append(" is not set\n", style="dim white")

        error_text.append("\nRequired configuration:\n", style="white")
        error_text.append("• ", style="white")
        error_text.append("BLINDSPOT_LLM", style="bold cyan")
        error_text.append(
            " - Model route to use (e.g. 'gemini/gemini-2.5-flash', 'openai/gpt-4o-mini', 'ollama/gemma4')\n",
            style="white",
        )

        if missing_optional_vars:
            error_text.append("\nOptional environment variables:\n", style="white")
            for var in missing_optional_vars:
                if "LLM_API_KEY" in var:
                    error_text.append("• ", style="white")
                    error_text.append("LLM_API_KEY", style="bold cyan")
                    error_text.append(" - API key for your chosen model provider\n", style="white")
                elif "LLM_API_BASE" in var:
                    error_text.append("• ", style="white")
                    error_text.append("LLM_API_BASE", style="bold cyan")
                    error_text.append(" - Custom API base URL if using local models (e.g. Ollama, LMStudio)\n", style="white")

        error_text.append("\nTip: Run 'blindspot setup' for interactive guided configuration.\n", style="bold green")

        console.print()
        console.print("[bold red]✖ BLINDSPOT ENVIRONMENT ERROR[/bold red]\n")
        console.print(error_text)
        console.print()
        sys.exit(1)
