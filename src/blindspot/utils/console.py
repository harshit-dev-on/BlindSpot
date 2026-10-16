"""Terminal formatting and console output helpers using Rich."""

import sys
from typing import Optional
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

