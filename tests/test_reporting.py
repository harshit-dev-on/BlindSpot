"""Tests for evidence aggregation, UX analysis, prioritization, and JSON/HTML reporting."""

import json
from pathlib import Path
from unittest.mock import MagicMock
import pytest

from blindspot.ai.base import BaseAIProvider
from blindspot.runtime import (
    BrowserInspectionResult,
    InspectionSummary,
    InteractiveElement,
    ViewportSize,
)
from blindspot.execution.models import (
    ActionExecutionRecord,
    ActionType,
    AgentAction,
    ExecutionRunResult,
    PersonaExecutionResult,
    TaskExecutionResult,
    TaskStatus,
)
from blindspot.personas.models import Persona, PersonaPlan, PersonaTask
from blindspot.reporting import (
    AIUXAnalyzer,
    BlindSpotReport,
    DeduplicatorAndPrioritizer,
    EvidenceAggregator,
    FindingCategory,
    SeverityLevel,
    TaskMetricSummary,
    UXFinding,
    generate_ux_report,
    render_html_report,
)
from blindspot.reporting.models import AIFindingsOutput, UXFindingDraft


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def sample_inspection() -> BrowserInspectionResult:
    """Sample inspection result with one labeled input and one unlabeled input."""
    return BrowserInspectionResult(
        timestamp="2026-10-16T12:00:00Z",
        requested_url="https://example.com",
        final_url="https://example.com/",
        context="An informational portal for software developers",
        title="Example Domain <script>alert('xss')</script>",
        viewport=ViewportSize(width=1280, height=800),
        interactive_elements=[
            InteractiveElement(
                element_type="button",
                tag="button",
                text="Search Catalog",
                aria_label="Search",
            ),
            InteractiveElement(
                element_type="input",
                tag="input",
                input_type="text",
                id="unlabeled_user_input",
                name="user_input",
                text="",
                aria_label="",
                placeholder="",
            ),
            InteractiveElement(
                element_type="button",
                tag="button",
                text="",
                aria_label="",
            ),
        ],
        summary=InspectionSummary(
            total_interactive_elements=3,
            links_count=0,
            buttons_count=2,
            form_fields_count=1,
            text_length=150,
        ),
        browser="chromium",
        screenshot_path="/tmp/mock_screenshot.png",
        result_json_path="/tmp/mock_inspection.json",
        page_text="Welcome to Example Domain. Find documentation and APIs.",
    )


@pytest.fixture
def sample_plan() -> PersonaPlan:
    """Sample persona plan with 2 personas and tasks."""
    return PersonaPlan(
        website_url="https://example.com",
        context="An informational portal for software developers",
        website_summary="Official developer documentation portal with API references.",
        personas=[
            Persona(
                id="persona_1",
                name="Taylor - Novice Developer",
                description="Looking for API documentation",
                experience_level="Novice",
                goals=["Read API docs"],
                likely_difficulties=["Finding search bar"],
                tasks=[
                    PersonaTask(
                        id="task_1",
                        objective="Locate API documentation",
                        starting_conditions="Starts on homepage",
                        success_criteria=["API docs link is clicked"],
                        evidence_to_collect=["Page title of documentation"],
                    ),
                    PersonaTask(
                        id="task_2",
                        objective="Submit feedback form",
                        starting_conditions="Starts on contact page",
                        success_criteria=["Confirmation alert visible"],
                        evidence_to_collect=["Success message"],
                    ),
                ],
            )
        ],
    )


@pytest.fixture
def sample_execution() -> ExecutionRunResult:
    """Sample execution result with 1 passing task and 1 failing task."""
    return ExecutionRunResult(
        target_url="https://example.com/",
        browser="chromium",
        headless=True,
        personas=[
            PersonaExecutionResult(
                persona_id="persona_1",
                persona_name="Taylor - Novice Developer",
                task_results=[
                    TaskExecutionResult(
                        task_id="task_1",
                        persona_id="persona_1",
                        task_objective="Locate API documentation",
                        status=TaskStatus.SUCCESS,
                        start_time="2026-10-16T12:01:00Z",
                        end_time="2026-10-16T12:01:05Z",
                        initial_url="https://example.com/",
                        final_url="https://example.com/docs",
                        actions_taken=[
                            ActionExecutionRecord(
                                step=1,
                                action=AgentAction(
                                    action=ActionType.CLICK,
                                    target="API Docs",
                                    reasoning="Click documentation navigation link",
                                ),
                                success=True,
                                page_url="https://example.com/",
                                page_title="Example Domain",
                            )
                        ],
                        evidence=["Observed exact text 'Documentation' on page"],
                    ),
                    TaskExecutionResult(
                        task_id="task_2",
                        persona_id="persona_1",
                        task_objective="Submit feedback form",
                        status=TaskStatus.FAILURE,
                        start_time="2026-10-16T12:01:06Z",
                        end_time="2026-10-16T12:01:15Z",
                        initial_url="https://example.com/contact",
                        final_url="https://example.com/contact",
                        actions_taken=[
                            ActionExecutionRecord(
                                step=1,
                                action=AgentAction(
                                    action=ActionType.CLICK,
                                    target="#submit-btn",
                                    reasoning="Attempt to click submit",
                                ),
                                success=False,
                                error="Element '#submit-btn' is covered by modal overlay",
                                page_url="https://example.com/contact",
                                page_title="Contact",
                            )
                        ],
                        error_message="Action execution failed: Element '#submit-btn' is covered by modal overlay",
                    ),
                ],
            )
        ],
    )


