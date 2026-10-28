"""Terminal formatting and console output helpers using Rich."""

from pathlib import Path
import sys
from typing import Any, List, Optional
from rich.console import Console, Group
import rich.panel
import rich.table
from rich.table import Table
from rich.text import Text

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

# ── Clean Modern Terminal Formatting (No Boxes / Borders) ────────────────────
_OrigPanel = rich.panel.Panel


class CleanPanel(_OrigPanel):
    """Panel replacement that renders clean borderless output without ASCII/Unicode boxes."""

    def __rich_console__(self, console_instance, options):
        items = []
        if self.title:
            if isinstance(self.title, str):
                items.append(Text(f"\n{self.title}", style="bold cyan"))
            else:
                items.append(self.title)
        items.append(self.renderable)
        yield Group(*items)


# Override rich.panel.Panel globally so no component or library draws box outlines
rich.panel.Panel = CleanPanel

# Configure Table to default to borderless (box=None) unless explicitly specified
_orig_table_init = rich.table.Table.__init__


def _clean_table_init(self, *args, **kwargs):
    if "box" not in kwargs:
        kwargs["box"] = None
    _orig_table_init(self, *args, **kwargs)


rich.table.Table.__init__ = _clean_table_init

# Configure Typer rich_utils if available
try:
    import typer.rich_utils as _typer_ru

    _typer_ru.Panel = CleanPanel  # type: ignore
    _typer_ru.STYLE_OPTIONS_TABLE_BOX = ""
    _typer_ru.STYLE_COMMANDS_TABLE_BOX = ""
    _typer_ru.STYLE_ERRORS_PANEL_BORDER = "none"
    _typer_ru.STYLE_OPTIONS_PANEL_BORDER = "none"
    _typer_ru.STYLE_COMMANDS_PANEL_BORDER = "none"

    def _clean_rich_format_error(self) -> None:
        if self.__class__.__name__ == "NoArgsIsHelpError":
            return
        c = _typer_ru._get_rich_console(stderr=True)
        ctx = getattr(self, "ctx", None)
        if ctx is not None:
            c.print(_typer_ru.highlighter(ctx.get_usage()), style=_typer_ru.STYLE_USAGE_COMMAND)
            if ctx.command.get_help_option(ctx) is not None:
                c.print(
                    _typer_ru.RICH_HELP.format(
                        command_path=_typer_ru.escape(ctx.command_path),
                        help_option=ctx.help_option_names[0],
                    ),
                    style=_typer_ru.STYLE_ERRORS_SUGGESTION,
                )
        c.print(f"\n[bold red]✖ Error:[/bold red] {self.format_message()}\n")

    _typer_ru.rich_format_error = _clean_rich_format_error  # type: ignore
except Exception:
    pass



def print_error(title: str, message: str, suggestion: Optional[str] = None) -> None:
    """Print a beginner-friendly formatted error message with optional suggestion hint.

    Args:
        title: Short description of the error category.
        message: Detailed explanation of what failed.
        suggestion: Actionable suggestion or example command to fix the issue.
    """
    err_console.print()
    err_console.print(f"[bold red]✖ Error:[/bold red] [bold white]{title}[/bold white]")
    err_console.print(f"  [red]{message}[/red]")
    if suggestion:
        err_console.print(f"  [bold yellow]Tip:[/bold yellow] [dim]{suggestion}[/dim]")
    err_console.print()


def print_success(message: str) -> None:
    """Print a success message."""
    console.print(f"[bold green]✔[/bold green] {message}")


def print_inspection_summary(url: str, context: str) -> None:
    """Print a structured summary of the validated inspection parameters.

    Args:
        url: Validated target website URL.
        context: Validated website purpose and audience context.
    """
    console.print()
    console.print("[bold cyan]BlindSpot Website Inspection Plan[/bold cyan] [dim](Input validation passed)[/dim]\n")
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Field", style="dim", width=18)
    table.add_column("Value", style="white")

    table.add_row("Website URL", f"[underline]{url}[/underline]")

    # Format context nicely (truncate visually if extremely long, show full length count)
    display_context = context if len(context) <= 200 else f"{context[:197]}..."
    table.add_row("Context", display_context)
    table.add_row("Context Length", f"{len(context)} characters")

    console.print(table)
    console.print()


