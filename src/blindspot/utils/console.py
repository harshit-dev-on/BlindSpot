"""Terminal formatting and console output helpers using Rich."""

import sys
from typing import Any, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Enable UTF-8 encoding stream on Windows when available to prevent charmap encoding errors
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

console = Console()
err_console = Console(stderr=True)


def print_error(title: str, message: str, suggestion: Optional[str] = None) -> None:
    """Print a beginner-friendly formatted error message with optional suggestion hint.

    Args:
        title: Short description of the error category.
        message: Detailed explanation of what failed.
        suggestion: Actionable suggestion or example command to fix the issue.
    """
    body = f"[bold red][ERROR] {message}[/bold red]"
    if suggestion:
        body += f"\n\n[bold yellow][TIP][/bold yellow] [dim]{suggestion}[/dim]"

    panel = Panel(
        body,
        title=f"[bold red]{title}[/bold red]",
        title_align="left",
        border_style="red",
        padding=(1, 2),
    )
    err_console.print(panel)


def print_success(message: str) -> None:
    """Print a success message."""
    console.print(f"[bold green][OK][/bold green] {message}")


def print_inspection_summary(url: str, context: str) -> None:
    """Print a structured summary of the validated inspection parameters.

    Args:
        url: Validated target website URL.
        context: Validated website purpose and audience context.
    """
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("Field", style="bold cyan", width=16)
    table.add_column("Value", style="white")

    table.add_row("Website URL", f"[underline]{url}[/underline]")

    # Format context nicely (truncate visually if extremely long, show full length count)
    display_context = context if len(context) <= 200 else f"{context[:197]}..."
    table.add_row("Context", display_context)
    table.add_row("Context Length", f"{len(context)} characters")

    panel = Panel(
        table,
        title="[bold blue]BlindSpot Website Inspection Plan[/bold blue]",
        subtitle="[dim]Status: Input validation passed[/dim]",
        border_style="blue",
        padding=(1, 2),
    )
    console.print(panel)


def print_inspection_start(url: str, browser: str) -> None:
    """Print an indicator that browser inspection has started."""
    console.print(
        f"[bold cyan]→[/bold cyan] Launching [bold]{browser}[/bold] to inspect [underline]{url}[/underline]..."
    )


def print_browser_inspection_summary(
    title: str,
    final_url: str,
    viewport_width: int,
    viewport_height: int,
    browser: str,
    total_elements: int,
    links_count: int,
    buttons_count: int,
    form_fields_count: int,
    text_length: int,
    screenshot_path: str,
    result_json_path: str,
) -> None:
    """Print a structured summary of the browser inspection results and artifacts.

    Args:
        title: Inspected page title.
        final_url: Final landing URL after any redirects.
        viewport_width: Viewport width in pixels.
        viewport_height: Viewport height in pixels.
        browser: Browser engine used ('chromium', etc.).
        total_elements: Total interactive elements discovered.
        links_count: Number of links discovered.
        buttons_count: Number of buttons discovered.
        form_fields_count: Number of form fields discovered.
        text_length: Length of extracted readable text.
        screenshot_path: Path to captured full-page screenshot.
        result_json_path: Path to saved structured JSON inspection file.
    """
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("Metric", style="bold cyan", width=22)
    table.add_column("Value", style="white")

    table.add_row("Page Title", title or "[dim](No title)[/dim]")
    table.add_row("Final URL", f"[underline]{final_url}[/underline]")
    table.add_row("Browser / Viewport", f"{browser} ({viewport_width}x{viewport_height})")
    table.add_row(
        "Interactive Elements",
        f"{total_elements} total ({links_count} links, {buttons_count} buttons, {form_fields_count} form fields)",
    )
    table.add_row("Page Text Length", f"{text_length:,} characters")
    table.add_row("Screenshot Saved", f"[green]{screenshot_path}[/green]")
    table.add_row("Structured Data Saved", f"[green]{result_json_path}[/green]")

    panel = Panel(
        table,
        title="[bold green]BlindSpot Browser Inspection Complete[/bold green]",
        subtitle="[dim]Status: Artifacts captured[/dim]",
        border_style="green",
        padding=(1, 2),
    )
    console.print(panel)
    console.print(
        f"[bold green][OK] Inspection successful.[/bold green] Artifacts saved to directory."
    )


