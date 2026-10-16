"""Tests for Agent Skills discovery, validation, installation, and CLI subcommands."""

from pathlib import Path
import pytest
from typer.testing import CliRunner

from blindspot.cli import app
from blindspot.skills.manager import (
    get_bundled_skills_dir,
    install_skills_to_workspace,
    list_bundled_skills,
    parse_skill_file,
    validate_skill,
)

runner = CliRunner()


def test_bundled_skills_exist():
    """Verify all bundled skills are discoverable."""
    skills = list_bundled_skills()
    skill_names = {s.name for s in skills}
    expected = {
        "blindspot-ux-audit",
        "blindspot-verify-fix",
        "blindspot-wcag-audit",
        "blindspot-persona-designer",
    }
    assert expected.issubset(skill_names)


def test_bundled_skills_conform_to_spec():
    """Verify every bundled skill passes specification validation with 0 errors."""
    skills = list_bundled_skills()
    assert len(skills) >= 4

    for skill in skills:
        result = validate_skill(skill.skill_path)
        assert result.is_valid is True, f"Skill {result.name} failed validation: {result.errors}"
        assert len(result.errors) == 0
        assert skill.version == "1.0.0"
        assert len(skill.description) > 20
        # Progressive disclosure guideline: instructions within ~2500 tokens
        assert result.token_estimate < 2500


def test_validate_skill_detects_invalid_name(tmp_path: Path):
    """Verify validator catches illegal name formats and directory mismatches."""
    bad_dir = tmp_path / "Invalid_Name"
    bad_dir.mkdir()
    bad_file = bad_dir / "SKILL.md"
    bad_file.write_text(
        """---
name: Invalid_Name
description: Test skill with uppercase and underscore
metadata:
  version: "1.0.0"
---

# Title
## Output Format
Some format
## Rules
1. Rule one
2. Rule two
3. Rule three
""",
        encoding="utf-8",
    )

    result = validate_skill(bad_file)
    assert result.is_valid is False
    assert any("lowercase" in err.lower() for err in result.errors)


def test_validate_skill_detects_missing_sections(tmp_path: Path):
    """Verify validator flags missing Output Format or Rules sections."""
    skill_dir = tmp_path / "test-skill"
    skill_dir.mkdir()
    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text(
        """---
name: test-skill
description: Minimal test skill lacking required structure
metadata:
  version: "1.0.0"
---

# Test Role
Just some text without output format or rules.
""",
        encoding="utf-8",
    )

    result = validate_skill(skill_file)
    assert result.is_valid is False
    assert any("output format" in err.lower() for err in result.errors)
    assert any("rules" in err.lower() for err in result.errors)


def test_install_skills_to_workspace(tmp_path: Path):
    """Verify skill installation exports to .agents/skills and .github/skills."""
    installed = install_skills_to_workspace(tmp_path, targets=["agents", "github"])

    assert "agents" in installed
    assert "github" in installed
    assert len(installed["agents"]) >= 4
    assert len(installed["github"]) >= 4

    for skill_file in installed["agents"]:
        assert skill_file.is_file()
        assert (tmp_path / ".agents" / "skills").is_dir()

    for skill_file in installed["github"]:
        assert skill_file.is_file()
        assert (tmp_path / ".github" / "skills").is_dir()


def test_cli_skill_list():
    """Verify 'blindspot skill list' outputs table of bundled skills."""
    result = runner.invoke(app, ["skill", "list"])
    assert result.exit_code == 0
    assert "blindspot-ux-audit" in result.output
    assert "blindspot-verify-fix" in result.output
    assert "blindspot-wcag-audit" in result.output
    assert "blindspot-persona-designer" in result.output


def test_cli_skill_validate():
    """Verify 'blindspot skill validate' validates all bundled skills."""
    result = runner.invoke(app, ["skill", "validate"])
    assert result.exit_code == 0
    assert "[PASS]" in result.output
    assert "blindspot-ux-audit" in result.output


def test_cli_skill_validate_invalid_path(tmp_path: Path):
    """Verify 'blindspot skill validate' on a missing path returns exit code 2."""
    missing = tmp_path / "nonexistent"
    result = runner.invoke(app, ["skill", "validate", str(missing)])
    assert result.exit_code == 2


def test_cli_skill_install(tmp_path: Path):
    """Verify 'blindspot skill install' exports to specified destination."""
    result = runner.invoke(app, ["skill", "install", "--dest", str(tmp_path)])
    assert result.exit_code == 0
    assert (tmp_path / ".agents" / "skills" / "blindspot-ux-audit" / "SKILL.md").is_file()
    assert (tmp_path / ".github" / "skills" / "blindspot-ux-audit" / "SKILL.md").is_file()
