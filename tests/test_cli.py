from pathlib import Path
import pytest
from typer.testing import CliRunner
from blindspot.ai.exceptions import AIAuthenticationError
from blindspot.cli import app
from blindspot.personas.models import Persona, PersonaPlan, PersonaTask

runner = CliRunner()


@pytest.fixture(autouse=True)
def mock_inspect_ai(monkeypatch):
    """Ensure inspect CLI tests mock AI persona generation without live network requests."""
    sample_plan = PersonaPlan(
        website_url="https://example.com",
        context="A technical documentation portal",
        website_summary="Technical docs with navigation links and code examples.",
        personas=[
            Persona(
                id="persona_1",
                name="Taylor - Web Developer",
                description="Testing technical documentation site.",
                experience_level="Intermediate",
                goals=["Find quickstart"],
                likely_difficulties=["Hidden search bar"],
                accessibility_needs="Standard",
                tasks=[
                    PersonaTask(
                        id="task_p1_1",
                        objective="Locate quickstart guide",
                        starting_conditions="Starts on homepage",
                        success_criteria=["Quickstart guide opens"],
                        evidence_to_collect=["Screenshot of quickstart page"],
                        is_verified=True,
                    ),
                    PersonaTask(
                        id="task_p1_2",
                        objective="Search for API reference",
                        starting_conditions="Starts on homepage",
                        success_criteria=["API reference table located"],
                        evidence_to_collect=["Text of API table"],
                        is_verified=False,
                        uncertainty_notes="Assumes site has API search bar",
                    ),
                ],
            )
        ],
        model_used="mock-model",
        provider_used="mock-provider",
    )

    def _mock_gen(inspection_result, provider, num_personas=3, output_dir=None):
        target_dir = output_dir or (Path(inspection_result.result_json_path).parent if inspection_result.result_json_path else None)
        if target_dir:
            p_file = Path(target_dir) / "personas.json"
            p_file.parent.mkdir(parents=True, exist_ok=True)
            p_file.write_text(sample_plan.model_dump_json(indent=2), encoding="utf-8")
            sample_plan.plan_file_path = str(p_file)
        return sample_plan

    monkeypatch.setattr("blindspot.cli.generate_personas_and_tasks", _mock_gen)

    from blindspot.execution.models import (
        ExecutionRunResult,
        PersonaExecutionResult,
        TaskExecutionResult,
        TaskStatus,
    )

    sample_run = ExecutionRunResult(
        target_url="https://example.com",
        browser="chromium",
        headless=True,
        personas=[
            PersonaExecutionResult(
                persona_id="persona_1",
                persona_name="Taylor - Web Developer",
                task_results=[
                    TaskExecutionResult(
                        task_id="task_p1_1",
                        persona_id="persona_1",
                        task_objective="Locate quickstart guide",
                        status=TaskStatus.SUCCESS,
                        start_time="2026-10-16T12:00:00Z",
                        end_time="2026-10-16T12:00:05Z",
                        initial_url="https://example.com",
                        final_url="https://example.com/quickstart",
                        evidence=["Quickstart guide observed"],
                    )
                ],
            )
        ],
    )

    def _mock_exec(plan, provider, output_dir, browser_type="chromium", headless=True, max_actions_per_task=8, **kwargs):
        res_file = Path(output_dir) / "execution_results.json"
        res_file.parent.mkdir(parents=True, exist_ok=True)
        res_file.write_text(sample_run.model_dump_json(indent=2), encoding="utf-8")
        sample_run.results_file_path = str(res_file)
        return sample_run

    monkeypatch.setattr("blindspot.cli.execute_persona_tasks", _mock_exec)

    from blindspot.reporting.models import FindingCategory, SeverityLevel, UXFinding

    def _mock_analyze(*args, **kwargs):
        return [
            UXFinding(
                id="finding_mock_1",
                title="Improve search field contrast",
                category=FindingCategory.USABILITY_OBSERVATION,
                description="Mock finding for CLI tests.",
                severity=SeverityLevel.MEDIUM,
                confidence=0.8,
                suggested_improvement="Increase input contrast",
                expected_benefit="Better discoverability",
            )
        ]

    monkeypatch.setattr("blindspot.reporting.analysis.AIUXAnalyzer.analyze", _mock_analyze)


