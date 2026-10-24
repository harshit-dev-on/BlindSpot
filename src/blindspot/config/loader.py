"""Configuration loading, environment variable override resolution, and persistence."""

import json
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


DEFAULT_CONFIG_FILENAMES = ("blindspot.toml", ".blindspot.toml", "cli-config.json")
USER_CONFIG_DIR = Path.home() / ".blindspot"
USER_CONFIG_TOML = USER_CONFIG_DIR / "config.toml"
USER_CONFIG_JSON = USER_CONFIG_DIR / "cli-config.json"
STRIX_CONFIG_JSON = Path.home() / ".strix" / "cli-config.json"


def get_user_config_path() -> Path:
    """Return user-level configuration path ~/.blindspot/config.toml."""
    return USER_CONFIG_TOML


def find_config_file(custom_path: Optional[Union[str, Path]] = None) -> Optional[Path]:
    """Locate configuration file from custom path, working directory, or home directory.

    Checks:
      1. Custom path (CLI flag --config)
      2. CWD (blindspot.toml, .blindspot.toml, cli-config.json)
      3. ~/.blindspot/config.toml
      4. ~/.blindspot/cli-config.json
      5. ~/.strix/cli-config.json (Strix parity interop)
    """
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

    # 2. Check user home directory (.blindspot/config.toml)
    if USER_CONFIG_TOML.is_file():
        return USER_CONFIG_TOML

    # 3. Check user home directory (.blindspot/cli-config.json)
    if USER_CONFIG_JSON.is_file():
        return USER_CONFIG_JSON

    # 4. Check Strix user configuration (~/.strix/cli-config.json)
    if STRIX_CONFIG_JSON.is_file():
        return STRIX_CONFIG_JSON

    return None


def load_config_file(path: Path) -> Dict[str, Any]:
    """Parse a TOML or JSON configuration file into a dictionary."""
    if path.suffix.lower() == ".json":
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # If Strix {"env": {...}} schema
            env_block = data.get("env", {}) if isinstance(data, dict) else {}
            res: Dict[str, Any] = {}
            llm_val = env_block.get("BLINDSPOT_LLM") or env_block.get("STRIX_LLM")
            if llm_val:
                cat, prov, mod = parse_model_route(str(llm_val))
                res["category"] = cat
                res["provider"] = prov
                res["model"] = mod
            api_key = env_block.get("LLM_API_KEY") or env_block.get("BLINDSPOT_API_KEY")
            if api_key:
                res["api_key"] = str(api_key).strip()
            base_url = (
                env_block.get("BLINDSPOT_BASE_URL")
                or env_block.get("LLM_API_BASE")
                or env_block.get("OPENAI_API_BASE")
                or env_block.get("OLLAMA_API_BASE")
            )
            if base_url:
                res["base_url"] = str(base_url).strip()
            timeout = env_block.get("LLM_TIMEOUT") or env_block.get("BLINDSPOT_TIMEOUT")
            if timeout:
                try:
                    res["timeout"] = float(timeout)
                except ValueError:
                    pass
            if "ai" in data and isinstance(data["ai"], dict):
                res.update(data["ai"])
            elif any(k in data for k in ("provider", "model", "category")):
                res.update({k: v for k, v in data.items() if k != "env"})
            return {"ai": res}
        except Exception as exc:
            raise ValueError(f"Failed to parse JSON configuration from '{path}': {exc}") from exc

    try:
        with open(path, "rb") as f:
            return tomllib.load(f)
    except Exception as exc:
        raise ValueError(f"Failed to parse TOML configuration from '{path}': {exc}") from exc


PROVIDER_ALIASES: Dict[str, str] = {
    "google": "gemini",
    "vertex": "gemini",
    "claude": "anthropic",
}


