"""Domain knowledge playbook loader for BlindSpot persona agents.

Injects specialized WCAG 2.2 and UX heuristic playbooks into persona prompts
based on the testing context.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

KNOWLEDGE_ROOT = Path(__file__).parent


def list_available_playbooks() -> List[Dict[str, str]]:
    """List all available internal domain knowledge playbooks."""
    playbooks: List[Dict[str, str]] = []
    if not KNOWLEDGE_ROOT.is_dir():
        return playbooks

    for md_file in sorted(KNOWLEDGE_ROOT.glob("**/*.md")):
        category = md_file.parent.name
        name = md_file.stem
        playbooks.append({
            "category": category,
            "name": name,
            "path": str(md_file),
        })

    return playbooks


def load_playbook(name: str, category: Optional[str] = None) -> Optional[str]:
    """Load text content of a specific knowledge playbook."""
    if category:
        target = KNOWLEDGE_ROOT / category / f"{name}.md"
        if target.is_file():
            return target.read_text(encoding="utf-8")

    # Search recursively
    matches = list(KNOWLEDGE_ROOT.glob(f"**/{name}.md"))
    if matches:
        return matches[0].read_text(encoding="utf-8")

    return None


def get_playbooks_for_persona(assistive_tech: Optional[str] = None, tech_literacy: Optional[str] = None) -> str:
    """Select and assemble relevant playbooks based on persona attributes."""
    selected_names = ["nielsen_heuristics"]

    if assistive_tech:
        at_lower = assistive_tech.lower()
        if "screen reader" in at_lower or "aria" in at_lower or "voice" in at_lower:
            selected_names.extend(["wcag_keyboard"])
        if "magnifier" in at_lower or "low vision" in at_lower:
            selected_names.extend(["wcag_contrast"])
        if "keyboard" in at_lower or "motor" in at_lower:
            selected_names.extend(["wcag_keyboard", "wcag_target_size"])
        if "mobile" in at_lower or "touch" in at_lower:
            selected_names.extend(["wcag_target_size"])

    # If novice / senior, emphasize error recovery and clarity
    if tech_literacy and tech_literacy.lower() in ("low", "novice", "beginner"):
        if "wcag_contrast" not in selected_names:
            selected_names.append("wcag_contrast")

    sections: List[str] = []
    for name in selected_names:
        content = load_playbook(name)
        if content:
            sections.append(f"--- PLAYBOOK: {name} ---\n{content}\n")

    return "\n".join(sections)
