"""Interactive setup wizard and model preflight connection verification for BlindSpot."""

import os
from pathlib import Path
from typing import Optional
import typer
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from blindspot.ai.adapter import (
    DEFAULT_KEY_ENVS,
    DEFAULT_PROVIDER_MODELS,
    UnifiedAIAdapter,
)
from blindspot.config.loader import (
    get_user_config_path,
    load_config,
    parse_model_route,
    save_config,
)
from blindspot.config.models import AIConfig, BlindSpotConfig
from blindspot.utils.console import console, print_error, print_provider_status


def preflight_model_connection(
    provider: str,
    model: str,
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    api_key_env: Optional[str] = None,
) -> bool:
    """Perform preflight health check on an AI model provider connection.

    Returns:
        True if the connection is reachable and verified, False otherwise.
    """
    console.print(f"\n[bold cyan]→[/bold cyan] Verifying connection to [bold]{provider}[/bold] ({model})...")
    adapter = UnifiedAIAdapter(
        provider=provider,
        model=model,
        base_url=base_url,
        api_key=api_key,
        api_key_env=api_key_env,
    )
    status = adapter.check_health()
    print_provider_status(
        provider=status.provider,
        model=status.model,
        base_url=status.base_url,
        is_reachable=status.is_reachable,
        model_available=status.model_available,
        latency_ms=status.latency_ms,
        message=status.message,
    )
    return status.is_reachable


def run_setup_wizard() -> None:
    """Run a streamlined setup wizard for BlindSpot."""
    # Load existing config to offer smart defaults
    existing_cfg = load_config()
    p = existing_cfg.ai.provider or "gemini"
    m = existing_cfg.ai.model or "gemini-2.5-flash"
    if m in ("default", "gemini-3.5-flash") or not m:
        m = "gemini-2.5-flash"
    current_route = f"{p}/{m}"

    console.print(
        Panel(
            "[bold white]BlindSpot AI Setup[/bold white]\n\n"
            "Configure your model in standard [cyan]<provider>/<model>[/cyan] format.\n\n"
            "[dim]Popular models:\n"
            "  • [bold cyan]gemini/gemini-2.5-flash[/bold cyan] (or google/gemini-2.5-flash) [Recommended]\n"
            "  • [bold white]openai/gpt-4o-mini[/bold white]\n"
            "  • [bold yellow]anthropic/claude-3-7-sonnet[/bold yellow]\n"
            "  • [bold green]ollama/gemma4[/bold green] (Local, free & private)\n"
            "  • [bold blue]openrouter/meta-llama/llama-3.1-8b-instruct[/bold blue][/dim]",
            title="[bold cyan]BlindSpot[/bold cyan]",
            title_align="left",
            border_style="cyan",
            padding=(1, 2),
        )
    )

    # 1. Model Route Prompt
    model_route = Prompt.ask(
        "[bold]Model Route[/bold] (<provider>/<model>)",
        default=current_route,
    )

    category, provider, model = parse_model_route(model_route)

    # 2. API Key Prompt (if cloud provider)
    api_key = existing_cfg.ai.api_key
    api_key_env = DEFAULT_KEY_ENVS.get(provider, "LLM_API_KEY")

    if provider != "ollama":
        env_val = os.environ.get(api_key_env) or os.environ.get("LLM_API_KEY")
        has_existing = bool(api_key or env_val)

        console.print(f"\nProvider [bold]{provider.upper()}[/bold] requires an API key (reads from [cyan]{api_key_env}[/cyan] or [cyan]LLM_API_KEY[/cyan]).")
        if has_existing:
            console.print("[dim]An API key was detected in your environment/config. Press Enter to keep it.[/dim]")

        entered_key = typer.prompt(
            f"Enter {provider.upper()} API Key",
            default="" if has_existing else None,
            show_default=False,
            hide_input=True,
        )
        if entered_key and entered_key.strip():
            api_key = entered_key.strip()
    else:
        api_key = None
        console.print("\n[green]✓ Local Ollama requires no API key.[/green]")

    # 3. Base URL (optional for Ollama or custom)
    base_url = existing_cfg.ai.base_url
    if provider == "ollama" and not base_url:
        base_url = "http://localhost:11434"

    # Construct prospective configuration
    ai_config = AIConfig(
        category=category,
        provider=provider,
        model=model,
        base_url=base_url,
        api_key=api_key,
        api_key_env=api_key_env,
    )
    blindspot_config = BlindSpotConfig(ai=ai_config)

    # 4. Instant Preflight Check
    is_reachable = preflight_model_connection(
        provider=provider,
        model=model,
        base_url=base_url,
        api_key=api_key,
        api_key_env=api_key_env,
    )

    if not is_reachable:
        save_anyway = Confirm.ask(
            "\nConnection could not be verified. Save configuration anyway?",
            default=True,
        )
        if not save_anyway:
            console.print("[yellow]Setup cancelled. Configuration was not saved.[/yellow]")
            return

    # Save
    saved_path = save_config(blindspot_config)

    console.print(
        Panel(
            f"[bold green]✓ BlindSpot successfully configured![/bold green]\n\n"
            f"[bold]Active Route:[/bold] [cyan]{provider}/{model}[/cyan]\n"
            f"[bold]Saved to:[/bold] [dim]{saved_path}[/dim]\n\n"
            "[bold white]Ready to test:[/bold white]\n"
            f"  • Quick scan:     [cyan]blindspot --target https://example.com[/cyan]\n"
            f"  • Verify status:  [cyan]blindspot provider test[/cyan]\n"
            f"  • Launch studio:  [cyan]blindspot web[/cyan]",
            title="[bold green]Ready[/bold green]",
            title_align="left",
            border_style="green",
            padding=(1, 2),
        )
    )
