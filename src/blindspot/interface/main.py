"""BlindSpot Agent Interface.

This module serves as the primary CLI entrypoint, dispatching commands
to the interactive launcher, scanner, or sub-command routers.
"""

from typing import Optional
from blindspot.cli import app


def main() -> None:
    """Main CLI entrypoint for BlindSpot."""
    app()


if __name__ == "__main__":
    main()
