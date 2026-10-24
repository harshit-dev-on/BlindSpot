"""Unit tests for internal domain knowledge playbooks and loader."""

import pytest
from blindspot.knowledge import (
    get_playbooks_for_persona,
    list_available_playbooks,
    load_playbook,
)


def test_list_available_playbooks():
    playbooks = list_available_playbooks()
    assert len(playbooks) >= 4
    names = [p["name"] for p in playbooks]
    assert "wcag_contrast" in names
    assert "wcag_keyboard" in names
    assert "wcag_target_size" in names
    assert "nielsen_heuristics" in names


def test_load_playbook():
    contrast_doc = load_playbook("wcag_contrast")
    assert contrast_doc is not None
    assert "4.5:1" in contrast_doc
    assert "1.4.3" in contrast_doc

    missing = load_playbook("non_existent_playbook")
    assert missing is None


def test_get_playbooks_for_persona():
    # Screen reader persona
    sr_content = get_playbooks_for_persona(assistive_tech="Screen Reader (NVDA)")
    assert "wcag_keyboard" in sr_content
    assert "nielsen_heuristics" in sr_content

    # Low vision magnifier persona
    mag_content = get_playbooks_for_persona(assistive_tech="Screen Magnifier")
    assert "wcag_contrast" in mag_content

    # Mobile touch persona
    mobile_content = get_playbooks_for_persona(assistive_tech="Touch Screen Mobile")
    assert "wcag_target_size" in mobile_content
