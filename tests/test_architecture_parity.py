"""Tests verifying architectural alignment for BlindSpot modules.

Ensures interface, runtime, agents, and report packages export expected symbols
and integrate seamlessly with backward-compatible legacy paths.
"""

import pytest
from typer.testing import CliRunner

from blindspot import __version__
from blindspot.agents import (
    PersonaTaskAgent,
    PersonaTestRunner,
    build_agent_step_prompt,
    build_agent_system_prompt,
    create_persona_agent,
    create_test_runner,
    execute_persona_tasks,
)
from blindspot.interface import (
    SUPPORTED_BROWSERS,
    app,
    main,
    preflight_model_connection,
    run_setup_wizard,
    show_interactive_start_screen,
    version_callback,
)
from blindspot.report import (
    AIUXAnalyzer,
    BlindSpotReport,
    DeduplicatorAndPrioritizer,
    EvidenceAggregator,
    FindingCategory,
    FindingItem,
    SeverityLevel,
    TaskMetricSummary,
    UXFinding,
    generate_sarif_log,
    generate_ux_report,
    render_html_report,
    write_sarif_file,
)
from blindspot.runtime import (
    BoundingBox,
    BrowserInspectionResult,
    BrowserInspector,
    InspectionSummary,
    InteractiveElement,
    ViewportSize,
    ensure_browser_engine,
    inspect_website,
)

runner = CliRunner()


def test_interface_exports_and_cli():
    """Verify interface module exports and CLI invocation."""
    assert callable(main)
    assert app is not None
    assert "chromium" in SUPPORTED_BROWSERS
    assert callable(run_setup_wizard)
    assert callable(preflight_model_connection)
    assert callable(show_interactive_start_screen)

    # Test version callback
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert f"BlindSpot version {__version__}" in result.stdout


def test_start_screen_result_unpacking_and_attrs():
    """Verify StartScreenResult supports 2-tuple unpacking while exposing headed, personas, concurrency."""
    from blindspot.interface.interactive import StartScreenResult
    res = StartScreenResult("https://example.com", "Focus on login", headed=True, personas=1, concurrency=1)
    target, instruction = res
    assert target == "https://example.com"
    assert instruction == "Focus on login"
    assert res.headed is True
    assert res.personas == 1
    assert res.concurrency == 1


def test_runtime_exports_and_models():
    """Verify runtime module exports and model instantiation."""
    vp = ViewportSize(width=1280, height=800)
    assert vp.width == 1280
    assert vp.height == 800

    bbox = BoundingBox(x=10, y=20, width=100, height=50)
    elem = InteractiveElement(
        element_type="button",
        tag="button",
        text="Submit",
        bounding_box=bbox,
    )
    assert elem.text == "Submit"
    assert elem.bounding_box.width == 100

    summary = InspectionSummary(
        total_interactive_elements=1,
        links_count=0,
        buttons_count=1,
        form_fields_count=0,
        text_length=50,
    )
    assert summary.total_interactive_elements == 1

    inspector = BrowserInspector(browser_type="chromium")
    assert inspector.browser_type == "chromium"


def test_agents_exports_and_factory():
    """Verify agents module exports, prompt builders, and factory functions."""
    sys_prompt = build_agent_system_prompt()
    assert "Autonomous Browser Agent" in sys_prompt
    assert "CRITICAL SAFETY" in sys_prompt

    from blindspot.ai.base import BaseAIProvider
    from blindspot.ai.models import AIResponse

    class DummyProvider(BaseAIProvider):
        @property
        def name(self) -> str:
            return "dummy"

        def generate(self, prompt, system_prompt=None, temperature=0.2, max_tokens=1024):
            return AIResponse(
                content='{"thought": "test", "action": "finish", "target": "", "value": ""}',
                model="test-model",
                provider="dummy",
            )

        def check_health(self):
            from blindspot.ai.models import ProviderStatus
            return ProviderStatus(provider="dummy", model="test", is_reachable=True, model_available=True)

    dummy = DummyProvider(model="test-model")
    agent = create_persona_agent(provider=dummy, max_actions=5)
    assert isinstance(agent, PersonaTaskAgent)
    assert agent.max_actions == 5

    test_runner = create_test_runner(provider=dummy, max_actions_per_task=3)
    assert isinstance(test_runner, PersonaTestRunner)
    assert test_runner.max_actions_per_task == 3


def test_report_exports_and_models():
    """Verify report module exports and models."""
    assert callable(generate_ux_report)
    assert callable(render_html_report)
    assert callable(write_sarif_file)
    assert callable(generate_sarif_log)

    finding = UXFinding(
        id="finding_1",
        title="Missing form label",
        category=FindingCategory.VERIFIED_ISSUE,
        description="Search input lacks aria-label",
        severity=SeverityLevel.HIGH,
        supporting_evidence=["<input id='q'>"],
        suggested_improvement="Add aria-label='Search'",
        expected_benefit="Screen reader users can locate search",
    )
    assert finding.severity == SeverityLevel.HIGH
    assert finding.category == FindingCategory.VERIFIED_ISSUE
