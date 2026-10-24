"""Interactive setup wizard for configuring AI model routes (Strix format).

This module re-exports setup routines from `blindspot.interface.scan_setup`
for backward compatibility.
"""

from blindspot.config.loader import (
    get_user_config_path,
    load_config,
    parse_model_route,
    save_config,
)
from blindspot.interface.scan_setup import (
    preflight_model_connection,
    run_setup_wizard,
)

__all__ = [
    "get_user_config_path",
    "load_config",
    "parse_model_route",
    "preflight_model_connection",
    "run_setup_wizard",
    "save_config",
]
