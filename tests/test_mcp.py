"""Comprehensive unit and integration tests for BlindSpot Model Context Protocol (MCP) server."""

import asyncio
import json
from pathlib import Path
import pytest

from blindspot.mcp.comparison import compare_test_runs
from blindspot.mcp.server import create_mcp_server
from blindspot.mcp.tools import (
    tool_get_findings,
    tool_get_test_results,
    tool_get_test_status,
    tool_inspect_website,
    tool_verify_fixes,
)
from blindspot.web.manager import job_manager


@pytest.fixture
def mcp_env(tmp_path, monkeypatch):
    """Fixture with isolated reports directory for MCP testing."""
    rep_dir = tmp_path / "mcp_reports"
    rep_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(job_manager, "reports_root", rep_dir)
    monkeypatch.setattr(job_manager, "_runs", {})
    return rep_dir


def test_mcp_server_tool_registration():
    """Verify that the MCP server correctly registers all 5 tools."""
    server = create_mcp_server()
    tools = asyncio.run(server.list_tools())
    tool_names = {t.name for t in tools}

    expected_tools = {
        "inspect_website",
        "get_test_status",
        "get_test_results",
        "get_findings",
        "verify_fixes",
    }
    assert expected_tools.issubset(tool_names), f"Missing tools: {expected_tools - tool_names}"


def test_inspect_website_valid_input(mcp_env, monkeypatch):
    """inspect_website tool should validate inputs and start background testing."""
    monkeypatch.setattr(job_manager, "start_run_background", lambda rid: None)

    res = tool_inspect_website(
        url="https://example.com",
        context="An informational reference website for testing protocols.",
        personas=2,
    )

    assert "run_id" in res
    assert res["status"] in ("queued", "running")
    assert res["target_url"] == "https://example.com"
    assert "instructions" in res


def test_inspect_website_invalid_url(mcp_env):
    """inspect_website tool should reject invalid URLs."""
    res = tool_inspect_website(
        url="not-a-valid-url",
        context="Testing valid context description for website.",
    )
    assert res.get("error") == "INVALID_URL"
    assert "protocol scheme" in res.get("message", "").lower() or "invalid" in res.get("message", "").lower()


@pytest.mark.parametrize(
    "blocked_url",
    [
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://169.254.169.254/latest/meta-data/",
        "http://10.0.0.1/admin",
        "http://metadata.google.internal",
    ],
)
def test_inspect_website_ssrf_protection(mcp_env, blocked_url):
    """inspect_website tool must block SSRF, localhost, and metadata endpoints."""
    res = tool_inspect_website(
        url=blocked_url,
        context="Testing SSRF security protections.",
    )
    assert res.get("error") == "SECURITY_BLOCKED"


def test_inspect_website_invalid_context(mcp_env):
    """inspect_website tool should reject short or empty contexts."""
    res = tool_inspect_website(
        url="https://example.com",
        context="short",
    )
    assert res.get("error") == "INVALID_CONTEXT"


def test_get_test_status_active_and_historical(mcp_env, monkeypatch):
    """get_test_status should report status for active and historical runs."""
    monkeypatch.setattr(job_manager, "start_run_background", lambda rid: None)

    # 1. Active run
    init_res = tool_inspect_website(
        url="https://example.com",
        context="A valid documentation website context.",
        personas=2,
    )
    run_id = init_res["run_id"]

    status_res = tool_get_test_status(run_id)
    assert status_res["run_id"] == run_id
    assert status_res["status"] in ("queued", "running")

    # 2. Historical run on disk
    hist_dir = mcp_env / "run_hist_123"
    hist_dir.mkdir(parents=True, exist_ok=True)
    (hist_dir / "report.json").write_text(
        json.dumps({
            "target_url": "https://historical.example.com",
            "task_metrics": {"total_tasks": 4, "passed_tasks": 4, "failed_tasks": 0},
        }),
        encoding="utf-8",
    )

    hist_status = tool_get_test_status("run_hist_123")
    assert hist_status["status"] == "completed"
    assert hist_status["target_url"] == "https://historical.example.com"
    assert hist_status["has_report"] is True


def test_get_test_status_invalid_or_missing_id(mcp_env):
    """get_test_status should handle invalid or non-existent run IDs."""
    # Malformed ID with traversal
    res_malformed = tool_get_test_status("../../etc/passwd")
    assert res_malformed.get("error") == "INVALID_RUN_ID"

    # Non-existent run ID
    res_missing = tool_get_test_status("run_does_not_exist_999")
    assert res_missing.get("error") == "NOT_FOUND"