# ─────────────────────────────────────────────────────────────────────────────
# 1. Evidence Aggregation & Objective Findings Tests
# ─────────────────────────────────────────────────────────────────────────────


def test_evidence_aggregator_extracts_verified_issues(
    sample_inspection: BrowserInspectionResult,
    sample_plan: PersonaPlan,
    sample_execution: ExecutionRunResult,
):
    """Verify objective execution failures and accessibility flaws are categorized as VERIFIED_ISSUE."""
    aggregator = EvidenceAggregator(
        inspection_result=sample_inspection,
        plan=sample_plan,
        execution_result=sample_execution,
    )
    findings = aggregator.extract_objective_findings()

    assert len(findings) >= 2
    # Verify all extracted are VERIFIED_ISSUE
    for f in findings:
        assert f.category == FindingCategory.VERIFIED_ISSUE
        assert f.confidence == 1.0

    # Ensure task_2 failure was captured
    task_failure = next((f for f in findings if "task_2" in f.task_ids), None)
    assert task_failure is not None
    assert "modal overlay" in "".join(task_failure.supporting_evidence)
    assert task_failure.severity in (SeverityLevel.HIGH, SeverityLevel.CRITICAL)

    # Ensure accessibility missing label was captured
    label_issue = next((f for f in findings if "missing accessible labels" in f.title.lower()), None)
    assert label_issue is not None
    assert label_issue.category == FindingCategory.VERIFIED_ISSUE


def test_evidence_aggregator_handles_sparse_or_none_evidence():
    """Verify aggregator does not crash when execution_result or inspection is None."""
    aggregator = EvidenceAggregator(inspection_result=None, plan=None, execution_result=None)
    findings = aggregator.extract_objective_findings()
    assert findings == []

    insp, personas, outcomes, failures = aggregator.prepare_evidence_summary()
    assert insp["total_elements"] == 0
    assert personas == []
    assert outcomes == []
    assert failures == []


# ─────────────────────────────────────────────────────────────────────────────
# 2. Finding Categorization & Verification Integrity Tests
# ─────────────────────────────────────────────────────────────────────────────


def test_ai_analyzer_reclassifies_unverified_subjective_issues(
    sample_inspection: BrowserInspectionResult,
    sample_plan: PersonaPlan,
    sample_execution: ExecutionRunResult,
):
    """Ensure subjective recommendations cannot be falsely labeled as verified issues."""
    mock_provider = MagicMock(spec=BaseAIProvider)
    mock_provider.name = "mock-provider"
    mock_provider.model = "mock-model"

    # AI incorrectly claims a subjective observation is a verified issue for a passing task
    mock_provider.generate_structured.return_value = AIFindingsOutput(
        findings=[
            UXFindingDraft(
                title="Search bar should be in the header",
                category=FindingCategory.VERIFIED_ISSUE,  # Subjective opinion!
                description="The search bar is located in the sidebar instead of the top header.",
                severity=SeverityLevel.LOW,
                confidence=0.7,
                task_ids=["task_1"],  # task_1 passed!
                suggested_improvement="Move search input to header",
                expected_benefit="Better discoverability",
            )
        ]
    )

    aggregator = EvidenceAggregator(sample_inspection, sample_plan, sample_execution)
    analyzer = AIUXAnalyzer(provider=mock_provider)
    findings = analyzer.analyze("https://example.com", "Dev Portal", aggregator)

    assert len(findings) == 1
    # Must be reclassified to USABILITY_OBSERVATION because task_1 was not a failure
    assert findings[0].category == FindingCategory.USABILITY_OBSERVATION


