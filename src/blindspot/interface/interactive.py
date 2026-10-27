"""Interactive terminal interface for BlindSpot."""

from typing import Optional, Tuple
import typer
from rich.prompt import Prompt

from blindspot.utils.console import console


class StartScreenResult(tuple):
    """Result of the interactive start screen with backward-compatible tuple unpacking."""

    def __new__(
        cls,
        target: Optional[str],
        instruction: Optional[str],
        headed: bool = True,
        personas: int = 1,
        concurrency: int = 1,
    ):
        obj = super().__new__(cls, (target, instruction))
        obj.target = target
        obj.instruction = instruction
        obj.headed = headed
        obj.personas = personas
        obj.concurrency = concurrency
        return obj


def show_interactive_start_screen() -> StartScreenResult:
    """Display the interactive start screen and prompt for target URL, instructions, browser mode, and persona count.

    Returns:
        StartScreenResult with (target_url, instruction) and .headed, .personas, .concurrency attributes.
        If target_url is None, Web Studio was requested.
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
            return StartScreenResult(None, None, False, 1, 1)

        chosen_instruction = Prompt.ask(
            "[bold cyan]?[/bold cyan] [bold]Custom instructions[/bold] [dim](optional, e.g. 'Focus on checkout flow')[/dim]",
            default="",
        )
        instruction = chosen_instruction.strip() if chosen_instruction.strip() else None

        watch_live_input = Prompt.ask(
            "[bold cyan]?[/bold cyan] [bold]Watch personas live in browser window?[/bold]",
            choices=["y", "n"],
            default="y",
        )
        headed = watch_live_input.lower().strip() == "y"

        personas_input = Prompt.ask(
            "[bold cyan]?[/bold cyan] [bold]Number of personas to test [1-5][/bold] [dim](1 for testing, 3 for full audit)[/dim]",
            default="1",
        )
        try:
            personas = max(1, min(5, int(personas_input.strip())))
        except ValueError:
            personas = 1

        concurrency = 1
        if personas > 1:
            concurrency_input = Prompt.ask(
                f"[bold cyan]?[/bold cyan] [bold]How many personas to run simultaneously? [1-{personas}][/bold] [dim](1 for sequential)[/dim]",
                default="1",
            )
            try:
                concurrency = max(1, min(personas, int(concurrency_input.strip())))
            except ValueError:
                concurrency = 1

        console.print()
        return StartScreenResult(chosen_target.strip(), instruction, headed, personas, concurrency)

    except (KeyboardInterrupt, typer.Abort):
        console.print("\n[yellow]Exited.[/yellow]\n")
        raise typer.Exit(code=0)


__all__ = ["StartScreenResult", "show_interactive_start_screen"]
