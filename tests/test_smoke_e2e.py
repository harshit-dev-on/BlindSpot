"""End-to-end offline smoke test verifying the entire BlindSpot testing pipeline.

Validates the full chain from browser inspection to report generation:
1. Website inspection using Playwright on local HTTP server.
2. AI persona synthesis & task planning (deterministic mock).
3. Isolated browser context task execution (Playwright actions & checkpointing).
4. Evidence collection & screenshot recording.
5. JSON and responsive HTML report generation.

This test runs entirely offline on loopback with deterministic mock AI responses and
requires no external network access or real cloud API credentials.
"""

import functools
import http.server
from pathlib import Path
import threading
from unittest.mock import MagicMock
import pytest

from blindspot.ai.base import BaseAIProvider
from blindspot.core.runner import PipelineConfig, run_pipeline
from blindspot.execution.models import ActionType, AgentAction
from blindspot.personas.models import Persona, PersonaPlanPayload, PersonaTask
from blindspot.reporting.models import AIFindingsOutput, FindingCategory, SeverityLevel, UXFindingDraft


@pytest.fixture
def local_sample_site_url(tmp_path: Path):
    """Serve a local HTML page mimicking TaskFlow via local HTTP server on loopback."""
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>TaskFlow E2E Test App</title>
</head>
<body>
  <header>
    <h1>TaskFlow Agile Workspace</h1>
    <nav>
      <a href="#features" id="nav-features">Features</a>
      <a href="#demo" id="nav-demo">Demo Form</a>
    </nav>
  </header>

  <main>
    <section id="features">
      <h2>Team Features</h2>
      <p>Kanban boards and sprint tracking.</p>
    </section>

    <section id="demo">
      <h2>Request Early Beta</h2>
      <div id="confirmation-banner" style="display:none;">Success! Beta invite registered.</div>
      <form id="lead-form" onsubmit="event.preventDefault(); document.getElementById('confirmation-banner').style.display='block';">
        <label for="full-name">Full Name</label>
        <input type="text" id="full-name" name="fullName" placeholder="Your Name" />
        <button type="submit" id="submit-btn">Register</button>
      </form>
    </section>
  </main>
</body>
</html>"""
    html_file = tmp_path / "index.html"
    html_file.write_text(html_content, encoding="utf-8")

    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(tmp_path))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    port = server.server_address[1]

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    yield f"http://127.0.0.1:{port}/index.html"

    server.shutdown()
    server.server_close()


def test_end_to_end_pipeline_offline_smoke(local_sample_site_url: str, tmp_path: Path, monkeypatch):
    """Run full pipeline and verify inspection, personas, task execution, evidence, and reports."""
    # 1. Setup deterministic mock AI responses
    mock_provider = MagicMock(spec=BaseAIProvider)
    mock_provider.name = "mock-provider"
    mock_provider.model = "mock-model"

    # Synthetic persona plan payload
    persona_payload = PersonaPlanPayload(
        website_summary="TaskFlow is a team sprint and agile task tracking web app.",
        personas=[
            Persona(
                id="persona_smoke_1",
                name="Jordan - Lead Engineer",
                description="Evaluating TaskFlow sprint capabilities.",
                experience_level="Advanced",
                goals=["Explore sprint boards", "Submit early access request"],
                likely_difficulties=["Form validation friction"],
                accessibility_needs="Standard desktop viewport",
                tasks=[
                    PersonaTask(
                        id="task_smoke_1",
                        objective="Register for early access using the demo form",
                        starting_conditions="Starts on homepage",
                        success_criteria=["Beta invite registered"],
                        evidence_to_collect=["Confirmation banner text"],
                        is_verified=True,
                    )
                ],
            )
        ],
    )

    # Browser agent actions: 1. fill name, 2. click submit, 3. finish
    action_1 = AgentAction(
        action=ActionType.FILL,
        target="#full-name",
        value="Jordan Lee",
        reasoning="Fill name field in beta registration form.",
    )
    action_2 = AgentAction(
        action=ActionType.CLICK,
        target="#submit-btn",
        value="",
        reasoning="Click register button to submit application.",
    )
    action_3 = AgentAction(
        action=ActionType.FINISH,
        target="",
        value="",
        reasoning="Success message observed on page.",
    )

    # Report analysis payload
    report_payload = AIFindingsOutput(
        findings=[
            UXFindingDraft(
                title="Immediate Visual Confirmation Delivered",
                category=FindingCategory.POTENTIAL_IMPROVEMENT,
                severity=SeverityLevel.LOW,
                description="The registration confirmation appears instantly upon submit.",
                affected_page_url=local_sample_site_url,
                suggested_improvement="Send email receipt alongside visual confirmation banner.",
                expected_benefit="Enhances user trust during onboarding.",
                confidence=0.9,
            )
        ],
    )

    # Configure structured generation sequence
    mock_provider.generate_structured.side_effect = [
        persona_payload,  # 1. Persona synthesis
        action_1,         # 2. Agent step 1 (fill)
        action_2,         # 3. Agent step 2 (click)
        action_3,         # 4. Agent step 3 (finish)
        report_payload,   # 5. UX analysis & report generation
    ]

    # Monkeypatch create_provider to return our deterministic mock
    monkeypatch.setattr(
        "blindspot.core.runner.create_provider",
        lambda cfg: mock_provider,
    )

    # 2. Configure Pipeline
    run_output_dir = tmp_path / "smoke_run_output"
    config = PipelineConfig(
        url=local_sample_site_url,
        context="TaskFlow agile workspace for modern engineering teams.",
        output_dir=run_output_dir,
        personas=1,
        browser="chromium",
        headless=True,
        max_actions=5,
        allow_local=True,
    )

    # 3. Execute Complete Pipeline
    events_log = []
    result = run_pipeline(config=config, on_event=lambda evt: events_log.append(evt))

    # 4. Verify Inspection Results
    assert result.status == "completed"
    assert result.inspection_result is not None
    assert "TaskFlow E2E Test App" in result.inspection_result.title
    assert result.inspection_result.summary.total_interactive_elements > 0
    assert Path(result.inspection_result.screenshot_path).exists()

    # 5. Verify Persona Plan
    assert result.plan is not None
    assert len(result.plan.personas) == 1
    assert result.plan.personas[0].name == "Jordan - Lead Engineer"

    # 6. Verify Execution Results
    assert result.execution_result is not None
    assert result.execution_result.total_tasks == 1
    assert result.execution_result.passed_tasks == 1
    assert len(result.execution_result.personas) == 1

    # 7. Verify Reports on Disk
    assert result.json_path is not None
    assert Path(result.json_path).exists()
    assert result.html_path is not None
    assert Path(result.html_path).exists()

    # Verify report content
    html_text = Path(result.html_path).read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in html_text
    assert "TaskFlow E2E Test App" in html_text or "TaskFlow" in html_text
    assert "Jordan - Lead Engineer" in html_text
    assert "Visual Evidence" in html_text or "Simulated Persona Profiles" in html_text

    # Verify event stream tracking
    stage_events = [e["stage"] for e in events_log if e.get("type") == "stage_start"]
    assert "inspection" in stage_events
    assert "personas" in stage_events
    assert "execution" in stage_events
    assert "reporting" in stage_events
