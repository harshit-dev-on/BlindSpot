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
from blindspot.execution import execute_persona_tasks
from blindspot.personas import generate_personas_and_tasks
from blindspot.reporting import generate_ux_report
from blindspot.skills import (
    get_bundled_skills_dir,
    install_skills_to_workspace,
    list_bundled_skills,
    validate_skill,
)
from blindspot.utils.console import (
    console,
    print_ai_prompt_result,
    print_browser_inspection_summary,
    print_error,
    print_execution_summary,
    print_inspection_start,
    print_inspection_summary,
    print_model_list,
    print_personas_summary,
    print_provider_list,
    print_provider_status,
    print_report_summary,
    print_skills_installed,
    print_skills_list,
    print_skills_validation_results,
)

app = typer.Typer(
    name="blindspot",
    help="BlindSpot: Open-source AI-powered website UX testing tool.\n\n"
    "Simulates real user personas exploring websites to uncover UX flaws, "
    "accessibility barriers, and confusing user journeys.",
    no_args_is_help=False,
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

skill_app = typer.Typer(
    name="skill",
    help="Manage, list, validate, and install Agent Skills following the open specification.",
    no_args_is_help=True,
)
app.add_typer(skill_app)

SUPPORTED_BROWSERS = ("chromium", "firefox", "webkit")


def version_callback(value: bool) -> None:
    """Print BlindSpot version and exit."""
    if value:
        typer.echo(f"BlindSpot version {__version__}")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    target: Annotated[
        Optional[str],
        typer.Option(
            "--target",
            "-t",
            help="Target website URL to test (e.g. https://example.com).",
            show_default=False,
        ),
    ] = None,
    url: Annotated[
        Optional[str],
        typer.Option(
            "--url",
            "-u",
            help="Alias for --target.",
            show_default=False,
        ),
    ] = None,
    instruction: Annotated[
        Optional[str],
        typer.Option(
            "--instruction",
            "-i",
            help="Custom focus or instruction for testing.",
            show_default=False,
        ),
    ] = None,
    context: Annotated[
        Optional[str],
        typer.Option(
            "--context",
            "-c",
            help="Alias for --instruction.",
            show_default=False,
        ),
    ] = None,
    headed: Annotated[
        bool,
        typer.Option(
            "--headed",
            help="Run browser in visible window.",
            show_default=False,
        ),
    ] = False,
    allow_local: Annotated[
        bool,
        typer.Option(
            "--allow-local",
            help="Permit testing local loopback servers (localhost / 127.0.0.1).",
            show_default=False,
        ),
    ] = False,
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
    if ctx.invoked_subcommand is not None:
        return

    effective_target = target or url
    effective_instruction = instruction or context

    if effective_target:
        inspect(
            url=effective_target,
            context=effective_instruction,
            headed=headed,
            allow_local=allow_local,
        )
        return

    # If bare `blindspot` command is run:
    # Launch Strix-style interactive start screen
    from blindspot.interface.interactive import show_interactive_start_screen
    chosen_target, chosen_instruction = show_interactive_start_screen()
    if not chosen_target:
        from blindspot.web import run_web_studio
        console.print("[bold cyan]→[/bold cyan] Launching BlindSpot Web Studio...")
        run_web_studio(port=8501, host="127.0.0.1")
        return

    inspect(
        url=chosen_target,
        context=chosen_instruction,
        headed=headed,
        allow_local=allow_local,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Setup Wizard
# ─────────────────────────────────────────────────────────────────────────────


@app.command(
    name="setup",
    help="Interactive setup wizard to configure your preferred AI provider and model.",
)
def setup_command() -> None:
    """Run interactive setup wizard to configure AI provider and credentials."""
    from blindspot.interface.scan_setup import run_setup_wizard

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
        Optional[str],
        typer.Option(
            "--url",
            "-u",
            help="Target website URL to test (e.g. https://example.com).",
            show_default=False,
        ),
    ] = None,
    target: Annotated[
        Optional[str],
        typer.Option(
            "--target",
            "-t",
            help="Alias for --url (Strix standard).",
            show_default=False,
        ),
    ] = None,
    context: Annotated[
        Optional[str],
        typer.Option(
            "--context",
            "-c",
            help="Context describing website purpose & audience, or path to text file.",
            show_default=False,
        ),
    ] = None,
    instruction: Annotated[
        Optional[str],
        typer.Option(
            "--instruction",
            "-i",
            help="Alias for --context (Strix standard).",
            show_default=False,
        ),
    ] = None,
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
    skip_execution: Annotated[
        bool,
        typer.Option(
            "--skip-execution",
            help="Skip browser task execution (only inspect and synthesize plan).",
            show_default=False,
        ),
    ] = False,
    max_actions: Annotated[
        int,
        typer.Option(
            "--max-actions",
            help="Maximum actions per persona task to prevent loops.",
            show_default=True,
        ),
    ] = 8,
    skip_report: Annotated[
        bool,
        typer.Option(
            "--skip-report",
            help="Skip JSON and HTML UX report generation.",
            show_default=False,
        ),
    ] = False,
    allow_local: Annotated[
        bool,
        typer.Option(
            "--allow-local",
            help="Permit testing local loopback servers (localhost / 127.0.0.1).",
            show_default=False,
        ),
    ] = False,
) -> None:
    """Run website inspection, capture page state, screenshot, elements, and synthesize AI personas."""
    # Determine effective headless mode
    effective_headless = False if headed else headless

    # Determine effective target and context
    effective_url = target or url
    if not effective_url:
        print_error(
            title="Missing Target URL",
            message="Target website URL was not provided.",
            suggestion="Specify a target using --target or --url (e.g. blindspot --target https://example.com).",
        )
        raise typer.Exit(code=1)

    effective_context = (
        instruction
        or context
        or "Autonomous exploration of user journeys, interface accessibility, and usability."
    )

    # 1. Validate Target URL
    url_res = validate_url(effective_url)
    if not url_res.is_valid:
        print_error(
            title="Invalid URL Provided",
            message=url_res.error_message or "Invalid URL.",
            suggestion=url_res.suggestion,
        )
        raise typer.Exit(code=1)

    # SSRF & Private Network Security Check
    from blindspot.execution.safety import validate_navigation_url
    is_safe, ssrf_reason = validate_navigation_url(effective_url, allow_local=allow_local)
    if not is_safe:
        print_error(
            title="Security Policy Blocked URL",
            message=ssrf_reason or "Target URL failed safety policies.",
            suggestion="Target URL must be a publicly accessible HTTP/HTTPS address, or pass '--allow-local' if testing a local development server.",
        )
        raise typer.Exit(code=1)

    # 2. Validate Context Description
    context_res, resolved_context = validate_context(effective_context)
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
    config = InspectConfig(url=effective_url.strip(), context=resolved_context)
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
            allow_local=allow_local,
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

    # 8. Automated Browser Task Execution
    execution_result = None
    if skip_execution:
        console.print("[dim]Persona task execution skipped (--skip-execution flag provided).[/dim]")
    else:
        console.print(
            f"\n[bold cyan]→[/bold cyan] Launching automated browser execution for [bold]{len(plan.personas)}[/bold] personas across isolated sessions..."
        )

        try:
            execution_result = execute_persona_tasks(
                plan=plan,
                provider=provider_instance,
                output_dir=run_output_dir or Path(result.result_json_path).parent,
                browser_type=selected_browser,
                headless=effective_headless,
                max_actions_per_task=max_actions,
                allow_local=allow_local,
            )
            print_execution_summary(execution_result)
        except Exception as exc:
            print_error(
                title="Browser Task Execution Error",
                message=str(exc),
                suggestion="Check browser reachability or try running with '--skip-execution'.",
            )
            raise typer.Exit(code=1)

    # 9. Evidence Aggregation, UX Analysis, and Report Generation
    if skip_report:
        console.print("[dim]UX report generation skipped (--skip-report flag provided).[/dim]")
        return

    console.print("\n[bold cyan]→[/bold cyan] Aggregating evidence and generating UX reports...")
    try:
        report, json_path, html_path = generate_ux_report(
            inspection_result=result,
            plan=plan,
            execution_result=execution_result,
            provider=provider_instance,
            output_dir=run_output_dir or Path(result.result_json_path).parent,
            context=resolved_context,
        )
        print_report_summary(
            report_id=report.report_id,
            target_url=report.target_url,
            total_tasks=report.task_metrics.total_tasks,
            passed_tasks=report.task_metrics.passed_tasks,
            failed_tasks=report.task_metrics.failed_tasks,
            verified_issues=report.verified_issues_count,
            usability_observations=report.usability_observations_count,
            potential_improvements=report.potential_improvements_count,
            json_path=json_path,
            html_path=html_path,
            top_findings=report.findings,
        )
    except Exception as exc:
        print_error(
            title="Report Generation Error",
            message=str(exc),
            suggestion="Verify directory write permissions or check previous task logs.",
        )
        raise typer.Exit(code=1)


