"""BlindSpot Interface package."""

from blindspot.interface.cli_args import SUPPORTED_BROWSERS, version_callback
from blindspot.interface.environment import validate_environment
from blindspot.interface.interactive import show_interactive_start_screen
from blindspot.cli import app
from blindspot.interface.scan_setup import preflight_model_connection, run_setup_wizard

main = app

__all__ = [
    "SUPPORTED_BROWSERS",
    "app",
    "main",
    "preflight_model_connection",
    "run_setup_wizard",
    "show_interactive_start_screen",
    "validate_environment",
    "version_callback",
]