def print_provider_list(
    active_provider: str,
    active_model: str,
    active_base_url: str,
    active_key_source: str,
    active_category: str = "local",
    config_source: Optional[str] = None,
) -> None:
    """Print a list of supported AI providers and the currently active configuration."""
    table = Table(title="[bold blue]BlindSpot AI Providers[/bold blue]", box=None, padding=(0, 2))
    table.add_column("Provider", style="bold cyan")
    table.add_column("Category", style="white")
    table.add_column("Key Env Var", style="dim")
    table.add_column("Status", style="green")

    providers_info = [
        ("ollama", "Local", "(None - Free & Offline)", "Supported"),
        ("gemini", "Cloud", "GEMINI_API_KEY", "Supported"),
        ("openai", "Cloud", "OPENAI_API_KEY", "Supported"),
        ("anthropic", "Cloud", "ANTHROPIC_API_KEY", "Supported"),
        ("openrouter", "Cloud", "OPENROUTER_API_KEY", "Supported"),
        ("custom", "Custom/Proxy", "CUSTOM_API_KEY (optional)", "Supported"),
    ]

    for p_id, cat, key_env, status in providers_info:
        is_active = active_provider in (p_id, "openai_compatible" if p_id == "custom" else "")
        label = p_id + (" [bold green](active)[/bold green]" if is_active else "")
        table.add_row(label, cat, key_env, f"[green]{status}[/green]")

    console.print(table)
    console.print()

    summary_table = Table(show_header=False, box=None, padding=(0, 1))
    summary_table.add_column("Key", style="bold cyan", width=18)
    summary_table.add_column("Value", style="white")

    summary_table.add_row("Active Category", active_category)
    summary_table.add_row("Active Provider", active_provider)
    summary_table.add_row("Active Model", active_model)
    summary_table.add_row("Base URL", active_base_url or "[dim](default)[/dim]")
    summary_table.add_row("API Key Source", active_key_source)
    if config_source:
        summary_table.add_row("Config Source", config_source)

    panel = Panel(
        summary_table,
        title="[bold blue]Active Configuration[/bold blue]",
        border_style="blue",
        padding=(1, 2),
    )
    console.print(panel)


def print_model_list(provider: str, models: list[str]) -> None:
    """Print available or verified models for a provider."""
    if not models:
        console.print(
            Panel(
                f"[yellow]No predefined or discovered models found for '{provider}'.[/yellow]\n"
                "You can specify any valid model identifier using [cyan]--model <name>[/cyan] or in your config file.",
                title=f"[bold blue]Models for {provider.upper()}[/bold blue]",
                border_style="yellow",
                padding=(1, 2),
            )
        )
        return

    table = Table(title=f"[bold blue]Models for {provider.upper()}[/bold blue]", box=None, padding=(0, 2))
    table.add_column("#", style="dim", width=4)
    table.add_column("Model Identifier", style="bold white")
    table.add_column("Status", style="green")

    for idx, m in enumerate(models, start=1):
        table.add_row(str(idx), m, "[green]Available[/green]")

    console.print(table)
    console.print("\n[dim]To test any model: blindspot provider test --provider " + provider + " --model <name>[/dim]")


def print_provider_status(
    provider: str,
    model: str,
    base_url: str,
    is_reachable: bool,
    model_available: bool,
    latency_ms: Optional[float],
    message: str,
) -> None:
    """Display connection test results in a styled panel."""
    status_str = "[bold green][ONLINE][/bold green]" if is_reachable else "[bold red][OFFLINE][/bold red]"
    model_str = "[bold green][READY][/bold green]" if model_available else "[bold red][NOT FOUND][/bold red]"

    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("Field", style="bold cyan", width=18)
    table.add_column("Value", style="white")

    table.add_row("Provider", provider)
    table.add_row("Model", model)
    table.add_row("Endpoint", base_url)
    table.add_row("Server Reachable", status_str)
    table.add_row("Model Status", model_str)
    if latency_ms is not None:
        table.add_row("Latency", f"{latency_ms} ms")
    if message:
        table.add_row("Details", message)

    border_color = "green" if (is_reachable and model_available) else "yellow" if is_reachable else "red"
    title = "[bold green]Provider Test Passed[/bold green]" if (is_reachable and model_available) else "[bold red]Provider Test Issue[/bold red]"

    panel = Panel(
        table,
        title=title,
        border_style=border_color,
        padding=(1, 2),
    )
    console.print(panel)


