"""BlindSpot Agent Skills Package.

Standardized Agent Skills following the open specification (Linux Foundation / Anthropic / OpenAI).
"""

from blindspot.skills.manager import (
    SkillMetadata,
    SkillValidationResult,
    get_bundled_skills_dir,
    install_skills_to_workspace,
    list_bundled_skills,
    parse_skill_file,
    validate_skill,
)

__all__ = [
    "SkillMetadata",
    "SkillValidationResult",
    "get_bundled_skills_dir",
    "install_skills_to_workspace",
    "list_bundled_skills",
    "parse_skill_file",
    "validate_skill",
]