def parse_model_route(route: str) -> tuple[str, str, str]:
    """Parse a <provider>/<model> string into (category, provider, model).

    Supports formats like:
      'google/gemini-2.5-flash' -> ('cloud', 'gemini', 'gemini-2.5-flash')
      'gemini/gemini-3.5-flash' -> ('cloud', 'gemini', 'gemini-3.5-flash')
      'openai/gpt-4o-mini'      -> ('cloud', 'openai', 'gpt-4o-mini')
      'anthropic/claude-3-7'    -> ('cloud', 'anthropic', 'claude-3-7')
      'ollama/gemma4'           -> ('local', 'ollama', 'gemma4')
      'openrouter/...'          -> ('cloud', 'openrouter', '...')
    """
    cleaned = (route or "").strip()
    if "/" in cleaned:
        p_part, m_part = cleaned.split("/", 1)
        p = p_part.strip().lower()
        p = PROVIDER_ALIASES.get(p, p)
        category = "local" if p == "ollama" else ("custom" if p in ("custom", "openai_compatible") else "cloud")
        return category, p, m_part.strip()

    low = cleaned.lower()
    if low.startswith("gemini"):
        return "cloud", "gemini", cleaned
    if low.startswith("gpt") or low.startswith("o1") or low.startswith("o3"):
        return "cloud", "openai", cleaned
    if low.startswith("claude"):
        return "cloud", "anthropic", cleaned
    if low in ("gemma", "gemma4", "llama", "llama3", "mistral", "qwen", "phi3"):
        return "local", "ollama", cleaned

    return "cloud", "gemini", cleaned


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
    # Support universal model identifier (e.g. "gemini/gemini-1.5-flash", "ollama/gemma4", "openai/gpt-4o-mini")
    universal_llm = os.environ.get("BLINDSPOT_LLM") or os.environ.get("STRIX_LLM")
    if universal_llm:
        parsed_cat, parsed_prov, parsed_mod = parse_model_route(universal_llm)
        ai_data["category"] = parsed_cat
        ai_data["provider"] = parsed_prov
        ai_data["model"] = parsed_mod

    # Universal LLM API key (identical to Strix and other coding tools)
    if os.environ.get("LLM_API_KEY"):
        ai_data["api_key"] = os.environ["LLM_API_KEY"].strip()

    if os.environ.get("BLINDSPOT_CATEGORY"):
        ai_data["category"] = os.environ["BLINDSPOT_CATEGORY"]
    if os.environ.get("BLINDSPOT_PROVIDER"):
        ai_data["provider"] = os.environ["BLINDSPOT_PROVIDER"]
    if os.environ.get("BLINDSPOT_MODEL"):
        ai_data["model"] = os.environ["BLINDSPOT_MODEL"]
    # Universal Base URL (Strix compatibility)
    universal_base = (
        os.environ.get("BLINDSPOT_BASE_URL")
        or os.environ.get("LLM_API_BASE")
        or os.environ.get("OPENAI_API_BASE")
        or os.environ.get("OLLAMA_API_BASE")
    )
    if universal_base:
        ai_data["base_url"] = universal_base.strip()
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
    """Save a BlindSpotConfig to configuration files.

    Saves to:
      1. ~/.blindspot/config.toml (standard TOML configuration)
      2. ~/.blindspot/cli-config.json (standard Strix JSON format for interoperability)
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

    # Also save Strix-format cli-config.json
    try:
        json_path = target_path.parent / "cli-config.json"
        active_route = f"{ai.provider}/{ai.model}"
        env_block: Dict[str, Any] = {
            "BLINDSPOT_LLM": active_route,
            "STRIX_LLM": active_route,
        }
        if ai.api_key:
            env_block["LLM_API_KEY"] = ai.api_key
        if ai.base_url:
            env_block["LLM_API_BASE"] = ai.base_url
        if ai.timeout:
            env_block["LLM_TIMEOUT"] = str(ai.timeout)
        with open(json_path, "w", encoding="utf-8") as jf:
            json.dump({"env": env_block}, jf, indent=2)
    except OSError:
        pass

    return target_path


def persist_current() -> None:
    """Merge currently active settings and env vars into user config (~/.blindspot/).

    Identical to Strix's persist_current(), ensuring settings survive across shell sessions
    so the user never has to re-enter them on subsequent runs.
    """
    cfg = load_config()
    save_config(cfg)