def print_ai_prompt_result(prompt: str, model: str, provider: str, content: str) -> None:
    """Display prompt and model response."""
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("Field", style="bold cyan", width=14)
    table.add_column("Value", style="white")

    table.add_row("Provider", f"{provider} ({model})")
    table.add_row("Prompt", prompt)
    table.add_row("Response", content)

    panel = Panel(
        table,
        title="[bold green]AI Model Response[/bold green]",
        border_style="green",
        padding=(1, 2),
    )
    console.print(panel)


def print_personas_summary(plan: Any) -> None:
    """Display AI persona generation and task planning findings."""
    # 1. Overview Panel
    overview_table = Table(show_header=False, box=None, padding=(0, 1))
    overview_table.add_column("Field", style="bold cyan", width=18)
    overview_table.add_column("Value", style="white")

    overview_table.add_row("Website Summary", plan.website_summary)
    overview_table.add_row(
        "AI Generator",
        f"{plan.provider_used or 'active'} ({plan.model_used or 'default'})",
    )
    overview_table.add_row(
        "Synthesized Personas",
        f"{len(plan.personas)} personas ({plan.total_tasks} total tasks)",
    )

    if plan.total_unverified_tasks > 0:
        overview_table.add_row(
            "Unverified Features",
            f"[yellow]{plan.total_unverified_tasks} tasks flagged with uncertainty[/yellow]",
        )
    else:
        overview_table.add_row(
            "Feature Grounding",
            "[green]All tasks grounded in verified website capabilities[/green]",
        )

    if plan.plan_file_path:
        overview_table.add_row("Plan Saved To", f"[bold green]{plan.plan_file_path}[/bold green]")

    console.print(
        Panel(
            overview_table,
            title="[bold blue]AI Persona Synthesis & Task Planning Complete[/bold blue]",
            subtitle="[dim]Status: Plan ready for autonomous execution[/dim]",
            border_style="blue",
            padding=(1, 2),
        )
    )

    # 2. Display Personas & Assigned Tasks
    for p_idx, persona in enumerate(plan.personas, start=1):
        p_table = Table(show_header=False, box=None, padding=(0, 1))
        p_table.add_column("Key", style="bold cyan", width=16)
        p_table.add_column("Val", style="white")

        p_table.add_row("Description", persona.description)
        p_table.add_row("Experience Level", f"[magenta]{persona.experience_level}[/magenta]")
        p_table.add_row("Browsing / Needs", persona.accessibility_needs or "Standard")
        p_table.add_row("Primary Goals", ", ".join(persona.goals))
        p_table.add_row("Likely Difficulties", ", ".join(persona.likely_difficulties))

        console.print(
            Panel(
                p_table,
                title=f"[bold cyan]Persona {p_idx}: {persona.name}[/bold cyan] [dim]({persona.id})[/dim]",
                border_style="cyan",
                padding=(0, 2),
            )
        )

        # Task Table for this Persona
        t_table = Table(box=None, padding=(0, 1))
        t_table.add_column("Task ID", style="bold white", width=16)
        t_table.add_column("Objective & Success Criteria", style="white", ratio=3)
        t_table.add_column("Evidence", style="dim", ratio=2)
        t_table.add_column("Status", width=14)

        for task in persona.tasks:
            status_badge = (
                "[green][VERIFIED][/green]"
                if task.is_verified
                else "[yellow][UNVERIFIED][/yellow]"
            )
            obj_text = f"[bold]{task.objective}[/bold]"
            if task.success_criteria:
                obj_text += f"\n[dim]Success: {'; '.join(task.success_criteria)}[/dim]"
            if not task.is_verified and task.uncertainty_notes:
                obj_text += f"\n[yellow]Note: {task.uncertainty_notes}[/yellow]"

            evidence_text = "\n".join(f"• {e}" for e in task.evidence_to_collect)

            t_table.add_row(task.id, obj_text, evidence_text, status_badge)

        console.print(t_table)
        console.print()