def test_cli_help():
    """Verify that root `blindspot --help` runs successfully and displays commands."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "BlindSpot" in result.stdout
    assert "inspect" in result.stdout


def test_cli_version():
    """Verify that `blindspot --version` outputs version number."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.stdout


def test_inspect_help():
    """Verify that `blindspot inspect --help` displays expected options."""
    result = runner.invoke(app, ["inspect", "--help"])
    assert result.exit_code == 0
    assert "--url" in result.stdout
    assert "--context" in result.stdout
    assert "--output-dir" in result.stdout
    assert "--browser" in result.stdout
    assert "--headless" in result.stdout


def test_inspect_missing_all_arguments():
    """Verify that invoking inspect without args displays help or an error code."""
    result = runner.invoke(app, ["inspect"])
    # Typer with no_args_is_help=True exits with 0 or 2 depending on typer version
    assert result.exit_code in (0, 2)
    assert "--url" in result.stdout or "Missing option" in result.output


def test_inspect_valid_arguments():
    """Verify successful inspect command execution with valid URL and context."""
    result = runner.invoke(
        app,
        [
            "inspect",
            "--url",
            "https://example.com",
            "--context",
            "A technical documentation portal for open source developers.",
        ],
    )
    assert result.exit_code == 0
    assert "BlindSpot Browser Inspection Complete" in result.stdout
    assert "Inspection successful" in result.stdout
    assert "https://example.com" in result.stdout


def test_inspect_custom_output_dir(tmp_path: Path):
    """Verify inspect command respects custom --output-dir option."""
    out_dir = tmp_path / "custom_cli_out"
    result = runner.invoke(
        app,
        [
            "inspect",
            "--url",
            "https://example.com",
            "--context",
            "A technical documentation portal for open source developers.",
            "--output-dir",
            str(out_dir),
        ],
    )
    assert result.exit_code == 0
    assert (out_dir / "screenshot.png").exists()
    assert (out_dir / "inspection_result.json").exists()


def test_inspect_headed_flag(tmp_path: Path):
    """Verify inspect command accepts --headed flag without error."""
    out_dir = tmp_path / "headed_out"
    result = runner.invoke(
        app,
        [
            "inspect",
            "--url",
            "https://example.com",
            "--context",
            "A technical documentation portal for open source developers.",
            "--output-dir",
            str(out_dir),
            "--headed",
        ],
    )
    assert result.exit_code == 0
    assert (out_dir / "screenshot.png").exists()



def test_inspect_invalid_browser():
    """Verify inspect command rejects unsupported browser choice."""
    result = runner.invoke(
        app,
        [
            "inspect",
            "--url",
            "https://example.com",
            "--context",
            "A technical documentation portal for open source developers.",
            "--browser",
            "unsupported_engine",
        ],
    )
    assert result.exit_code == 1
    assert "Invalid Browser" in result.output or "not supported" in result.output


def test_inspect_invalid_url():
    """Verify that invalid URL triggers clear error message and exit code 1."""
    result = runner.invoke(
        app,
        [
            "inspect",
            "--url",
            "invalid-url-without-scheme",
            "--context",
            "A technical documentation portal for open source developers.",
        ],
    )
    assert result.exit_code == 1
    assert "Invalid URL" in result.output or "protocol scheme" in result.output


def test_inspect_invalid_context():
    """Verify that invalid context triggers clear error message and exit code 1."""
    result = runner.invoke(
        app,
        [
            "inspect",
            "--url",
            "https://example.com",
            "--context",
            "too brief",
        ],
    )
    assert result.exit_code == 1
    assert "Invalid Context" in result.output or "too brief" in result.output


