"""Automated tests for BlindSpot provider CLI commands."""

from unittest.mock import MagicMock, patch
from typer.testing import CliRunner
import httpx

from blindspot.cli import app

runner = CliRunner()


def test_provider_help():
    result = runner.invoke(app, ["provider", "--help"])
    assert result.exit_code == 0
    assert "list" in result.stdout
    assert "test" in result.stdout
    assert "prompt" in result.stdout


def test_provider_list_command():
    result = runner.invoke(app, ["provider", "list"])
    assert result.exit_code == 0
    assert "BlindSpot AI Providers" in result.stdout
    assert "ollama" in result.stdout
    assert "openai_compatible" in result.stdout


def test_provider_test_success_mocked():
    mock_tags = MagicMock(spec=httpx.Response)
    mock_tags.status_code = 200
    mock_tags.json.return_value = {"models": [{"name": "gemma4:latest"}]}

    mock_chat = MagicMock(spec=httpx.Response)
    mock_chat.status_code = 200
    mock_chat.json.return_value = {"message": {"content": "Hello! I am operational."}}

    with patch.object(httpx.Client, "get", return_value=mock_tags), patch.object(
        httpx.Client, "post", return_value=mock_chat
    ):
        result = runner.invoke(app, ["provider", "test", "--provider", "ollama", "--model", "gemma4"])
        assert result.exit_code == 0
        assert "ONLINE" in result.stdout or "READY" in result.stdout
        assert "Hello! I am operational." in result.stdout


def test_provider_test_offline_mocked():
    with patch.object(httpx.Client, "get", side_effect=httpx.ConnectError("Connection refused")):
        result = runner.invoke(app, ["provider", "test", "--provider", "ollama"])
        assert result.exit_code == 1
        assert "OFFLINE" in result.stdout


def test_provider_prompt_command_mocked():
    mock_chat = MagicMock(spec=httpx.Response)
    mock_chat.status_code = 200
    mock_chat.json.return_value = {"message": {"content": "Website navigation is clear and accessible."}}

    with patch.object(httpx.Client, "post", return_value=mock_chat):
        result = runner.invoke(
            app,
            ["provider", "prompt", "Analyze this UX flow", "--provider", "ollama", "--model", "gemma4"],
        )
        assert result.exit_code == 0
        assert "Website navigation is clear and accessible." in result.stdout


def test_provider_test_invalid_provider_option():
    result = runner.invoke(app, ["provider", "test", "--provider", "invalid_ai"])
    assert result.exit_code == 1
    assert "Unsupported AI provider" in result.output
