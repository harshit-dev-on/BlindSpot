"""Configuration loading, environment variable override resolution, and persistence."""

import os
from pathlib import Path
import sys
from typing import Any, Dict, Optional, Union

# Use standard library tomllib in Python 3.11+
if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib  # type: ignore

from blindspot.config.models import AIConfig, BlindSpotConfig, TaskModelsConfig


DEFAULT_CONFIG_FILENAMES = ("blindspot.toml", ".blindspot.toml")


def get_user_config_path() -> Path:
    """Return user-level configuration path ~/.blindspot/config.toml."""
    return Path.home() / ".blindspot" / "config.toml"


def find_config_file(custom_path: Optional[Union[str, Path]] = None) -> Optional[Path]:
    """Locate configuration file from custom path, working directory, or home directory."""
    if custom_path:
        p = Path(custom_path)
        if p.is_file():
            return p
        raise FileNotFoundError(f"Specified configuration file '{custom_path}' does not exist.")

    # 1. Check current directory
    cwd = Path.cwd()
    for name in DEFAULT_CONFIG_FILENAMES:
        candidate = cwd / name
        if candidate.is_file():
            return candidate

    # 2. Check user home directory
    user_config = get_user_config_path()
    if user_config.is_file():
        return user_config

    return None


def load_config_file(path: Path) -> Dict[str, Any]:
    """Parse a TOML configuration file into a dictionary."""
    try:
        with open(path, "rb") as f:
            return tomllib.load(f)
    except Exception as exc:
        raise ValueError(f"Failed to parse TOML configuration from '{path}': {exc}") from exc


def load_config(
    custom_path: Optional[Union[str, Path]] = None,
    category: Optional[str] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    base_url: Optional[str] = None,
    api_key_env: Optional[str] = None,
    timeout: Optional[float] = None,
) -> BlindSpotConfig:
    """Load configuration with precedence: CLI flags > Env vars > Config file > Defaults."""
    raw_data: Dict[str, Any] = {}

    # 1. Load from file if found
    config_file = find_config_file(custom_path)
    if config_file:
        raw_data = load_config_file(config_file)

    # Allow configuration either in [ai] table or at top-level
    ai_data: Dict[str, Any] = raw_data.get("ai", {})
    if not ai_data and ("provider" in raw_data or "model" in raw_data):
        ai_data = raw_data

    # 2. Apply Environment Variables
    if os.environ.get("BLINDSPOT_CATEGORY"):
        ai_data["category"] = os.environ["BLINDSPOT_CATEGORY"]
    if os.environ.get("BLINDSPOT_PROVIDER"):
        ai_data["provider"] = os.environ["BLINDSPOT_PROVIDER"]
    if os.environ.get("BLINDSPOT_MODEL"):
        ai_data["model"] = os.environ["BLINDSPOT_MODEL"]
    if os.environ.get("BLINDSPOT_BASE_URL"):
        ai_data["base_url"] = os.environ["BLINDSPOT_BASE_URL"]
    if os.environ.get("BLINDSPOT_API_KEY_ENV"):
        ai_data["api_key_env"] = os.environ["BLINDSPOT_API_KEY_ENV"]
    if os.environ.get("BLINDSPOT_API_KEY"):
        ai_data["api_key"] = os.environ["BLINDSPOT_API_KEY"]
    if os.environ.get("BLINDSPOT_TIMEOUT"):
        try:
            ai_data["timeout"] = float(os.environ["BLINDSPOT_TIMEOUT"])
        except ValueError:
            pass

    # 3. Apply Explicit CLI Overrides
    if category:
        ai_data["category"] = category
    if provider:
        ai_data["provider"] = provider
    if model:
        ai_data["model"] = model
    if base_url:
        ai_data["base_url"] = base_url
    if api_key_env:
        ai_data["api_key_env"] = api_key_env
    if timeout is not None:
        ai_data["timeout"] = timeout

    ai_config = AIConfig(**ai_data)
    return BlindSpotConfig(ai=ai_config)


def save_config(config: BlindSpotConfig, path: Optional[Union[str, Path]] = None) -> Path:
    """Save a BlindSpotConfig to a TOML file.

    Defaults to the user-level configuration path (~/.blindspot/config.toml).
    Does NOT store sensitive credentials if api_key_env is defined.
    """
    target_path = Path(path) if path else get_user_config_path()
    target_path.parent.mkdir(parents=True, exist_ok=True)

    ai = config.ai

    lines = [
        "# BlindSpot Configuration File",
        "# Generated automatically by `blindspot setup`",
        "",
        "[ai]",
        f'category = "{ai.category}"',
        f'provider = "{ai.provider}"',
        f'model = "{ai.model}"',
    ]

    if ai.base_url:
        lines.append(f'base_url = "{ai.base_url}"')

    if ai.api_key:
        lines.append(f'api_key = "{ai.api_key}"')
    if ai.api_key_env:
        lines.append(f'api_key_env = "{ai.api_key_env}"')

    lines.append(f"timeout = {ai.timeout}")
    lines.append("")

    # Task models section for future pipeline extensibility
    tasks = ai.tasks
    lines.append("[ai.tasks]")
    if tasks.persona_generation:
        lines.append(f'persona_generation = "{tasks.persona_generation}"')
    if tasks.task_planning:
        lines.append(f'task_planning = "{tasks.task_planning}"')
    if tasks.ux_analysis:
        lines.append(f'ux_analysis = "{tasks.ux_analysis}"')
    if tasks.report_generation:
        lines.append(f'report_generation = "{tasks.report_generation}"')
    lines.append("")

    content = "\n".join(lines)
    with open(target_path, "w", encoding="utf-8") as f:
        f.write(content)

    return target_path