def test_get_test_results_completed_run(mcp_env):
    """get_test_results should return structured summary and report locations."""
    run_dir = mcp_env / "run_results_123"
    run_dir.mkdir(parents=True, exist_ok=True)

    sample_report = {
        "report_id": "rep_abc",
        "target_url": "https://example.com",
        "context": "An e-commerce store context",
        "task_metrics": {
            "total_tasks": 5,
            "passed_tasks": 4,
            "failed_tasks": 1,
            "inconclusive_tasks": 0,
        },
        "findings": [
            {
                "id": "finding_1",
                "title": "Missing alt text on logo",
                "category": "OBJECTIVE_DEFECT",
                "severity": "Low",
                "affected_page_url": "https://example.com",
                "suggested_improvement": "Add alt='Company Logo'",
            },
            {
                "id": "finding_2",
                "title": "Checkout button contrast is low",
                "category": "USABILITY_OBSERVATION",
                "severity": "Medium",
                "affected_page_url": "https://example.com/cart",
                "suggested_improvement": "Increase button color contrast ratio to 4.5:1",
            },
        ],
        "disclaimer": "Simulated personas disclaimer",
    }
    (run_dir / "report.json").write_text(json.dumps(sample_report), encoding="utf-8")
    (run_dir / "report.html").write_text("<html>Report</html>", encoding="utf-8")

    res = tool_get_test_results("run_results_123")
    assert res["status"] == "completed"
    assert res["target_url"] == "https://example.com"
    assert res["summary_counts"]["total_findings"] == 2
    assert res["summary_counts"]["verified_defects"] == 1
    assert res["summary_counts"]["usability_observations"] == 1
    assert res["report_paths"]["json_report"] is not None
    assert res["report_paths"]["html_report"] is not None
    assert len(res["top_findings"]) == 2


def test_get_findings_filtering(mcp_env):
    """get_findings should support filtering by severity and category."""
    run_dir = mcp_env / "run_findings_123"
    run_dir.mkdir(parents=True, exist_ok=True)

    sample_report = {
        "target_url": "https://example.com",
        "findings": [
            {
                "id": "f_1",
                "title": "Broken link to terms",
                "category": "OBJECTIVE_DEFECT",
                "severity": "Critical",
                "confidence": 0.95,
                "affected_page_url": "https://example.com",
                "supporting_evidence": ["HTTP 404 encountered"],
                "reproduction_steps": ["Click Terms link in footer"],
                "suggested_improvement": "Update footer terms URL",
                "expected_benefit": "Restores legal navigation compliance",
            },
            {
                "id": "f_2",
                "title": "Unclear search bar placeholder",
                "category": "USABILITY_OBSERVATION",
                "severity": "Low",
                "confidence": 0.70,
                "affected_page_url": "https://example.com",
                "supporting_evidence": ["Placeholder is '...'"],
                "reproduction_steps": ["Observe search input"],
                "suggested_improvement": "Change placeholder to 'Search products...'",
                "expected_benefit": "Improves discoverability",
            },
        ],
    }
    (run_dir / "report.json").write_text(json.dumps(sample_report), encoding="utf-8")

    # 1. Unfiltered
    res_all = tool_get_findings("run_findings_123")
    assert res_all["findings_count"] == 2

    # 2. Filter by severity: Critical
    res_crit = tool_get_findings("run_findings_123", severity="Critical")
    assert res_crit["findings_count"] == 1
    assert res_crit["findings"][0]["id"] == "f_1"

    # 3. Filter by category: usability_observation
    res_obs = tool_get_findings("run_findings_123", category="usability_observation")
    assert res_obs["findings_count"] == 1
    assert res_obs["findings"][0]["id"] == "f_2"


