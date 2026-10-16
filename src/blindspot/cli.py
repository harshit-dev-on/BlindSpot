"""Command-line interface for BlindSpot using Typer."""

import os
from pathlib import Path
from typing import Optional
import typer
from typing_extensions import Annotated

from blindspot import __version__
from blindspot.ai import (
    DEFAULT_KEY_ENVS,
    create_provider,
    get_models_for_provider,
    mask_api_key,
)
from blindspot.ai.exceptions import AIProviderError
from blindspot.browser import inspect_website
from blindspot.config import find_config_file, load_config
from blindspot.core.models import InspectConfig
from blindspot.core.validation import validate_context, validate_url
from blindspot.personas import generate_personas_and_tasks
from blindspot.utils.console import (
    console,
    print_ai_prompt_result,
    print_browser_inspection_summary,
    print_error,
    print_inspection_start,
    print_inspection_summary,
    print_model_list,
    print_personas_summary,
    print_provider_list,
    print_provider_status,
)

app = typer.Typer(
    name="blindspot",
    help="BlindSpot: Open-source AI-powered website UX testing tool.\n\n"
    "Simulates real user personas exploring websites to uncover UX flaws, "
    "accessibility barriers, and confusing user journeys.",
    no_args_is_help=True,
    add_completion=False,
)

provider_app = typer.Typer(
    name="provider",
    help="Configure, inspect, and test AI model providers.",
    no_args_is_help=True,
)
app.add_typer(provider_app)

model_app = typer.Typer(
    name="model",
    help="Discover and list AI models.",
    no_args_is_help=True,
)
app.add_typer(model_app)

SUPPORTED_BROWSERS = ("chromium", "firefox", "webkit")


def version_callback(value: bool) -> None:
    """Print BlindSpot version and exit."""
    if value:
        typer.echo(f"BlindSpot version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        Optional[bool],
        typer.Option(
            "--version",
            "-v",
            help="Show the version of BlindSpot and exit.",
            callback=version_callback,
            is_eager=True,
        ),
    ] = None,
) -> None:
    """BlindSpot CLI entry point."""
    pass


# ─────────────────────────────────────────────────────────────────────────────
# Setup Wizard
# ─────────────────────────────────────────────────────────────────────────────


@app.command(
    name="setup",
    help="Interactive setup wizard to configure your preferred AI provider and model.",
)
def setup_command() -> None:
    """Run interactive setup wizard to configure AI provider and credentials."""
    from blindspot.cli_setup import run_setup_wizard

    try:
        run_setup_wizard()
    except (KeyboardInterrupt, typer.Abort):
        console.print("\n[yellow]Setup cancelled by user.[/yellow]")
        raise typer.Exit(code=0)


# ─────────────────────────────────────────────────────────────────────────────
# Model Discovery Commands
# ─────────────────────────────────────────────────────────────────────────────


@model_app.command(
    name="list",
    help="List discoverable and verified models for an AI provider.",
)
def model_list_command(
    provider: Annotated[
        Optional[str],
        typer.Option(
            "--provider",
            "-p",
            help="Provider to query models for (default: active provider).",
            show_default=False,
        ),
    ] = None,
    config: Annotated[
        Optional[Path],
        typer.Option(
            "--config",
            "-C",
            help="Path to custom configuration file.",
            show_default=False,
        ),
    ] = None,
) -> None:
    """Display discoverable local models or curated cloud models."""
    try:
        loaded = load_config(custom_path=config, provider=provider)
    except Exception as exc:
        print_error("Configuration Error", str(exc))
        raise typer.Exit(code=1)

    ai_cfg = loaded.ai
    selected_provider = provider.lower().strip() if provider else ai_cfg.provider
    if selected_provider == "openai_compatible":
        selected_provider = "custom"

    models = get_models_for_provider(selected_provider, base_url=ai_cfg.base_url)
    print_model_list(provider=selected_provider, models=models)


# ─────────────────────────────────────────────────────────────────────────────
# AI Provider Commands
# ─────────────────────────────────────────────────────────────────────────────


