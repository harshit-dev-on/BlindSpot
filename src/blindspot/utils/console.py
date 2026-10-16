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
    console.print(
        "[bold green][OK] Input validated successfully.[/bold green] Ready to run UX inspection."
    )
