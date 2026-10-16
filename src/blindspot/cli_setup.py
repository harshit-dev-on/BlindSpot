"""Interactive setup wizard for configuring universal AI providers."""

from pathlib import Path
from typing import List, Optional
import typer
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from blindspot.ai.adapter import (
    CURATED_MODELS,
    DEFAULT_BASE_URLS,
    DEFAULT_KEY_ENVS,
    DEFAULT_PROVIDER_MODELS,
    UnifiedAIAdapter,
    get_models_for_provider,
)
from blindspot.config.loader import get_user_config_path, save_config
from blindspot.config.models import AIConfig, BlindSpotConfig
from blindspot.utils.console import console, print_error, print_provider_status


def run_setup_wizard() -> None:
    """Run an interactive terminal wizard to configure BlindSpot's AI engine."""
    console.print(
        Panel(
            "[bold white]Welcome to the BlindSpot AI Setup Wizard![/bold white]\n\n"
            "BlindSpot works with local runtimes (like [cyan]Ollama[/cyan] running [cyan]Gemma 4[/cyan]), "
            "major cloud APIs ([cyan]Google Gemini[/cyan], [cyan]OpenAI[/cyan], [cyan]Anthropic[/cyan]), "
            "and custom self-hosted endpoints.",
            title="[bold blue]BlindSpot AI Setup[/bold blue]",
            border_style="blue",
            padding=(1, 2),
        )
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Step 1: Select Category
    # ─────────────────────────────────────────────────────────────────────────
    console.print("\n[bold cyan]Step 1 of 5: Choose AI Deployment Category[/bold cyan]")
    console.print("  [bold]1[/bold]) [green]Local AI[/green]      - Completely private, free & offline (e.g. Ollama with Gemma 4)")
    console.print("  [bold]2[/bold]) [blue]Cloud API[/blue]     - Fast, highly capable hosted models (Google Gemini, OpenAI, Claude)")
    console.print("  [bold]3[/bold]) [yellow]Custom API[/yellow]    - Self-hosted or proxy endpoint (vLLM, LM Studio, LocalAI)")
    console.print("  [bold]4[/bold]) [magenta]Hybrid[/magenta]        - Local inference for tasks + Cloud for deep UX analysis")

    category_choice = Prompt.ask(
        "Select category",
        choices=["1", "2", "3", "4"],
        default="1",
    )

    category_map = {
        "1": "local",
        "2": "cloud",
        "3": "custom",
        "4": "hybrid",
    }
    category = category_map[category_choice]

    # ─────────────────────────────────────────────────────────────────────────
    # Step 2: Select Provider
    # ─────────────────────────────────────────────────────────────────────────
    console.print(f"\n[bold cyan]Step 2 of 5: Select Provider for '{category.upper()}'[/bold cyan]")

    provider = "ollama"
    if category == "local":
        console.print("Using [bold green]Ollama[/bold green] (local model engine).")
        provider = "ollama"

    elif category == "cloud":
        console.print("  [bold]1[/bold]) [cyan]Google Gemini API[/cyan]  - High-performance, large context window (Recommended)")
        console.print("  [bold]2[/bold]) [white]OpenAI[/white]             - GPT-4o, GPT-4o-mini, o3-mini")
        console.print("  [bold]3[/bold]) [yellow]Anthropic Claude[/yellow]   - Claude 3.5 Sonnet, Claude 3.5 Haiku")
        console.print("  [bold]4[/bold]) [blue]OpenRouter[/blue]         - Multi-provider gateway")

        cloud_choice = Prompt.ask("Select cloud provider", choices=["1", "2", "3", "4"], default="1")
        cloud_map = {
            "1": "gemini",
            "2": "openai",
            "3": "anthropic",
            "4": "openrouter",
        }
        provider = cloud_map[cloud_choice]

    elif category == "custom":
        console.print("Configuring custom OpenAI-compatible endpoint.")
        provider = "custom"

    elif category == "hybrid":
        console.print("Hybrid mode: Ollama will be primary; cloud analysis can be configured.")
        provider = "ollama"

    # ─────────────────────────────────────────────────────────────────────────
    # Step 3: Configure Model
    # ─────────────────────────────────────────────────────────────────────────
    console.print(f"\n[bold cyan]Step 3 of 5: Select Model for {provider.upper()}[/bold cyan]")

    curated = get_models_for_provider(provider)
    if curated:
        console.print("Suggested models:")
        for idx, m in enumerate(curated[:5], start=1):
            console.print(f"  [bold]{idx}[/bold]) [white]{m}[/white]")
        console.print(f"  [bold]{len(curated[:5]) + 1}[/bold]) [dim]Custom model name[/dim]")

        choices = [str(i) for i in range(1, len(curated[:5]) + 2)]
        m_choice = Prompt.ask("Select model", choices=choices, default="1")

        idx_choice = int(m_choice) - 1
        if idx_choice < len(curated[:5]):
            model = curated[idx_choice]
        else:
            model = Prompt.ask("Enter model name", default=DEFAULT_PROVIDER_MODELS.get(provider, "default"))
    else:
        default_model = DEFAULT_PROVIDER_MODELS.get(provider, "default")
        model = Prompt.ask("Enter model identifier", default=default_model)

    # Base URL (only prompt if custom or if user desires custom endpoint)
    base_url = None
    if provider == "custom":
        base_url = Prompt.ask("Enter API base URL", default="http://localhost:8000/v1")
    elif provider == "ollama":
        use_custom_url = Confirm.ask("Use default Ollama endpoint (http://localhost:11434)?", default=True)
        if not use_custom_url:
            base_url = Prompt.ask("Enter Ollama endpoint URL", default="http://localhost:11434")

    # ─────────────────────────────────────────────────────────────────────────
    # Step 4: Authentication & Credentials (if needed)
    # ─────────────────────────────────────────────────────────────────────────
    api_key = None
    api_key_env = DEFAULT_KEY_ENVS.get(provider)

    if provider in ("gemini", "openai", "anthropic", "openrouter", "custom"):
        console.print(f"\n[bold cyan]Step 4 of 5: Credentials for {provider.upper()}[/bold cyan]")
        console.print(f"BlindSpot reads credentials from environment variable: [bold yellow]{api_key_env}[/bold yellow]")
        console.print("  [bold]1[/bold]) Read from environment variable at runtime [dim](Recommended - keeps secrets out of files)[/dim]")
        console.print("  [bold]2[/bold]) Enter API key now [dim](Stored securely in user config)[/dim]")

        cred_choice = Prompt.ask("Choose credential option", choices=["1", "2"], default="1")
        if cred_choice == "2":
            entered_key = typer.prompt(
                f"Enter your {provider.upper()} API Key",
                hide_input=True,
            )
            if entered_key.strip():
                api_key = entered_key.strip()
                console.print("[green]✔ API key captured securely (hidden from terminal display).[/green]")

    else:
        console.print("\n[bold cyan]Step 4 of 5: Credentials[/bold cyan]")
        console.print("[green]✔ No API key required for local Ollama.[/green]")

    # Build prospective config
    ai_config = AIConfig(
        category=category,
        provider=provider,
        model=model,
        base_url=base_url,
        api_key=api_key,
        api_key_env=api_key_env,
    )
    blindspot_config = BlindSpotConfig(ai=ai_config)

    # ─────────────────────────────────────────────────────────────────────────
    # Step 5: Test Connection & Save
    # ─────────────────────────────────────────────────────────────────────────
    console.print(f"\n[bold cyan]Step 5 of 5: Verification & Persistence[/bold cyan]")
    test_now = Confirm.ask("Test provider connection right now?", default=True)

    if test_now:
        console.print(f"[bold cyan]→[/bold cyan] Testing connection to [bold]{provider}[/bold] ({model})...")
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

        if not status.is_reachable:
            save_anyway = Confirm.ask(
                "Connection failed. Do you want to save this configuration anyway?",
                default=True,
            )
            if not save_anyway:
                console.print("[yellow]Setup cancelled. No configuration was written.[/yellow]")
                return

    saved_path = save_config(blindspot_config)

    # ─────────────────────────────────────────────────────────────────────────
    # Summary & Next Steps
    # ─────────────────────────────────────────────────────────────────────────
    console.print(
        Panel(
            f"[bold green]✔ Configuration saved successfully![/bold green]\n\n"
            f"[bold]Saved to:[/bold] [underline]{saved_path}[/underline]\n"
            f"[bold]Active Provider:[/bold] {provider}\n"
            f"[bold]Active Model:[/bold] {model}\n\n"
            "[bold white]How to change or test your configuration later:[/bold white]\n"
            "• Re-run the wizard anytime: [cyan]blindspot setup[/cyan]\n"
            "• Test connectivity: [cyan]blindspot provider test[/cyan]\n"
            "• List discovered models: [cyan]blindspot model list[/cyan]\n"
            "• Send a quick test prompt: [cyan]blindspot provider prompt \"Hello!\"[/cyan]\n"
            f"• Directly edit your configuration file: [dim]{saved_path}[/dim]",
            title="[bold green]BlindSpot Ready[/bold green]",
            border_style="green",
            padding=(1, 2),
        )
    )