@provider_app.command(
    name="list",
    help="List supported AI providers and show active configuration.",
)
def provider_list(
    config: Annotated[
        Optional[Path],
        typer.Option(
            "--config",
            "-C",
            help="Path to custom configuration file.",
            show_default=False,
        ),
    ] = None,
) -> None:
    """Display supported AI providers and the currently active model configuration."""
    try:
        loaded = load_config(custom_path=config)
    except Exception as exc:
        print_error("Configuration Error", str(exc))
        raise typer.Exit(code=1)

    ai_cfg = loaded.ai
    config_file = find_config_file(config)
    config_source = str(config_file) if config_file else "Built-in Defaults / Environment"

    key_source = "(not required)"
    if ai_cfg.provider in ("gemini", "openai", "anthropic", "openrouter", "custom", "openai_compatible"):
        env_var_name = ai_cfg.api_key_env or DEFAULT_KEY_ENVS.get(ai_cfg.provider, "")
        env_val = os.environ.get(env_var_name)
        if env_val:
            key_source = f"env:{env_var_name} ({mask_api_key(env_val)})"
        elif ai_cfg.api_key:
            key_source = f"direct config ({mask_api_key(ai_cfg.api_key)})"
        else:
            key_source = f"env:{env_var_name} [dim](NOT SET)[/dim]"

    print_provider_list(
        active_provider=ai_cfg.provider,
        active_model=ai_cfg.model,
        active_base_url=ai_cfg.base_url or "",
        active_key_source=key_source,
        active_category=ai_cfg.category,
        config_source=config_source,
    )


@provider_app.command(
    name="test",
    help="Test connectivity and model readiness for an AI provider.",
)
def provider_test(
    provider: Annotated[
        Optional[str],
        typer.Option(
            "--provider",
            "-p",
            help="Override AI provider (ollama, gemini, openai, anthropic, openrouter, custom).",
            show_default=False,
        ),
    ] = None,
    model: Annotated[
        Optional[str],
        typer.Option(
            "--model",
            "-m",
            help="Override model name/identifier.",
            show_default=False,
        ),
    ] = None,
    base_url: Annotated[
        Optional[str],
        typer.Option(
            "--base-url",
            help="Override provider base URL.",
            show_default=False,
        ),
    ] = None,
    api_key_env: Annotated[
        Optional[str],
        typer.Option(
            "--api-key-env",
            help="Override environment variable holding the API key.",
            show_default=False,
        ),
    ] = None,
    prompt: Annotated[
        Optional[str],
        typer.Option(
            "--prompt",
            help="Optional test prompt to send to the model if reachable.",
            show_default=False,
        ),
    ] = None,
    config: Annotated[
        Optional[Path],
        typer.Option(
            "--config",
            "-C",
            help="Path to custom configuration file.",
            show_default=False,
        ),
    ] = None,
) -> None:
    """Verify endpoint reachability, model existence, and test prompt response."""
    try:
        loaded = load_config(
            custom_path=config,
            provider=provider,
            model=model,
            base_url=base_url,
            api_key_env=api_key_env,
        )
    except Exception as exc:
        print_error("Configuration Error", str(exc))
        raise typer.Exit(code=1)

    ai_cfg = loaded.ai
    console.print(
        f"[bold cyan]→[/bold cyan] Testing provider [bold]{ai_cfg.provider}[/bold] with model [bold]{ai_cfg.model}[/bold]..."
    )

    try:
        p = create_provider(ai_cfg)
        status = p.check_health()
    except AIProviderError as exc:
        print_error("Provider Setup Error", exc.message, exc.suggestion)
        raise typer.Exit(code=1)
    except Exception as exc:
        print_error("Provider Error", str(exc))
        raise typer.Exit(code=1)

    print_provider_status(
        provider=status.provider,
        model=status.model,
        base_url=status.base_url,
        is_reachable=status.is_reachable,
        model_available=status.model_available,
        latency_ms=status.latency_ms,
        message=status.message,
    )

    if not status.is_reachable or not status.model_available:
        raise typer.Exit(code=1)

    # Run verification prompt
    test_prompt = prompt or "Say hello in one brief sentence to confirm you are online."
    console.print(f"[bold cyan]→[/bold cyan] Sending test verification prompt: [dim]\"{test_prompt}\"[/dim]")

    try:
        response = p.generate(prompt=test_prompt)
        print_ai_prompt_result(
            prompt=test_prompt,
            model=response.model,
            provider=response.provider,
            content=response.content.strip(),
        )
    except AIProviderError as exc:
        print_error("Model Generation Failed", exc.message, exc.suggestion)
        raise typer.Exit(code=1)
    except Exception as exc:
        print_error("Generation Error", str(exc))
        raise typer.Exit(code=1)


