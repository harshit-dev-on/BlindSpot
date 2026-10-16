"""Command-line interface for BlindSpot using Typer."""

from pathlib import Path
from typing import Optional
import typer
from typing_extensions import Annotated

from blindspot import __version__
from blindspot.ai import create_provider
from blindspot.ai.exceptions import AIProviderError
from blindspot.browser import inspect_website
from blindspot.config import find_config_file, load_config
from blindspot.core.models import InspectConfig
from blindspot.core.validation import validate_context, validate_url
from blindspot.utils.console import (
    console,
    print_ai_prompt_result,
    print_browser_inspection_summary,
    print_error,
    print_inspection_start,
    print_inspection_summary,
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
    if ai_cfg.provider == "openai_compatible":
        import os
        from blindspot.ai.providers.openai_compatible import mask_api_key

        env_val = os.environ.get(ai_cfg.api_key_env or "")
        if env_val:
            key_source = f"env:{ai_cfg.api_key_env} ({mask_api_key(env_val)})"
        elif ai_cfg.api_key:
            key_source = f"direct config ({mask_api_key(ai_cfg.api_key)})"
        else:
            key_source = f"env:{ai_cfg.api_key_env} [dim](NOT SET)[/dim]"

    print_provider_list(
        active_provider=ai_cfg.provider,
        active_model=ai_cfg.model,
        active_base_url=ai_cfg.base_url or "",
        active_key_source=key_source,
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
            help="Override AI provider (ollama, openai_compatible).",
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

    # If prompt requested, or run a simple verification prompt
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
            help="Override AI provider (ollama, openai_compatible).",
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
) -> None:
    """Run website inspection, capture page state, screenshot, and elements."""
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

    # 6. Display Result Summary
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


if __name__ == "__main__":
    app()
