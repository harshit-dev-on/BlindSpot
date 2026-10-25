"""Automatic browser binary provisioning for zero-config first runs."""

from __future__ import annotations

import logging
import subprocess
import sys
from typing import Optional

from rich.console import Console

logger = logging.getLogger(__name__)
console = Console()


def ensure_browser_engine(browser_type: str = "chromium") -> None:
    """Verify that the required Playwright browser engine is installed.

    If missing, automatically downloads and provisions it without requiring manual intervention.
    """
    from playwright.sync_api import Error as PlaywrightError, sync_playwright

    with sync_playwright() as p:
        launcher = getattr(p, browser_type, None)
        if launcher is None:
            raise ValueError(f"Browser engine '{browser_type}' is not supported.")

        try:
            # Test launch
            browser = launcher.launch(headless=True)
            browser.close()
            return
        except PlaywrightError as exc:
            err_msg = str(exc)
            if "Executable doesn't exist" in err_msg or "Please run" in err_msg:
                console.print(
                    f"\n[bold cyan]→ First-time setup:[/bold cyan] Automatically provisioning [bold]{browser_type}[/bold] browser binary..."
                )
                try:
                    cmd = [sys.executable, "-m", "playwright", "install", browser_type]
                    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    console.print(f"[bold green]✓[/bold green] [bold]{browser_type}[/bold] successfully installed.\n")
                except Exception as install_exc:
                    raise RuntimeError(
                        f"Failed to auto-install Playwright browser '{browser_type}': {install_exc}.\n"
                        f"Please run 'playwright install {browser_type}' manually."
                    ) from install_exc
            else:
                raise
