"""Agent Skills management, validation, and export module following the open standard.

Conforms to the Agent Skills specification (standardized under the Linux Foundation / Agentic AI Foundation).
"""

from dataclasses import dataclass, field
import os
from pathlib import Path
import re
import shutil
from typing import Any, Dict, List, Optional
import yaml


@dataclass
class SkillMetadata:
    """Parsed metadata and frontmatter from an Agent Skill."""

    name: str
    description: str
    version: str = "1.0.0"
    author: Optional[str] = None
    allowed_tools: Optional[str] = None
    license: Optional[str] = None
    compatibility: Optional[str] = None
    raw_frontmatter: Dict[str, Any] = field(default_factory=dict)
    body: str = ""
    skill_path: Optional[Path] = None


@dataclass
class SkillValidationResult:
    """Outcome of validating a SKILL.md file against the Agent Skills specification."""

    name: str
    path: Path
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    token_estimate: int = 0


def get_bundled_skills_dir() -> Path:
    """Return the directory containing packaged BlindSpot skills."""
    return Path(__file__).parent


def parse_skill_file(skill_md_path: Path) -> SkillMetadata:
    """Parse a SKILL.md file into YAML frontmatter and markdown body."""
    if not skill_md_path.is_file():
        raise FileNotFoundError(f"Skill file not found: {skill_md_path}")

    content = skill_md_path.read_text(encoding="utf-8")
    
    # Standard YAML frontmatter regex: starts with ---, ends with ---
    pattern = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)
    match = pattern.match(content)

    if not match:
        raise ValueError(
            f"File {skill_md_path} does not contain valid YAML frontmatter delimiters ('---')"
        )

    frontmatter_raw = match.group(1)
    body = match.group(2).strip()

    data = yaml.safe_load(frontmatter_raw) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML frontmatter in {skill_md_path} is not a valid dictionary mapping")

    name = str(data.get("name", "")).strip()
    description = str(data.get("description", "")).strip()

    # Metadata map
    meta_dict = data.get("metadata", {})
    if not isinstance(meta_dict, dict):
        meta_dict = {}

    version = meta_dict.get("version", data.get("version", "1.0.0"))
    author = meta_dict.get("author", data.get("author"))
    allowed_tools = data.get("allowed-tools") or data.get("allowed_tools")
    license_str = data.get("license")
    compat_str = data.get("compatibility")

    return SkillMetadata(
        name=name,
        description=description,
        version=str(version),
        author=author,
        allowed_tools=allowed_tools,
        license=license_str,
        compatibility=compat_str,
        raw_frontmatter=data,
        body=body,
        skill_path=skill_md_path,
    )


