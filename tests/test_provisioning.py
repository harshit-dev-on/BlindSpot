"""Unit tests for automatic browser binary provisioning."""

import pytest
from unittest.mock import MagicMock, patch
from playwright.sync_api import Error as PlaywrightError
from blindspot.runtime import ensure_browser_engine


def test_ensure_browser_engine_already_installed():
    # Calling on already-installed chromium should succeed seamlessly without error
    ensure_browser_engine("chromium")


def test_ensure_browser_engine_auto_installs_on_missing():
    with patch("playwright.sync_api.sync_playwright") as mock_playwright:
        mock_p = MagicMock()
        mock_playwright.return_value.__enter__.return_value = mock_p
        mock_launcher = MagicMock()
        setattr(mock_p, "chromium", mock_launcher)

        # First call raises missing executable error, second call succeeds after auto-install
        mock_launcher.launch.side_effect = [
            PlaywrightError("Executable doesn't exist at /path/to/chromium. Please run 'playwright install'"),
            MagicMock(),
        ]

        with patch("subprocess.run") as mock_run:
            ensure_browser_engine("chromium")
            # Verify subprocess was called to install chromium
            assert mock_run.called
            args = mock_run.call_args[0][0]
            assert "playwright" in args
            assert "install" in args
            assert "chromium" in args
