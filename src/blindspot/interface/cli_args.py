"""CLI argument specifications, options, and callbacks for BlindSpot."""

from typing import Optional
import typer

from blindspot import __version__

SUPPORTED_BROWSERS = ("chromium", "firefox", "webkit")


def version_callback(value: bool) -> None:
    """Print BlindSpot version and exit."""
    if value:
        typer.echo(f"BlindSpot version {__version__}")
        raise typer.Exit()