def validate_skill(skill_md_path: Path) -> SkillValidationResult:
    """Validate a SKILL.md file against the Agent Skills specification checklist."""
    errors: List[str] = []
    warnings: List[str] = []

    try:
        meta = parse_skill_file(skill_md_path)
    except Exception as exc:
        return SkillValidationResult(
            name=skill_md_path.parent.name,
            path=skill_md_path,
            is_valid=False,
            errors=[f"Failed to parse skill: {exc}"],
        )

    # 1. Name validation
    # Constraints: 1-64 chars, lowercase, numbers, hyphens only, no consecutive hyphens, no start/end hyphen
    # Must match parent folder name
    parent_dir_name = skill_md_path.parent.name
    name_regex = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

    if not meta.name:
        errors.append("Missing required 'name' in YAML frontmatter.")
    elif len(meta.name) > 64:
        errors.append(f"Skill name '{meta.name}' exceeds 64 characters ({len(meta.name)} chars).")
    elif not name_regex.match(meta.name):
        errors.append(
            f"Invalid skill name '{meta.name}'. Must contain only lowercase letters, "
            "numbers, and single hyphens without leading or trailing hyphens."
        )

    if meta.name != parent_dir_name:
        errors.append(
            f"Skill name '{meta.name}' does not match parent directory name '{parent_dir_name}'."
        )

    # 2. Description validation
    # Constraints: 1-1024 chars, non-empty, actionable
    if not meta.description:
        errors.append("Missing required 'description' in YAML frontmatter.")
    elif len(meta.description) > 1024:
        errors.append(
            f"Skill description exceeds 1024 characters ({len(meta.description)} chars)."
        )
    elif len(meta.description) < 15:
        warnings.append("Skill description is very short; recommended to include trigger keywords.")

    # 3. Version in metadata
    if not meta.version:
        warnings.append("Version is missing in metadata; default '1.0.0' assumed.")

    # 4. Body structure checklist
    # Check for explicit Output Format header (e.g. ## Output Format)
    if not re.search(r"^#{1,4}\s+output format", meta.body, re.IGNORECASE | re.MULTILINE):
        errors.append("Missing explicit '## Output Format' heading in markdown body.")

    # Check for explicit Rules header (e.g. ## Rules)
    if not re.search(r"^#{1,4}\s+rules", meta.body, re.IGNORECASE | re.MULTILINE):
        errors.append("Missing explicit '## Rules' heading in markdown body.")
    else:
        # Check that at least 3 rules are specified
        rules_matches = re.findall(r"^\s*\d+\.\s+", meta.body, re.MULTILINE)
        if len(rules_matches) < 3:
            warnings.append(
                f"Found only {len(rules_matches)} numbered rules. Spec recommends at least 3 explicit rules."
            )

    # Check for Examples header (e.g. ## Example)
    if not re.search(r"^#{1,4}\s+example", meta.body, re.IGNORECASE | re.MULTILINE):
        warnings.append("Recommended to include at least one '## Example' with sample input/output.")

    # 5. Token estimate (approx 4 chars per token)
    full_text = skill_md_path.read_text(encoding="utf-8")
    token_est = len(full_text) // 4
    if token_est > 3000:
        warnings.append(
            f"Estimated token footprint ({token_est} tokens) is high. Consider moving long references into 'references/' directory."
        )

    is_valid = len(errors) == 0

    return SkillValidationResult(
        name=meta.name or parent_dir_name,
        path=skill_md_path,
        is_valid=is_valid,
        errors=errors,
        warnings=warnings,
        token_estimate=token_est,
    )


def list_bundled_skills() -> List[SkillMetadata]:
    """Discover all packaged skills bundled in BlindSpot."""
    base_dir = get_bundled_skills_dir()
    skills: List[SkillMetadata] = []

    for item in sorted(base_dir.iterdir()):
        if item.is_dir() and (item / "SKILL.md").is_file():
            try:
                meta = parse_skill_file(item / "SKILL.md")
                skills.append(meta)
            except Exception:
                continue

    return skills


def install_skills_to_workspace(
    target_root: Path,
    targets: Optional[List[str]] = None,
) -> Dict[str, List[Path]]:
    """Install bundled skills into target directory locations.

    Args:
        target_root: The root of the workspace.
        targets: List of target locations: 'agents' (.agents/skills), 'github' (.github/skills), or None (both).

    Returns:
        Dict mapping location name to list of installed SKILL.md paths.
    """
    if targets is None:
        targets = ["agents", "github"]

    base_dir = get_bundled_skills_dir()
    installed: Dict[str, List[Path]] = {}

    destination_maps = {
        "agents": target_root / ".agents" / "skills",
        "github": target_root / ".github" / "skills",
    }

    for target_key in targets:
        dest_dir = destination_maps.get(target_key)
        if not dest_dir:
            continue

        dest_dir.mkdir(parents=True, exist_ok=True)
        installed[target_key] = []

        for item in base_dir.iterdir():
            if item.is_dir() and (item / "SKILL.md").is_file():
                target_skill_dir = dest_dir / item.name
                target_skill_dir.mkdir(parents=True, exist_ok=True)
                
                target_file = target_skill_dir / "SKILL.md"
                shutil.copy2(item / "SKILL.md", target_file)
                installed[target_key].append(target_file)

    return installed