def test_ai_analyzer_graceful_fallback_on_model_failure(
    sample_inspection: BrowserInspectionResult,
    sample_plan: PersonaPlan,
    sample_execution: ExecutionRunResult,
):
    """Verify that if the AI provider throws an error, analyzer returns empty list without crashing."""
    mock_provider = MagicMock(spec=BaseAIProvider)
    mock_provider.generate_structured.side_effect = RuntimeError("Service Unavailable (503)")

    aggregator = EvidenceAggregator(sample_inspection, sample_plan, sample_execution)
    analyzer = AIUXAnalyzer(provider=mock_provider)
    findings = analyzer.analyze("https://example.com", "Dev Portal", aggregator)

    assert findings == []


# ─────────────────────────────────────────────────────────────────────────────
# 3. Deduplication and Prioritization Tests
# ─────────────────────────────────────────────────────────────────────────────


def test_deduplicator_merges_duplicate_findings():
    """Verify duplicate findings targeting the same defect are merged."""
    dedup = DeduplicatorAndPrioritizer()
    f1 = UXFinding(
        id="f1",
        title="Submit Button Covered by Modal",
        category=FindingCategory.VERIFIED_ISSUE,
        description="Submit button cannot be clicked due to modal.",
        severity=SeverityLevel.HIGH,
        confidence=0.9,
        persona_ids=["persona_1"],
        task_ids=["task_1"],
        supporting_evidence=["Error: overlay cover"],
        suggested_improvement="Close modal on submit",
        expected_benefit="Allows submit",
    )
    f2 = UXFinding(
        id="f2",
        title="Submit button covered by modal!",
        category=FindingCategory.VERIFIED_ISSUE,
        description="Modal overlay blocks submit.",
        severity=SeverityLevel.CRITICAL,
        confidence=1.0,
        persona_ids=["persona_2"],
        task_ids=["task_2"],
        supporting_evidence=["Error: element intercept"],
        suggested_improvement="Dismiss modal",
        expected_benefit="Allows submit",
    )

    merged = dedup.deduplicate([f1, f2])
    assert len(merged) == 1
    result = merged[0]
    assert "persona_1" in result.persona_ids and "persona_2" in result.persona_ids
    assert "task_1" in result.task_ids and "task_2" in result.task_ids
    assert len(result.supporting_evidence) == 2
    # Severity upgraded to CRITICAL
    assert result.severity == SeverityLevel.CRITICAL
    assert result.confidence == 1.0


def test_prioritizer_assigns_correct_ranks_and_reasoning(sample_execution: ExecutionRunResult):
    """Verify critical task-blocking issues outrank low cosmetic improvements."""
    prioritizer = DeduplicatorAndPrioritizer()

    f_low = UXFinding(
        id="f_low",
        title="Increase contrast on footer links",
        category=FindingCategory.POTENTIAL_IMPROVEMENT,
        description="Footer link contrast could be slightly higher.",
        severity=SeverityLevel.LOW,
        confidence=0.7,
        suggested_improvement="Update color hex",
        expected_benefit="Slight contrast boost",
    )
    f_crit = UXFinding(
        id="f_crit",
        title="Submit button covered by modal",
        category=FindingCategory.VERIFIED_ISSUE,
        description="Prevents task completion.",
        severity=SeverityLevel.CRITICAL,
        confidence=1.0,
        task_ids=["task_2"],  # Failed in sample_execution
        supporting_evidence=["Action failed: overlay"],
        suggested_improvement="Remove overlay",
        expected_benefit="Unblocks submission",
    )

    ranked = prioritizer.prioritize([f_low, f_crit], execution_result=sample_execution)
    assert len(ranked) == 2
    assert ranked[0].id == "finding_1"
    assert ranked[0].title == "Submit button covered by modal"
    assert ranked[0].priority_rank == 1
    assert ranked[0].priority_score > ranked[1].priority_score
    assert "Directly blocked task completion" in ranked[0].priority_reasoning


# ─────────────────────────────────────────────────────────────────────────────
# 4. HTML Rendering and XSS Escaping Tests
# ─────────────────────────────────────────────────────────────────────────────