@app.command(
    name="web",
    help="Launch the interactive BlindSpot web demonstration studio.",
)
def web(
    host: Annotated[
        str,
        typer.Option(
            "--host",
            "-h",
            help="Host address to bind the web server to.",
            show_default=True,
        ),
    ] = "127.0.0.1",
    port: Annotated[
        int,
        typer.Option(
            "--port",
            "-p",
            help="TCP port to listen on.",
            show_default=True,
        ),
    ] = 8000,
    open_browser: Annotated[
        bool,
        typer.Option(
            "--open/--no-open",
            help="Automatically open the web demonstration interface in your browser.",
            show_default=True,
        ),
    ] = True,
    reload: Annotated[
        bool,
        typer.Option(
            "--reload",
            help="Enable auto-reload for local development.",
            show_default=False,
        ),
    ] = False,
) -> None:
    """Launch the interactive BlindSpot web demonstration server."""
    try:
        import uvicorn
        from rich.panel import Panel
        from blindspot.web.app import app as fastapi_app
    except ImportError as exc:
        print_error(
            title="Web Dependencies Missing",
            message=f"The BlindSpot web demonstration requires 'fastapi' and 'uvicorn' ({exc}).",
            suggestion="Install them with:\n    pip install \"blindspot[web]\"\nor:\n    pip install fastapi uvicorn",
        )
        raise typer.Exit(code=1)

    url = f"http://{host}:{port}"
    console.print(
        Panel(
            f"[bold cyan]BlindSpot UX Testing Studio[/bold cyan]\n\n"
            f"• Local URL:   [bold green]{url}[/bold green]\n"
            f"• API Docs:    [dim]{url}/docs[/dim]\n"
            f"• Bound Host:  [dim]{host}[/dim]\n"
            f"• Port:        [dim]{port}[/dim]\n\n"
            f"[italic dim]Press Ctrl+C to stop the web server.[/italic dim]",
            title="[bold white] Web Server Online [/bold white]",
            border_style="cyan",
            expand=False,
        )
    )

    if open_browser:
        import webbrowser
        try:
            webbrowser.open(url)
        except Exception:
            pass

    uvicorn.run("blindspot.web.app:app", host=host, port=port, reload=reload)