def print_execution_summary(run_result: Any) -> None:
    """Display results of persona-based browser task execution."""
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("Field", style="bold cyan", width=18)
    table.add_column("Value", style="white")

    table.add_row("Target Website", run_result.target_url)
    table.add_row(
        "Browser Execution",
        f"{run_result.browser} ({'headless' if run_result.headless else 'headed/visible window'})",
    )
    table.add_row(
        "Task Results",
        f"[bold white]{run_result.total_tasks} total tasks[/bold white] | "
        f"[green]{run_result.passed_tasks} passed[/green] | "
        f"[red]{run_result.failed_tasks} failed[/red] | "
        f"[yellow]{run_result.inconclusive_tasks} inconclusive[/yellow]",
    )

    if run_result.results_file_path:
        table.add_row(
            "Evidence Saved To",
            f"[bold green]{run_result.results_file_path}[/bold green]",
        )

    border_color = "green" if run_result.failed_tasks == 0 else "yellow"
    console.print(
        Panel(
            table,
            title="[bold green]Persona-Based Browser Testing Complete[/bold green]",
            subtitle="[dim]Status: Evidence and task logs captured[/dim]",
            border_style=border_color,
            padding=(1, 2),
        )
    )

    # Detailed task outcome tables per persona
    for persona in run_result.personas:
        console.print(f"[bold cyan]Persona: {persona.persona_name}[/bold cyan] [dim]({persona.persona_id})[/dim]")
        p_table = Table(box=None, padding=(0, 1))
        p_table.add_column("Task ID", style="bold white", width=16)
        p_table.add_column("Objective", style="white", ratio=3)
        p_table.add_column("Actions", width=10)
        p_table.add_column("Outcome", width=16)
        p_table.add_column("Evidence", style="dim", ratio=2)

        for task_res in persona.task_results:
            status_badge = (
                "[bold green][PASS][/bold green]"
                if task_res.status.value == "success"
                else "[bold red][FAIL][/bold red]"
                if task_res.status.value == "failure"
                else "[bold yellow][INCONCLUSIVE][/bold yellow]"
            )

            actions_count = f"{len(task_res.actions_taken)} steps"
            evidence_str = "; ".join(task_res.evidence) if task_res.evidence else (task_res.error_message or "None")

            p_table.add_row(
                task_res.task_id,
                task_res.task_objective,
                actions_count,
                status_badge,
                evidence_str,
            )

        console.print(p_table)
        console.print()


