"""Unit tests for BlindSpot session, state, and coverage tracking."""

import json
from pathlib import Path
import pytest
from blindspot.core.session import CoverageTracker, RunSession, ScanMode, TokenBudget


def test_token_budget_tracking():
    budget = TokenBudget(max_budget_dollars=1.0)
    assert not budget.is_exceeded()

    # Record some tokens
    budget.record_usage(prompt_tokens=100_000, completion_tokens=50_000)
    assert budget.prompt_tokens == 100_000
    assert budget.completion_tokens == 50_000
    assert budget.total_tokens == 150_000
    assert budget.estimated_cost_dollars > 0.0
    assert not budget.is_exceeded()

    # Exceed budget
    budget.record_usage(prompt_tokens=10_000_000, completion_tokens=5_000_000)
    assert budget.is_exceeded()


def test_coverage_tracker():
    tracker = CoverageTracker(elements_discovered_count=10)
    assert tracker.element_coverage_ratio == 0.0

    tracker.record_visit("https://example.com")
    tracker.record_visit("https://example.com/pricing")
    assert len(tracker.urls_visited) == 2

    tracker.record_interaction("btn-signup")
    tracker.record_interaction("input-email")
    assert len(tracker.elements_interacted) == 2
    assert tracker.element_coverage_ratio == 0.2

    tracker.record_wcag("1.4.3")
    assert "1.4.3" in tracker.wcag_criteria_evaluated

    d = tracker.to_dict()
    assert d["elements_interacted_count"] == 2
    assert d["element_coverage_ratio"] == 0.2


def test_run_session_lifecycle(tmp_path: Path):
    session = RunSession.create(
        target_url="https://example.com",
        scan_mode=ScanMode.DEEP,
        max_budget_dollars=5.0,
        output_dir=tmp_path,
    )
    assert session.status == "running"
    assert session.scan_mode == ScanMode.DEEP
    assert session.run_id.startswith("blindspot_")
    assert "https://example.com" in session.coverage.urls_visited

    # Add notes and findings
    session.notes["test_user"] = "alex@example.com"
    session.findings_count += 2
    session.usability_issues_count += 1
    session.accessibility_issues_count += 1

    session.complete("completed")
    assert session.status == "completed"
    assert session.ended_at is not None
    assert session.duration_seconds >= 0.0

    # Save state
    state_file = session.save_state()
    assert state_file.is_file()

    with open(state_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["run_id"] == session.run_id
    assert data["target_url"] == "https://example.com"
    assert data["scan_mode"] == "deep"
    assert data["notes"]["test_user"] == "alex@example.com"
    assert data["findings_count"] == 2
