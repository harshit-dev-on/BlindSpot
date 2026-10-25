"""Interactive terminal interface for BlindSpot."""

from typing import Optional, Tuple
import typer
from rich.panel import Panel
from rich.prompt import Prompt

from blindspot.utils.console import console


def show_interactive_start_screen() -> Tuple[Optional[str], Optional[str]]:
    """Display the interactive start screen and prompt for target URL and instructions.

    Returns:
        Tuple of (target_url, instruction). If target_url is None, Web Studio was requested.
    """
    console.print(
        Panel(
            "[bold white]BlindSpot — Autonomous AI UX Testing[/bold white]\n\n"
            "[dim]Simulate human user personas to uncover UX flaws, accessibility barriers, and friction.[/dim]",
            title="[bold cyan]BlindSpot[/bold cyan]",
            title_align="left",
            border_style="cyan",
            padding=(1, 2),
        )
    )

    try:
        chosen_target = Prompt.ask(
            "Enter Target URL to test [or press Enter to launch Web Studio]",
            default="",
        )
        if not chosen_target.strip():
            return None, None

        chosen_instruction = Prompt.ask(
            "Custom instructions [optional, e.g. 'Focus on checkout flow']",
            default="",
        )
        instruction = chosen_instruction.strip() if chosen_instruction.strip() else None
        return chosen_target.strip(), instruction

    except (KeyboardInterrupt, typer.Abort):
        console.print("\n[yellow]Exited.[/yellow]")
        raise typer.Exit(code=0)