@provider_app.command(
    name="prompt",
    help="Send a prompt directly to the configured AI model.",
)
def provider_prompt(
    text: Annotated[
        str,
        typer.Argument(
            help="Prompt text to send to the model.",
        ),
    ],
    provider: Annotated[
        Optional[str],
        typer.Option(
            "--provider",
            "-p",
            help="Override AI provider (ollama, gemini, openai, anthropic, openrouter, custom).",
        ),
    ] = None,
    model: Annotated[
        Optional[str],
        typer.Option(
            "--model",
            "-m",
            help="Override model name/identifier.",
        ),
    ] = None,
    base_url: Annotated[
        Optional[str],
        typer.Option(
            "--base-url",
            help="Override provider base URL.",
        ),
    ] = None,
    system: Annotated[
        Optional[str],
        typer.Option(
            "--system",
            "-s",
            help="Optional system prompt instructions.",
        ),
    ] = None,
    config: Annotated[
        Optional[Path],
        typer.Option(
            "--config",
            "-C",
            help="Path to custom configuration file.",
        ),
    ] = None,
) -> None:
    """Send a user prompt to the configured model and display the response."""
    try:
        loaded = load_config(
            custom_path=config,
            provider=provider,
            model=model,
            base_url=base_url,
        )
        ai_cfg = loaded.ai
        p = create_provider(ai_cfg)
    except Exception as exc:
        print_error("Configuration Error", str(exc))
        raise typer.Exit(code=1)

    console.print(
        f"[bold cyan]→[/bold cyan] Querying [bold]{ai_cfg.provider}[/bold] ({ai_cfg.model})..."
    )

    try:
        response = p.generate(prompt=text, system_prompt=system)
        print_ai_prompt_result(
            prompt=text,
            model=response.model,
            provider=response.provider,
            content=response.content.strip(),
        )
    except AIProviderError as exc:
        print_error("AI Generation Error", exc.message, exc.suggestion)
        raise typer.Exit(code=1)
    except Exception as exc:
        print_error("AI Error", str(exc))
        raise typer.Exit(code=1)


# ─────────────────────────────────────────────────────────────────────────────
# Browser Inspection Command
# ─────────────────────────────────────────────────────────────────────────────


