"""Command-line interface for BlindSpot using Typer."""

from pathlib import Path
from typing import Optional
import typer
from typing_extensions import Annotated

from blindspot import __version__
from blindspot.browser import inspect_website
from blindspot.core.models import InspectConfig
from blindspot.core.validation import validate_context, validate_url
from blindspot.utils.console import (
    print_browser_inspection_summary,
    print_error,
    print_inspection_start,
    print_inspection_summary,
)

app = typer.Typer(
    name="blindspot",
    help="BlindSpot: Open-source AI-powered website UX testing tool.\n\n"
    "Simulates real user personas exploring websites to uncover UX flaws, "
    "accessibility barriers, and confusing user journeys.",
    no_args_is_help=True,
    add_completion=False,
)

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
