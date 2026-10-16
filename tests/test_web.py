"""Comprehensive tests for the BlindSpot web demonstration API and security boundaries."""

from pathlib import Path
import json
import pytest
from starlette.testclient import TestClient

from blindspot.core.runner import PipelineResult
from blindspot.reporting.models import (
    BlindSpotReport,
    FindingCategory,
    SeverityLevel,
    TaskMetricSummary,
    UXFinding,
)
from blindspot.web.app import app
from blindspot.web.manager import job_manager, RunRecord


@pytest.fixture
def client(tmp_path, monkeypatch):
    """TestClient fixture with isolated reports root."""
    reports_dir = tmp_path / "web_reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(job_manager, "reports_root", reports_dir)
    monkeypatch.setattr(job_manager, "_runs", {})
    return TestClient(app)


def test_landing_page_serves_html(client):
    """GET / should serve the HTML demonstration interface."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "BlindSpot" in resp.text
    assert "Start Automated UX Test" in resp.text


def test_create_run_valid_payload(client, monkeypatch):
    """POST /api/runs should validate URL and context and create a run."""
    # Mock background runner so real browser does not launch during unit test
    def _mock_start_bg(run_id):
        rec = job_manager.get_run(run_id)
        rec.status = "running"
        rec.events.append({"type": "stage_start", "stage": "inspection", "message": "Inspecting..."})

    monkeypatch.setattr(job_manager, "start_run_background", _mock_start_bg)

    payload = {
        "url": "https://example.com",
        "context": "An informational example website for testing domain protocols.",
        "personas": 3,
        "headed": False,
        "browser": "chromium",
    }
    resp = client.post("/api/runs", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert "run_id" in data
    assert data["target_url"] == "https://example.com"
    assert data["status"] in ("queued", "running")


def test_create_run_invalid_url_rejected(client):
    """POST /api/runs should reject invalid URLs."""
    payload = {
        "url": "not-a-valid-url",
        "context": "A test context describing website functionality.",
        "personas": 2,
    }
    resp = client.post("/api/runs", json=payload)
    assert resp.status_code == 400
    assert "Invalid URL" in resp.json()["detail"]


@pytest.mark.parametrize(
    "ssrf_url",
    [
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://169.254.169.254/latest/meta-data/",
        "http://10.0.0.1/admin",
        "http://192.168.1.1/router",
        "http://metadata.google.internal/computeMetadata/v1/",
        "http://service.local/internal",
    ],
)
def test_create_run_ssrf_blocked(client, ssrf_url):
    """POST /api/runs must strictly block localhost, private IPs, and cloud metadata."""
    payload = {
        "url": ssrf_url,
        "context": "Testing security validation for private endpoints.",
        "personas": 2,
    }
    resp = client.post("/api/runs", json=payload)
    assert resp.status_code == 400
    assert "Security Policy Blocked" in resp.json()["detail"]


def test_create_run_invalid_context_rejected(client):
    """POST /api/runs should reject empty or insufficient context."""
    payload = {
        "url": "https://example.com",
        "context": "short",  # < 10 characters
        "personas": 2,
    }
    resp = client.post("/api/runs", json=payload)
    assert resp.status_code == 400
    assert "Invalid Context" in resp.json()["detail"]


def test_get_run_status_and_list(client, monkeypatch):
    """GET /api/runs and GET /api/runs/{run_id} should return accurate statuses."""
    monkeypatch.setattr(job_manager, "start_run_background", lambda r: None)

    # 1. Create a run
    resp = client.post("/api/runs", json={
        "url": "https://example.com",
        "context": "A valid online encyclopedia website context.",
        "personas": 2,
    })
    assert resp.status_code == 201
    run_id = resp.json()["run_id"]

    # 2. Get status
    resp_status = client.get(f"/api/runs/{run_id}")
    assert resp_status.status_code == 200
    assert resp_status.json()["run_id"] == run_id
    assert resp_status.json()["target_url"] == "https://example.com"

    # 3. List runs
    resp_list = client.get("/api/runs")
    assert resp_list.status_code == 200
    items = resp_list.json()
    assert len(items) >= 1
    assert any(i["run_id"] == run_id for i in items)


def test_get_run_events_polling(client, monkeypatch):
    """GET /api/runs/{run_id}/events?stream=false should return event history."""
    monkeypatch.setattr(job_manager, "start_run_background", lambda r: None)

    resp = client.post("/api/runs", json={
        "url": "https://example.com",
        "context": "A valid online e-commerce website context.",
        "personas": 2,
    })
    run_id = resp.json()["run_id"]
    rec = job_manager.get_run(run_id)
    rec.events.append({"type": "stage_start", "stage": "inspection", "message": "Inspecting..."})
    rec.events.append({"type": "action_step", "step": 1, "action": "click", "page_url": "https://example.com"})

    resp_events = client.get(f"/api/runs/{run_id}/events?stream=false")
    assert resp_events.status_code == 200
    data = resp_events.json()
    assert data["run_id"] == run_id
    assert len(data["events"]) == 2
    assert data["events"][0]["stage"] == "inspection"


def test_cancel_run(client, monkeypatch):
    """POST /api/runs/{run_id}/cancel should trigger cancellation."""
    monkeypatch.setattr(job_manager, "start_run_background", lambda r: None)

    resp = client.post("/api/runs", json={
        "url": "https://example.com",
        "context": "A valid news portal website context.",
        "personas": 2,
    })
    run_id = resp.json()["run_id"]

    resp_cancel = client.post(f"/api/runs/{run_id}/cancel")
    assert resp_cancel.status_code == 200
    assert resp_cancel.json()["status"] == "cancelling"

    # Status should reflect cancellation
    rec = job_manager.get_run(run_id)
    assert rec.cancel_event.is_set()


def test_path_traversal_defense_on_report_files(client, tmp_path):
    """GET /api/runs/{run_id}/reports/{filename} must block directory traversal attempts."""
    run_dir = job_manager.reports_root / "run_sec_test"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "report.json").write_text('{"report_id": "test"}', encoding="utf-8")

    # Legitimate access
    resp_ok = client.get("/api/runs/run_sec_test/reports/report.json")
    assert resp_ok.status_code == 200

    # Path traversal attempts
    traversal_paths = [
        "../run_sec_test/report.json",
        "../../pyproject.toml",
        "..%2F..%2Fpyproject.toml",
        "/etc/passwd",
        "C:\\Windows\\win.ini",
    ]
    for path in traversal_paths:
        resp = client.get(f"/api/runs/run_sec_test/reports/{path}")
        assert resp.status_code in (400, 403, 404), f"Failed to block traversal: {path}"


def test_api_does_not_expose_secrets(client, monkeypatch):
    """Verify that no web endpoint reveals API keys or sensitive env vars."""
    monkeypatch.setenv("GEMINI_API_KEY", "SECRET_GEMINI_API_KEY_12345")
    monkeypatch.setenv("OPENAI_API_KEY", "SECRET_OPENAI_API_KEY_67890")
    monkeypatch.setattr(job_manager, "start_run_background", lambda r: None)

    resp = client.post("/api/runs", json={
        "url": "https://example.com",
        "context": "Testing that credentials are not leaked.",
        "personas": 2,
    })
    run_id = resp.json()["run_id"]

    # Check status endpoint
    status_text = client.get(f"/api/runs/{run_id}").text
    assert "SECRET_GEMINI" not in status_text
    assert "SECRET_OPENAI" not in status_text

    # Check list endpoint
    list_text = client.get("/api/runs").text
    assert "SECRET_GEMINI" not in list_text
    assert "SECRET_OPENAI" not in list_text


def test_get_completed_results(client, tmp_path):
    """GET /api/runs/{run_id}/results should return valid report.json content."""
    run_dir = job_manager.reports_root / "run_results_test"
    run_dir.mkdir(parents=True, exist_ok=True)
    report_data = {
        "report_id": "rep_12345",
        "target_url": "https://example.com",
        "findings": [],
        "task_metrics": {"total_tasks": 3, "passed_tasks": 3, "failed_tasks": 0},
    }
    (run_dir / "report.json").write_text(json.dumps(report_data), encoding="utf-8")

    resp = client.get("/api/runs/run_results_test/results")
    assert resp.status_code == 200
    data = resp.json()
    assert data["report_id"] == "rep_12345"
    assert data["target_url"] == "https://example.com"