def test_inspect_with_skip_ai(tmp_path: Path):
    """Verify --skip-ai option skips persona generation."""
    out_dir = tmp_path / "skip_ai_out"
    result = runner.invoke(
        app,
        [
            "inspect",
            "--url",
            "https://example.com",
            "--context",
            "A technical documentation portal for open source developers.",
            "--output-dir",
            str(out_dir),
            "--skip-ai",
        ],
    )
    assert result.exit_code == 0
    assert "AI persona synthesis skipped" in result.stdout
    assert (out_dir / "screenshot.png").exists()
    assert (out_dir / "inspection_result.json").exists()
    assert not (out_dir / "personas.json").exists()


def test_inspect_generates_personas_and_plan_file(tmp_path: Path):
    """Verify that default inspect command generates personas and personas.json."""
    out_dir = tmp_path / "plan_out"
    result = runner.invoke(
        app,
        [
            "inspect",
            "--url",
            "https://example.com",
            "--context",
            "A technical documentation portal for open source developers.",
            "--output-dir",
            str(out_dir),
        ],
    )
    assert result.exit_code == 0
    assert "AI Persona Synthesis & Task Planning Complete" in result.stdout
    assert (out_dir / "personas.json").exists()


def test_inspect_missing_ai_config_error(monkeypatch):
    """Verify helpful error message when AI provider fails authentication or setup."""
    def _mock_failing_provider(*args, **kwargs):
        raise AIAuthenticationError(
            "Missing Gemini API key.",
            provider="gemini",
            suggestion="Run 'blindspot setup' or set GEMINI_API_KEY.",
        )

    monkeypatch.setattr("blindspot.cli.create_provider", _mock_failing_provider)

    result = runner.invoke(
        app,
        [
            "inspect",
            "--url",
            "https://example.com",
            "--context",
            "A technical documentation portal for open source developers.",
        ],
    )
    assert result.exit_code == 1
    assert "AI Configuration Error" in result.output or "Missing Gemini API key" in result.output
    assert "blindspot setup" in result.output


def test_inspect_with_skip_execution(tmp_path: Path):
    """Verify --skip-execution generates personas without running browser execution."""
    out_dir = tmp_path / "skip_exec_out"
    result = runner.invoke(
        app,
        [
            "inspect",
            "--url",
            "https://example.com",
            "--context",
            "A technical documentation portal for open source developers.",
            "--output-dir",
            str(out_dir),
            "--skip-execution",
        ],
    )
    assert result.exit_code == 0
    assert "Persona task execution skipped" in result.stdout
    assert (out_dir / "personas.json").exists()
    assert not (out_dir / "execution_results.json").exists()


def test_inspect_executes_and_saves_execution_results(tmp_path: Path):
    """Verify default inspect command generates personas, runs browser tasks, and outputs reports."""
    out_dir = tmp_path / "full_run_out"
    result = runner.invoke(
        app,
        [
            "inspect",
            "--url",
            "https://example.com",
            "--context",
            "A technical documentation portal for open source developers.",
            "--output-dir",
            str(out_dir),
        ],
    )
    assert result.exit_code == 0
    assert "Persona-Based Browser Testing Complete" in result.stdout
    assert (out_dir / "execution_results.json").exists()
    assert (out_dir / "report.json").exists()
    assert (out_dir / "report.html").exists()
    assert ("UX & accessibility audit completed" in result.stdout or "BlindSpot UX Testing & Analysis Complete" in result.stdout)


def test_inspect_with_skip_report(tmp_path: Path):
    """Verify --skip-report flag suppresses report generation."""
    out_dir = tmp_path / "skip_report_out"
    result = runner.invoke(
        app,
        [
            "inspect",
            "--url",
            "https://example.com",
            "--context",
            "A technical documentation portal for open source developers.",
            "--output-dir",
            str(out_dir),
            "--skip-report",
        ],
    )
    assert result.exit_code == 0
    assert "UX report generation skipped" in result.stdout
    assert not (out_dir / "report.json").exists()
    assert not (out_dir / "report.html").exists()