@app.command(
    name="mcp",
    help="Launch the BlindSpot Model Context Protocol (MCP) server for AI coding agents.",
)
def mcp_cmd(
    transport: Annotated[
        str,
        typer.Option(
            "--transport",
            "-t",
            help="Transport mechanism: 'stdio' (default for AI coding agents) or 'sse'.",
            show_default=True,
        ),
    ] = "stdio",
) -> None:
    """Launch the BlindSpot MCP server for local AI coding agent pair programming."""
    try:
        from blindspot.mcp.server import run_mcp_server
    except ImportError as exc:
        print_error(
            title="MCP Dependencies Missing",
            message=f"The BlindSpot MCP server requires the official 'mcp' SDK ({exc}).",
            suggestion="Install with:\n    pip install \"blindspot[mcp]\"\nor:\n    pip install mcp",
        )
        raise typer.Exit(code=1)

    run_mcp_server(transport=transport)


@skill_app.command(
    name="list",
    help="List all packaged BlindSpot Agent Skills available for AI coding agents.",
)
def list_skills_cmd() -> None:
    """List all bundled Agent Skills conforming to the open standard."""
    skills = list_bundled_skills()
    if not skills:
        console.print("[dim]No bundled Agent Skills found.[/dim]")
        return
    print_skills_list(skills)


@skill_app.command(
    name="validate",
    help="Validate a SKILL.md file or directory against the Agent Skills specification checklist.",
)
def validate_skills_cmd(
    target_path: Annotated[
        Optional[Path],
        typer.Argument(
            help="Path to a SKILL.md file or directory containing skills. Defaults to bundled skills.",
        ),
    ] = None,
) -> None:
    """Validate skill files against the open Agent Skills specification."""
    search_dir = target_path or get_bundled_skills_dir()
    results = []

    if search_dir.is_file() and search_dir.name == "SKILL.md":
        results.append(validate_skill(search_dir))
    elif search_dir.is_dir():
        if (search_dir / "SKILL.md").is_file():
            results.append(validate_skill(search_dir / "SKILL.md"))
        else:
            for item in sorted(search_dir.iterdir()):
                if item.is_dir() and (item / "SKILL.md").is_file():
                    results.append(validate_skill(item / "SKILL.md"))
    else:
        print_error(
            title="Invalid Path",
            message=f"Path '{search_dir}' is neither a directory nor a SKILL.md file.",
        )
        raise typer.Exit(code=2)

    if not results:
        console.print(f"[dim]No SKILL.md files found in {search_dir}[/dim]")
        return

    print_skills_validation_results(results)

    if not all(r.is_valid for r in results):
        raise typer.Exit(code=1)


@skill_app.command(
    name="install",
    help="Install BlindSpot Agent Skills into a project workspace (.agents/skills and/or .github/skills).",
)
def install_skills_cmd(
    target: Annotated[
        str,
        typer.Option(
            "--target",
            "-t",
            help="Target agent directory standard: 'agents' (.agents/skills), 'github' (.github/skills), or 'both'.",
            show_default=True,
        ),
    ] = "both",
    dest: Annotated[
        Optional[Path],
        typer.Option(
            "--dest",
            "-d",
            help="Destination project root folder. Defaults to current working directory.",
        ),
    ] = None,
) -> None:
    """Export and install BlindSpot skills into the local workspace for AI coding agents."""
    project_root = dest or Path.cwd()
    target_modes = ["agents", "github"] if target == "both" else [target]

    if target not in ("agents", "github", "both"):
        print_error(
            title="Invalid Target",
            message=f"Invalid target '{target}'. Must be 'agents', 'github', or 'both'.",
        )
        raise typer.Exit(code=2)

    installed = install_skills_to_workspace(project_root, targets=target_modes)
    print_skills_installed(installed)


if __name__ == "__main__":
    app()



