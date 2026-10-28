"""Automated tests for BlindSpot provider and setup CLI commands."""

from unittest.mock import MagicMock, patch
from typer.testing import CliRunner
import httpx
import litellm

from blindspot.cli import app

runner = CliRunner()


def test_provider_help():
    result = runner.invoke(app, ["provider", "--help"])
    assert result.exit_code == 0
    assert "list" in result.stdout
    assert "test" in result.stdout
    assert "prompt" in result.stdout


def test_model_help():
    result = runner.invoke(app, ["model", "--help"])
    assert result.exit_code == 0
    assert "list" in result.stdout


def test_model_list_gemini():
    result = runner.invoke(app, ["model", "list", "--provider", "gemini"])
    assert result.exit_code == 0
    assert "Models for GEMINI" in result.stdout
    assert "gemini-2.5-flash" in result.stdout


def test_provider_list_command():
    result = runner.invoke(app, ["provider", "list"])
    assert result.exit_code == 0
    assert "BlindSpot AI Providers" in result.stdout
    assert "antigravity" in result.stdout
    assert "ollama" in result.stdout
    assert "gemini" in result.stdout
    assert "openai" in result.stdout


def test_antigravity_provider_test():
    result = runner.invoke(app, ["provider", "test", "--provider", "antigravity"])
    assert result.exit_code == 0
    assert "antigravity" in result.stdout
    assert "ONLINE" in result.stdout or "READY" in result.stdout



def test_provider_test_success_mocked():
    mock_tags = MagicMock(spec=httpx.Response)
    mock_tags.status_code = 200
    mock_tags.json.return_value = {"models": [{"name": "gemma4:latest"}]}

    mock_litellm_resp = MagicMock()
    mock_litellm_resp.model = "gemma4"
    choice = MagicMock()
    choice.message.content = "Hello! I am operational."
    mock_litellm_resp.choices = [choice]
    mock_litellm_resp.usage = {"total_tokens": 8}

    with patch.object(httpx.Client, "get", return_value=mock_tags), patch.object(
        litellm, "completion", return_value=mock_litellm_resp
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
    mock_litellm_resp = MagicMock()
    mock_litellm_resp.model = "gemma4"
    choice = MagicMock()
    choice.message.content = "Website navigation is clear and accessible."
    mock_litellm_resp.choices = [choice]
    mock_litellm_resp.usage = {"total_tokens": 12}

    with patch.object(litellm, "completion", return_value=mock_litellm_resp):
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


def test_setup_wizard_local_scripted(tmp_path, monkeypatch):
    """Test interactive setup wizard end-to-end with scripted inputs."""
    user_config = tmp_path / "config.toml"
    monkeypatch.setattr("blindspot.config.loader.get_user_config_path", lambda: user_config)

    # Streamlined interactive input:
    # 1. Model Route: "ollama/gemma4"
    # 2. Save confirmation if offline check fails: "y"
    wizard_inputs = "\n".join(["ollama/gemma4", "y"]) + "\n"

    result = runner.invoke(app, ["setup"], input=wizard_inputs)
    assert result.exit_code == 0
    assert "BlindSpot AI Setup" in result.stdout
    assert "BlindSpot successfully configured" in result.stdout
    assert user_config.exists()
    content = user_config.read_text(encoding="utf-8")
    assert 'provider = "ollama"' in content
    assert 'model = "gemma4"' in content
