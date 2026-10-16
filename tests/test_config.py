"""Unit tests for BlindSpot configuration loading and validation."""

import os
from pathlib import Path
import pytest
from pydantic import ValidationError

from blindspot.config.models import AIConfig, BlindSpotConfig
from blindspot.config.loader import find_config_file, load_config


def test_ai_config_defaults():
    cfg = AIConfig()
    assert cfg.provider == "ollama"
    assert cfg.model == "gemma4"
    assert cfg.base_url is None
    assert cfg.api_key_env is None
    assert cfg.timeout == 60.0


def test_ai_config_invalid_provider():
    with pytest.raises(ValidationError, match="Unsupported AI provider 'invalid_provider'"):
        AIConfig(provider="invalid_provider")


def test_ai_config_empty_model():
    with pytest.raises(ValidationError, match="Model name cannot be empty"):
        AIConfig(model="   ")


def test_load_config_from_toml(tmp_path: Path):
    toml_content = """
[ai]
provider = "openai_compatible"
model = "gpt-4o-mini"
base_url = "https://custom.endpoint.com/v1"
api_key_env = "CUSTOM_KEY"
timeout = 45.0
"""
    config_file = tmp_path / "blindspot.toml"
    config_file.write_text(toml_content, encoding="utf-8")

    cfg = load_config(custom_path=config_file)
    assert cfg.ai.provider == "openai_compatible"
    assert cfg.ai.model == "gpt-4o-mini"
    assert cfg.ai.base_url == "https://custom.endpoint.com/v1"
    assert cfg.ai.api_key_env == "CUSTOM_KEY"
    assert cfg.ai.timeout == 45.0


def test_load_config_missing_custom_file():
    with pytest.raises(FileNotFoundError, match="does not exist"):
        load_config(custom_path="nonexistent_config_file_98765.toml")


def test_load_config_env_var_overrides(monkeypatch):
    monkeypatch.setenv("BLINDSPOT_PROVIDER", "openai_compatible")
    monkeypatch.setenv("BLINDSPOT_MODEL", "meta-llama/Llama-3-8b-chat")
    monkeypatch.setenv("BLINDSPOT_BASE_URL", "https://api.together.xyz/v1")
    monkeypatch.setenv("BLINDSPOT_API_KEY_ENV", "TOGETHER_API_KEY")
    monkeypatch.setenv("BLINDSPOT_TIMEOUT", "120.0")

    cfg = load_config()
    assert cfg.ai.provider == "openai_compatible"
    assert cfg.ai.model == "meta-llama/Llama-3-8b-chat"
    assert cfg.ai.base_url == "https://api.together.xyz/v1"
    assert cfg.ai.api_key_env == "TOGETHER_API_KEY"
    assert cfg.ai.timeout == 120.0


def test_load_config_cli_overrides_env_and_file(tmp_path: Path, monkeypatch):
    toml_content = """
[ai]
provider = "ollama"
model = "llama3"
"""
    config_file = tmp_path / "blindspot.toml"
    config_file.write_text(toml_content, encoding="utf-8")

    monkeypatch.setenv("BLINDSPOT_MODEL", "mistral")

    cfg = load_config(custom_path=config_file, model="gemma4-custom", provider="openai_compatible")
    assert cfg.ai.provider == "openai_compatible"
    assert cfg.ai.model == "gemma4-custom"


def test_save_and_load_config(tmp_path: Path):
    from blindspot.config.loader import save_config
    from blindspot.config.models import TaskModelsConfig

    target_file = tmp_path / "saved_config.toml"
    cfg = BlindSpotConfig(
        ai=AIConfig(
            category="cloud",
            provider="gemini",
            model="gemini-2.5-flash",
            api_key_env="GEMINI_API_KEY",
            tasks=TaskModelsConfig(
                persona_generation="gemini-2.5-flash",
                ux_analysis="gemini-2.5-pro",
            ),
        )
    )

    saved_path = save_config(cfg, path=target_file)
    assert saved_path == target_file
    assert target_file.exists()

    loaded = load_config(custom_path=target_file)
    assert loaded.ai.category == "cloud"
    assert loaded.ai.provider == "gemini"
    assert loaded.ai.model == "gemini-2.5-flash"
    assert loaded.ai.tasks.persona_generation == "gemini-2.5-flash"
    assert loaded.ai.tasks.ux_analysis == "gemini-2.5-pro"