@app.command(
    name="inspect",
    help="Inspect a target website using browser automation.\n\n"
    "Navigates to the website with Playwright, captures interactive elements, "
    "page content, full-page screenshot, and structured inspection data.",
    no_args_is_help=True,
)
def inspect(
    url: Annotated[
        str,
        typer.Option(
            "--url",
            "-u",
            help="Target website URL to test (e.g. https://example.com).",
            show_default=False,
        ),
    ],
    context: Annotated[
        str,
        typer.Option(
            "--context",
            "-c",
            help="Context describing website purpose & audience, or path to text file.",
            show_default=False,
        ),
    ],
    output_dir: Annotated[
        Optional[Path],
        typer.Option(
            "--output-dir",
            "-o",
            help="Custom directory to store artifacts (default: unique folder in reports/).",
            show_default=False,
        ),
    ] = None,
    browser: Annotated[
        str,
        typer.Option(
            "--browser",
            "-b",
            help="Browser engine to use: chromium, firefox, webkit.",
            show_default=True,
        ),
    ] = "chromium",
    headless: Annotated[
        bool,
        typer.Option(
            "--headless/--no-headless",
            help="Run browser in headless mode or visible window.",
            show_default=True,
        ),
    ] = True,
    headed: Annotated[
        bool,
        typer.Option(
            "--headed",
            help="Run browser in visible window (alias for --no-headless).",
            show_default=False,
        ),
    ] = False,
    personas: Annotated[
        int,
        typer.Option(
            "--personas",
            "-p",
            help="Number of AI user personas to generate (default: 3).",
            show_default=True,
        ),
    ] = 3,
    skip_ai: Annotated[
        bool,
        typer.Option(
            "--skip-ai",
            help="Skip AI persona generation (browser inspection only).",
            show_default=False,
        ),
    ] = False,
    ai_provider: Annotated[
        Optional[str],
        typer.Option(
            "--ai-provider",
            help="Override AI provider for persona generation (e.g. ollama, gemini, openai).",
            show_default=False,
        ),
    ] = None,
    ai_model: Annotated[
        Optional[str],
        typer.Option(
            "--ai-model",
            help="Override AI model identifier for persona generation.",
            show_default=False,
        ),
    ] = None,
) -> None:
    """Run website inspection, capture page state, screenshot, elements, and synthesize AI personas."""
    # Determine effective headless mode
    effective_headless = False if headed else headless

    # 1. Validate Target URL
    url_res = validate_url(url)
    if not url_res.is_valid:
        print_error(
            title="Invalid URL Provided",
            message=url_res.error_message or "Invalid URL.",
            suggestion=url_res.suggestion,
        )
        raise typer.Exit(code=1)

    # 2. Validate Context Description
    context_res, resolved_context = validate_context(context)
    if not context_res.is_valid:
        print_error(
            title="Invalid Context Provided",
            message=context_res.error_message or "Invalid Context.",
            suggestion=context_res.suggestion,
        )
        raise typer.Exit(code=1)

    # 3. Validate Browser Choice
    selected_browser = browser.lower().strip()
    if selected_browser not in SUPPORTED_BROWSERS:
        print_error(
            title="Invalid Browser Selected",
            message=f"Browser engine '{browser}' is not supported.",
            suggestion=f"Please choose one of: {', '.join(SUPPORTED_BROWSERS)} (e.g. --browser chromium).",
        )
        raise typer.Exit(code=1)

    # 4. Display Input Validation Summary
    config = InspectConfig(url=url.strip(), context=resolved_context)
    print_inspection_summary(url=config.url, context=config.context)
    print_inspection_start(url=config.url, browser=selected_browser)

    # 5. Launch Browser Inspection
    try:
        result = inspect_website(
            url=config.url,
            context=config.context,
            output_dir=output_dir,
            browser_type=selected_browser,
            headless=effective_headless,
        )
    except Exception as exc:
        print_error(
            title="Browser Inspection Failed",
            message=str(exc),
            suggestion="Verify the URL is accessible. If browser binaries are missing, run 'playwright install chromium'.",
        )
        raise typer.Exit(code=1)

    # 6. Display Browser Result Summary
    print_browser_inspection_summary(
        title=result.title,
        final_url=result.final_url,
        viewport_width=result.viewport.width,
        viewport_height=result.viewport.height,
        browser=result.browser,
        total_elements=result.summary.total_interactive_elements,
        links_count=result.summary.links_count,
        buttons_count=result.summary.buttons_count,
        form_fields_count=result.summary.form_fields_count,
        text_length=result.summary.text_length,
        screenshot_path=result.screenshot_path,
        result_json_path=result.result_json_path,
    )

    # 7. AI Persona Synthesis and Task Planning
    if skip_ai:
        console.print("[dim]AI persona synthesis skipped (--skip-ai flag provided).[/dim]")
        return

    console.print("\n[bold cyan]→[/bold cyan] Initializing AI model for persona generation...")
    try:
        loaded_cfg = load_config(provider=ai_provider, model=ai_model)
        ai_cfg = loaded_cfg.ai
        effective_model = (
            ai_model
            or (ai_cfg.tasks.persona_generation if ai_cfg.tasks else None)
            or ai_cfg.model
        )
        effective_cfg = ai_cfg.model_copy(update={"model": effective_model})
        provider_instance = create_provider(effective_cfg)
    except Exception as exc:
        print_error(
            title="AI Configuration Error",
            message=f"Could not initialize AI provider: {exc}",
            suggestion="Run 'blindspot setup' to configure an AI provider or pass '--skip-ai' to perform browser inspection only.",
        )
        raise typer.Exit(code=1)

    console.print(
        f"[bold cyan]→[/bold cyan] Synthesizing [bold]{personas}[/bold] AI personas & tasks using [bold]{provider_instance.name}[/bold] ({provider_instance.model})..."
    )

    try:
        run_output_dir = Path(result.result_json_path).parent if result.result_json_path else output_dir
        plan = generate_personas_and_tasks(
            inspection_result=result,
            provider=provider_instance,
            num_personas=personas,
            output_dir=run_output_dir,
        )
        print_personas_summary(plan)
    except AIProviderError as exc:
        print_error(
            title="AI Persona Generation Failed",
            message=exc.message,
            suggestion=exc.suggestion or "Verify your API key, local model status, or network connection. Re-run 'blindspot setup'.",
        )
        raise typer.Exit(code=1)
    except Exception as exc:
        print_error(
            title="Persona Synthesis Error",
            message=str(exc),
            suggestion="Verify model output schema compliance or run with '--skip-ai'.",
        )
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