def test_verify_fixes_comparison_logic():
    """compare_test_runs should accurately categorize resolved, recurring, and new issues."""
    ref_report = {
        "task_metrics": {"total_tasks": 2, "passed_tasks": 1, "failed_tasks": 1},
        "findings": [
            {
                "id": "ref_1",
                "title": "Broken checkout navigation",
                "category": "OBJECTIVE_DEFECT",
                "severity": "Critical",
                "affected_page_url": "https://example.com/checkout",
            },
            {
                "id": "ref_2",
                "title": "Footer logo missing alt attribute",
                "category": "OBJECTIVE_DEFECT",
                "severity": "Low",
                "affected_page_url": "https://example.com",
            },
        ],
    }

    # Scenario:
    # - ref_1 was fixed (no longer detected, task passed in new run)
    # - ref_2 is still present (recurring)
    # - A new issue (f_new) was detected
    cur_report = {
        "task_metrics": {"total_tasks": 2, "passed_tasks": 2, "failed_tasks": 0},
        "findings": [
            {
                "id": "cur_1",
                "title": "Footer logo missing alt attribute",
                "category": "OBJECTIVE_DEFECT",
                "severity": "Low",
                "affected_page_url": "https://example.com",
            },
            {
                "id": "cur_2",
                "title": "Color contrast issue on newsletter button",
                "category": "USABILITY_OBSERVATION",
                "severity": "Medium",
                "affected_page_url": "https://example.com",
            },
        ],
    }

    diff = compare_test_runs(current_report=cur_report, reference_report=ref_report)

    assert diff["summary"]["resolved_count"] == 1
    assert diff["summary"]["recurring_count"] == 1
    assert diff["summary"]["new_count"] == 1
    assert diff["verdict"] == "PARTIALLY_RESOLVED"

    assert diff["resolved"][0]["reference_finding_id"] == "ref_1"
    assert diff["recurring"][0]["reference_finding_id"] == "ref_2"
    assert diff["new"][0]["current_finding_id"] == "cur_2"


def test_verify_fixes_tool_direct_comparison(mcp_env):
    """tool_verify_fixes should compare two completed runs."""
    ref_dir = mcp_env / "run_ref_001"
    ref_dir.mkdir(parents=True, exist_ok=True)
    (ref_dir / "report.json").write_text(
        json.dumps({
            "target_url": "https://example.com",
            "findings": [{"id": "f_1", "title": "404 Error on About page", "severity": "High"}],
            "task_metrics": {"total_tasks": 1, "passed_tasks": 0, "failed_tasks": 1},
        }),
        encoding="utf-8",
    )

    cur_dir = mcp_env / "run_cur_002"
    cur_dir.mkdir(parents=True, exist_ok=True)
    (cur_dir / "report.json").write_text(
        json.dumps({
            "target_url": "https://example.com",
            "findings": [],  # Bug resolved!
            "task_metrics": {"total_tasks": 1, "passed_tasks": 1, "failed_tasks": 0},
        }),
        encoding="utf-8",
    )

    res = tool_verify_fixes(run_id="run_cur_002", reference_run_id="run_ref_001")
    assert res["mode"] == "comparison"
    assert res["verdict"] == "ALL_RESOLVED"
    assert res["summary"]["resolved_count"] == 1
    assert res["summary"]["recurring_count"] == 0


def test_verify_fixes_tool_start_retest(mcp_env, monkeypatch):
    """tool_verify_fixes should initiate new test run when given url, context, and reference."""
    monkeypatch.setattr(job_manager, "start_run_background", lambda rid: None)

    ref_dir = mcp_env / "run_ref_003"
    ref_dir.mkdir(parents=True, exist_ok=True)
    (ref_dir / "report.json").write_text(json.dumps({"target_url": "https://example.com", "findings": []}), encoding="utf-8")

    res = tool_verify_fixes(
        url="https://example.com",
        context="Retesting website to verify fixes.",
        reference_run_id="run_ref_003",
    )

    assert res["mode"] == "verification_retest_started"
    assert "new_run_id" in res
    assert res["reference_run_id"] == "run_ref_003"
    assert "instructions" in res


def test_mcp_never_exposes_secrets(mcp_env, monkeypatch):
    """Verify MCP tools never return API keys or environment secrets."""
    monkeypatch.setenv("GEMINI_API_KEY", "SUPER_SECRET_KEY_12345")
    monkeypatch.setenv("OPENAI_API_KEY", "SUPER_SECRET_KEY_67890")
    monkeypatch.setattr(job_manager, "start_run_background", lambda rid: None)

    # 1. Start test
    res_start = tool_inspect_website(
        url="https://example.com",
        context="Testing secrecy of credentials in MCP outputs.",
    )
    start_str = json.dumps(res_start)
    assert "SUPER_SECRET" not in start_str

    # 2. Get status
    res_status = tool_get_test_status(res_start["run_id"])
    status_str = json.dumps(res_status)
    assert "SUPER_SECRET" not in status_str