def print_report_summary(
    report_id: str,
    target_url: str,
    total_tasks: int,
    passed_tasks: int,
    failed_tasks: int,
    verified_issues: int,
    usability_observations: int,
    potential_improvements: int,
    json_path: Path,
    html_path: Path,
    top_findings: Optional[List[Any]] = None,
) -> None:
    """Display final UX report generation summary and top prioritized findings in console."""
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("Field", style="bold cyan", width=24)
    table.add_column("Value", style="white")

    table.add_row("Target Website", target_url)
    table.add_row("Report ID", report_id)
    table.add_row(
        "Task Results",
        f"{total_tasks} total tasks | [green]{passed_tasks} passed[/green] | [red]{failed_tasks} failed[/red]",
    )
    table.add_row(
        "Discovered Findings",
        f"[bold red]{verified_issues} Verified Defects[/bold red] • [bold yellow]{usability_observations} Usability Observations[/bold yellow] • [bold cyan]{potential_improvements} Potential Improvements[/bold cyan]",
    )
    table.add_row("Machine-Readable JSON", str(json_path))
    table.add_row("Interactive HTML Report", f"[bold underline green]{html_path}[/bold underline green]")

    border_color = "red" if verified_issues > 0 else "yellow" if usability_observations > 0 else "green"
    console.print(
        Panel(
            table,
            title="[bold green]BlindSpot UX Testing & Analysis Complete[/bold green]",
            subtitle="[dim]Status: Report generated and saved[/dim]",
            border_style=border_color,
            padding=(1, 2),
        )
    )

    if top_findings:
        console.print("\n[bold]Top Prioritized Usability Recommendations:[/bold]")
        f_table = Table(box=None, padding=(0, 1))
        f_table.add_column("Rank", style="dim", width=6)
        f_table.add_column("Category", width=22)
        f_table.add_column("Severity", width=12)
        f_table.add_column("Finding Title", style="bold white", ratio=2)
        f_table.add_column("Recommended Action", style="white", ratio=3)

        for f in top_findings[:5]:
            cat_color = (
                "red" if f.category.value == "verified_issue"
                else "yellow" if f.category.value == "usability_observation"
                else "cyan"
            )
            sev_color = (
                "red" if f.severity.value == "Critical"
                else "bright_red" if f.severity.value == "High"
                else "yellow" if f.severity.value == "Medium"
                else "blue"
            )
            f_table.add_row(
                f"#{f.priority_rank}",
                f"[{cat_color}]{f.category.label}[/{cat_color}]",
                f"[{sev_color}]{f.severity.value}[/{sev_color}]",
                f.title,
                f.suggested_improvement,
            )
        console.print(f_table)
        console.print(f"\n[dim]To view full evidence, reproduction steps & screenshots: open {html_path}[/dim]\n")


def print_skills_list(skills: list) -> None:
    """Print a formatted table of available Agent Skills."""
    table = Table(
        title="[bold cyan]BlindSpot Agent Skills (Open Standard)[/bold cyan]",
        box=None,
        padding=(0, 2),
    )
    table.add_column("Skill Name", style="bold white", width=28)
    table.add_column("Version", style="dim", width=10)
    table.add_column("Description", style="white", ratio=3)
    table.add_column("Allowed Tools", style="cyan", width=22)

    for s in skills:
        tools = s.allowed_tools or "all"
        table.add_row(f"/{s.name}", s.version, s.description, tools)

    console.print(table)
    console.print("\n[dim]Compatible with OpenAI Codex, GitHub Copilot, Cursor, Antigravity, VS Code, and Goose.[/dim]\n")


def print_skills_validation_results(results: list) -> None:
    """Print the results of validating SKILL.md files against the Agent Skills specification."""
    all_valid = all(r.is_valid for r in results)
    title_color = "green" if all_valid else "red"
    console.print(f"\n[bold {title_color}]Agent Skills Validation Summary ({len(results)} evaluated):[/bold {title_color}]\n")

    for r in results:
        status_badge = "[bold green][PASS][/bold green]" if r.is_valid else "[bold red][FAIL][/bold red]"
        console.print(f" {status_badge} [bold white]{r.name}[/bold white] [dim]({r.token_estimate} tokens) - {r.path}[/dim]")
        for err in r.errors:
            console.print(f"    [bold red]Error:[/bold red] {err}")
        for warn in r.warnings:
            console.print(f"    [bold yellow]Warning:[/bold yellow] {warn}")

    console.print()


def print_skills_installed(installed: dict) -> None:
    """Print confirmation of skills installed into workspace."""
    table = Table(
        title="[bold green]Agent Skills Exported to Workspace[/bold green]",
        box=None,
        padding=(0, 2),
    )
    table.add_column("Environment Target", style="bold cyan", width=25)
    table.add_column("Installed Skills", style="white", ratio=2)

    for target, files in installed.items():
        names = ", ".join(f.parent.name for f in files)
        dest_folder = ".agents/skills" if target == "agents" else ".github/skills"
        table.add_row(f"{dest_folder} ({target})", names)

    console.print(table)
    console.print("\n[dim]AI coding agents (Cursor, Copilot, Antigravity, Claude) in this workspace can now activate these skills.[/dim]\n")