def test_html_report_escaping_and_safety():
    """Verify website title, evidence, and descriptions containing XSS vectors are strictly escaped."""
    report = BlindSpotReport(
        report_id="rep_test_xss",
        target_url="https://example.com/<script>alert('url_xss')</script>",
        context="Testing XSS <img src=x onerror=alert('ctx')>",
        findings=[
            UXFinding(
                id="finding_1",
                title="Malicious Title <script>alert('title')</script>",
                category=FindingCategory.VERIFIED_ISSUE,
                description="Dangerous description <script>evil()</script>",
                severity=SeverityLevel.HIGH,
                suggested_improvement="Fix code <iframe src=evil.com>",
                expected_benefit="Safe benefit <svg onload=alert(1)>",
                supporting_evidence=["Evidence: <script>bad()</script>"],
                reproduction_steps=["Step 1: click <button onclick='evil()'>"],
            )
        ],
    )

    html_out = render_html_report(report)

    # Ensure dangerous tags are NOT present in unescaped form
    assert "<script>alert('url_xss')</script>" not in html_out
    assert "<script>alert('title')</script>" not in html_out
    assert "<script>evil()</script>" not in html_out
    assert "<iframe src=evil.com>" not in html_out
    assert "<svg onload=alert(1)>" not in html_out
    assert "<script>bad()</script>" not in html_out

    # Ensure escaped entities exist
    assert "&lt;script&gt;alert(&#x27;url_xss&#x27;)&lt;/script&gt;" in html_out
    assert "&lt;script&gt;alert(&#x27;title&#x27;)&lt;/script&gt;" in html_out


def test_html_report_handles_missing_screenshots(tmp_path: Path):
    """Verify HTML report handles nonexistent screenshot paths cleanly without breaking."""
    report = BlindSpotReport(
        report_id="rep_missing_img",
        target_url="https://example.com",
        context="Sample",
        findings=[
            UXFinding(
                id="finding_1",
                title="Issue with missing screenshot file",
                category=FindingCategory.VERIFIED_ISSUE,
                description="Screenshot file was deleted or never saved.",
                severity=SeverityLevel.MEDIUM,
                suggested_improvement="Fix bug",
                expected_benefit="Benefit",
                screenshot_paths=["/nonexistent/path/checkpoint.png"],
            )
        ],
    )

    html_out = render_html_report(report, output_dir=tmp_path)
    assert "checkpoint.png (checkpoint logged)" in html_out
    assert "placeholder-icon" in html_out


# ─────────────────────────────────────────────────────────────────────────────
# 5. End-to-End Report Generation Tests
# ─────────────────────────────────────────────────────────────────────────────


def test_generate_ux_report_end_to_end(
    sample_inspection: BrowserInspectionResult,
    sample_plan: PersonaPlan,
    sample_execution: ExecutionRunResult,
    tmp_path: Path,
):
    """Verify complete generation of report.json and report.html with mocked AI."""
    mock_provider = MagicMock(spec=BaseAIProvider)
    mock_provider.name = "mock-ai"
    mock_provider.model = "mock-model"

    mock_provider.generate_structured.return_value = AIFindingsOutput(
        findings=[
            UXFindingDraft(
                title="Feedback form lacked submit progress indication",
                category=FindingCategory.USABILITY_OBSERVATION,
                description="No visual loader appears after clicking submit.",
                severity=SeverityLevel.MEDIUM,
                confidence=0.85,
                task_ids=["task_2"],
                suggested_improvement="Add a spinner to the submit button while sending request.",
                expected_benefit="Prevents accidental double-clicks and reassures users.",
            )
        ]
    )

    report, json_path, html_path = generate_ux_report(
        inspection_result=sample_inspection,
        plan=sample_plan,
        execution_result=sample_execution,
        provider=mock_provider,
        output_dir=tmp_path,
        context=sample_inspection.context,
    )

    # 1. Check returned model
    assert isinstance(report, BlindSpotReport)
    assert report.task_metrics.total_tasks == 2
    assert report.task_metrics.passed_tasks == 1
    assert report.task_metrics.failed_tasks == 1
    assert len(report.findings) >= 2  # Objective findings + AI finding

    # 2. Check JSON file on disk and schema round-trip
    assert json_path.exists()
    raw_json = json.loads(json_path.read_text(encoding="utf-8"))
    reloaded_report = BlindSpotReport.model_validate(raw_json)
    assert reloaded_report.report_id == report.report_id
    assert len(reloaded_report.findings) == len(report.findings)

    # 3. Check HTML file on disk
    assert html_path.exists()
    html_content = html_path.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in html_content
    assert "BlindSpot Automated UX Testing Report" in html_content
    assert "Objectively Verified Defects" in html_content
    assert "Simulated Persona Profiles" in html_content

    # 4. Check Markdown file on disk
    md_path = tmp_path / "report.md"
    assert md_path.exists()
    md_content = md_path.read_text(encoding="utf-8")
    assert "# 🔍 BlindSpot UX & Accessibility Audit Report" in md_content
    assert "Executive Summary" in md_content
    assert "Prioritized UX & Accessibility Findings" in md_content

