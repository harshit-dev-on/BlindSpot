"""Automated tests for BlindSpot Typer CLI commands."""

from typer.testing import CliRunner
from blindspot.cli import app

runner = CliRunner()


def test_cli_help():
    """Verify that root `blindspot --help` runs successfully and displays commands."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "BlindSpot" in result.stdout
    assert "inspect" in result.stdout


def test_cli_version():
    """Verify that `blindspot --version` outputs version number."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.stdout


def test_inspect_help():
    """Verify that `blindspot inspect --help` displays expected options."""
    result = runner.invoke(app, ["inspect", "--help"])
    assert result.exit_code == 0
    assert "--url" in result.stdout
    assert "--context" in result.stdout


def test_inspect_missing_all_arguments():
    """Verify that invoking inspect without args displays help or an error code."""
    result = runner.invoke(app, ["inspect"])
    # Typer with no_args_is_help=True exits with 0 or 2 depending on typer version
    assert result.exit_code in (0, 2)
    assert "--url" in result.stdout or "Missing option" in result.output


def test_inspect_valid_arguments():
    """Verify successful inspect command execution with valid URL and context."""
    result = runner.invoke(
        app,
        [
            "inspect",
            "--url",
            "https://example.com",
            "--context",
            "A technical documentation portal for open source developers.",
        ],
    )
    assert result.exit_code == 0
    assert "Input validated successfully" in result.stdout
    assert "https://example.com" in result.stdout


def test_inspect_invalid_url():
    """Verify that invalid URL triggers clear error message and exit code 1."""
    result = runner.invoke(
        app,
        [
            "inspect",
            "--url",
            "invalid-url-without-scheme",
            "--context",
            "A technical documentation portal for open source developers.",
        ],
    )
    assert result.exit_code == 1
    assert "Invalid URL" in result.output or "protocol scheme" in result.output


def test_inspect_invalid_context():
    """Verify that invalid context triggers clear error message and exit code 1."""
    result = runner.invoke(
        app,
        [
            "inspect",
            "--url",
            "https://example.com",
            "--context",
            "too brief",
        ],
    )
    assert result.exit_code == 1
    assert "Invalid Context" in result.output or "too brief" in result.output
