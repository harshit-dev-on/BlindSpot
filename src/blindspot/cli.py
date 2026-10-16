"""Command-line interface for BlindSpot using Typer."""

from typing import Optional
import typer
from typing_extensions import Annotated

from blindspot import __version__
from blindspot.core.models import InspectConfig
from blindspot.core.validation import validate_context, validate_url
from blindspot.utils.console import print_error, print_inspection_summary

app = typer.Typer(
    name="blindspot",
    help="BlindSpot: Open-source AI-powered website UX testing tool.\n\n"
    "Simulates real user personas exploring websites to uncover UX flaws, "
    "accessibility barriers, and confusing user journeys.",
    no_args_is_help=True,
    add_completion=False,
)


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


@app.command(
    name="inspect",
    help="Prepare and validate a website inspection session.\n\n"
    "Requires a target website URL and a context description of the website's "
    "purpose and target audience.",
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
) -> None:
    """Run website inspection input validation and session preparation."""
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

    # 3. Create Validated Configuration & Print Summary
    config = InspectConfig(url=url.strip(), context=resolved_context)
    print_inspection_summary(url=config.url, context=config.context)


if __name__ == "__main__":
    app()