def print_inspection_start(
    url: str,
    browser: str,
    headed: bool = False,
    personas: int = 3,
    concurrency: int = 1,
) -> None:
    """Print startup information indicating the audit has initiated."""
    console.print()
    console.print("[bold green]●[/bold green] [bold white]BLINDSPOT[/bold white] [dim]UX & accessibility audit initiated[/dim]")
    console.print(f"  [dim]Target[/dim]    [bold white]{url}[/bold white]")
    if headed:
        console.print(f"  [dim]Engine[/dim]    [dim]{browser}[/dim] · [bold cyan]Live Visible Window[/bold cyan] [dim](watching personas operate in real-time)[/dim]")
    else:
        console.print(f"  [dim]Engine[/dim]    [dim]{browser} · Headless (tip: pass '--headed' to watch live on screen)[/dim]")

    if personas == 1:
        console.print("  [dim]Personas[/dim]  [bold cyan]1 persona[/bold cyan] [dim](single testing mode)[/dim]\n")
    else:
        mode_desc = f"{concurrency} running simultaneously" if concurrency > 1 else "sequential (1 at a time)"
        console.print(f"  [dim]Personas[/dim]  [bold white]{personas}[/bold white] personas · [dim]{mode_desc}[/dim]\n")


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
    console.print("[bold green]BlindSpot Browser Inspection Complete[/bold green] [dim](Artifacts captured)[/dim]\n")
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Metric", style="dim", width=22)
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

    console.print(table)
    console.print(
        f"\n[bold green]✔ Inspection successful.[/bold green] Artifacts saved to directory.\n"
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
    table = Table(title="[bold cyan]BlindSpot AI Providers[/bold cyan]", box=None, padding=(0, 2))
    table.add_column("Provider", style="bold cyan")
    table.add_column("Category", style="white")
    table.add_column("Key Env Var", style="dim")
    table.add_column("Status", style="green")

    providers_info = [
        ("antigravity", "Local/Bridge", "(None - Antigravity IDE)", "Supported"),
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

    console.print()
    console.print(table)
    console.print()

    summary_table = Table(show_header=False, box=None, padding=(0, 2))
    summary_table.add_column("Key", style="dim", width=18)
    summary_table.add_column("Value", style="white")

    summary_table.add_row("Active Category", active_category)
    summary_table.add_row("Active Provider", active_provider)
    summary_table.add_row("Active Model", active_model)
    summary_table.add_row("Base URL", active_base_url or "[dim](default)[/dim]")
    summary_table.add_row("API Key Source", active_key_source)
    if config_source:
        summary_table.add_row("Config Source", config_source)

    console.print("[bold cyan]Active Configuration[/bold cyan]")
    console.print(summary_table)
    console.print()


def print_model_list(provider: str, models: list[str]) -> None:
    """Print available or verified models for a provider."""
    console.print()
    console.print(f"[bold cyan]Models for {provider.upper()}[/bold cyan]")
    if not models:
        console.print(f"  [yellow]No predefined or discovered models found for '{provider}'.[/yellow]")
        console.print("  [dim]You can specify any valid model identifier using --model <name> or in your config file.[/dim]\n")
        return

    table = Table(box=None, padding=(0, 2))
    table.add_column("#", style="dim", width=4)
    table.add_column("Model Identifier", style="bold white")
    table.add_column("Status", style="green")

    for idx, m in enumerate(models, start=1):
        table.add_row(str(idx), m, "[green]Available[/green]")

    console.print(table)
    console.print("\n[dim]To test any model: blindspot provider test --provider " + provider + " --model <name>[/dim]\n")


def print_provider_status(
    provider: str,
    model: str,
    base_url: str,
    is_reachable: bool,
    model_available: bool,
    latency_ms: Optional[float],
    message: str,
) -> None:
    """Display connection test results cleanly."""
    status_str = "[bold green][ONLINE][/bold green]" if is_reachable else "[bold red][OFFLINE][/bold red]"
    model_str = "[bold green][READY][/bold green]" if model_available else "[bold red][NOT FOUND][/bold red]"

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Field", style="dim", width=18)
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

    console.print()
    if is_reachable and model_available:
        console.print("[bold green]✔ Provider Test Passed[/bold green]")
    else:
        console.print("[bold red]✖ Provider Test Issue[/bold red]")
    console.print(table)
    console.print()


def print_ai_prompt_result(prompt: str, model: str, provider: str, content: str) -> None:
    """Display prompt and model response cleanly."""
    console.print()
    console.print(f"[bold cyan]AI Provider:[/bold cyan] [bold white]{provider}[/bold white] [dim]({model})[/dim]")
    console.print(f"[bold cyan]User Prompt:[/bold cyan]\n  [white]{prompt}[/white]\n")
    console.print(f"[bold green]AI Response:[/bold green]\n{content}\n")


def print_personas_summary(plan: Any) -> None:
    """Display AI persona generation and task planning findings cleanly without boxes."""
    console.print()
    console.print("[bold cyan]AI Persona Synthesis & Task Planning Complete[/bold cyan] [dim](Plan ready for execution)[/dim]\n")

    overview_table = Table(show_header=False, box=None, padding=(0, 2))
    overview_table.add_column("Field", style="dim", width=22)
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

    console.print(overview_table)
    console.print()

    # Display Personas & Assigned Tasks
    for p_idx, persona in enumerate(plan.personas, start=1):
        console.print(f"[bold cyan]Persona {p_idx}: {persona.name}[/bold cyan] [dim]({persona.id}) · {persona.experience_level}[/dim]")
        console.print(f"  [dim]Description:[/dim]      {persona.description}")
        console.print(f"  [dim]Browsing / Needs:[/dim] {persona.accessibility_needs or 'Standard'}")
        console.print(f"  [dim]Primary Goals:[/dim]    {', '.join(persona.goals)}")
        if persona.likely_difficulties:
            console.print(f"  [dim]Difficulties:[/dim]     {', '.join(persona.likely_difficulties)}")

        console.print()
        # Task Table for this Persona
        t_table = Table(box=None, padding=(0, 2))
        t_table.add_column("Task ID", style="bold white", width=14)
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
    """Display results of persona-based browser task execution cleanly without boxes."""
    console.print()
    title_color = "green" if run_result.failed_tasks == 0 else "yellow"
    console.print(f"[bold {title_color}]Persona-Based Browser Testing Complete[/bold {title_color}] [dim](Evidence & logs captured)[/dim]\n")

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Field", style="dim", width=20)
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

    console.print(table)
    console.print()

    # Detailed task outcome tables per persona
    for persona in run_result.personas:
        console.print(f"[bold cyan]Persona: {persona.persona_name}[/bold cyan] [dim]({persona.persona_id})[/dim]")
        p_table = Table(box=None, padding=(0, 2))
        p_table.add_column("Task ID", style="bold white", width=14)
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
    console.print()
    console.print("[bold green]✔ UX & accessibility audit completed[/bold green]\n")
    console.print(f"  [dim]Target[/dim]    [bold white]{target_url}[/bold white]")

    stats_parts: list[str] = [f"[bold green]{passed_tasks} passed[/bold green]"]
    if failed_tasks > 0:
        stats_parts.append(f"[bold red]{failed_tasks} failed[/bold red]")
    stats_parts.append(f"[dim]({total_tasks} total)[/dim]")
    console.print(f"  [dim]Tasks[/dim]     {' · '.join(stats_parts)}")

    finding_parts: list[str] = []
    if verified_issues > 0:
        finding_parts.append(f"[bold red]{verified_issues} verified defects[/bold red]")
    if usability_observations > 0:
        finding_parts.append(f"[bold yellow]{usability_observations} observations[/bold yellow]")
    if potential_improvements > 0:
        finding_parts.append(f"[bold cyan]{potential_improvements} potential improvements[/bold cyan]")
    if not finding_parts:
        finding_parts.append("[green]0 issues detected[/green]")
    console.print(f"  [dim]Findings[/dim]  {' · '.join(finding_parts)}\n")

    console.print(f"  [dim]Output[/dim]    [#60a5fa]{json_path}[/]")
    console.print(f"  [dim]Report[/dim]    [#22c55e]{html_path}[/]")
    md_path = json_path.parent / "report.md"
    if md_path.exists():
        console.print(f"  [dim]Markdown[/dim]  [#38bdf8]{md_path}[/]")
    console.print(f"  [dim]View[/dim]      [bold #22c55e]blindspot view {report_id}[/]\n")

    console.print(
        "[#60a5fa]blindspot.ai[/]  [dim]·[/]  "
        "[#60a5fa]docs.blindspot.ai[/]  [dim]·[/]  "
        "[#60a5fa]github.com/harshit-dev-on/BlindSpot[/]\n"
    )

    if top_findings:
        console.print("[bold]Top Prioritized Usability Recommendations:[/bold]")
        f_table = Table(box=None, padding=(0, 2))
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


def print_finding_panel(finding_id: str, title: str, category: str, severity: str, impact: str) -> None:
    """Print real-time finding cleanly without a box."""
    sev_color = "red" if severity in ("Critical", "High") else "yellow"
    console.print()
    console.print(f"[bold {sev_color}]● {finding_id.upper()}[/bold {sev_color}]  [bold white]{title}[/bold white]")
    console.print(f"  [dim]Severity:[/dim] [{sev_color}]{severity}[/{sev_color}]  [dim]·  Category:[/dim] {category}")
    console.print(f"  [dim]Impact:[/dim]   [white]{impact}[/white]\n")


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
