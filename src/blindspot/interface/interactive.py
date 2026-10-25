"""Interactive terminal interface for BlindSpot."""

from typing import Optional, Tuple
import typer
from rich.prompt import Prompt

from blindspot.utils.console import console


def show_interactive_start_screen() -> Tuple[Optional[str], Optional[str]]:
    """Display the interactive start screen and prompt for target URL and instructions.

    Returns:
        Tuple of (target_url, instruction). If target_url is None, Web Studio was requested.
    """
    console.print()
    console.print("[bold cyan]BlindSpot[/bold cyan]  [bold white]Autonomous AI UX Testing[/bold white]")
    console.print("[dim]Simulate human user personas to uncover UX flaws, accessibility barriers, and friction.[/dim]\n")

    try:
        chosen_target = Prompt.ask(
            "[bold cyan]?[/bold cyan] [bold]Target URL[/bold] [dim](press Enter to launch Web Studio)[/dim]",
            default="",
        )
        if not chosen_target.strip():
            return None, None

        chosen_instruction = Prompt.ask(
            "[bold cyan]?[/bold cyan] [bold]Custom instructions[/bold] [dim](optional, e.g. 'Focus on checkout flow')[/dim]",
            default="",
        )
        instruction = chosen_instruction.strip() if chosen_instruction.strip() else None
        console.print()
        return chosen_target.strip(), instruction

    except (KeyboardInterrupt, typer.Abort):
        console.print("\n[yellow]Exited.[/yellow]\n")
        raise typer.Exit(code=0)
