"""Central orchestration pipeline for BlindSpot inspection, persona testing, and reporting."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
import secrets
from typing import Any, Callable, Dict, Optional

from blindspot.ai import create_provider
from blindspot.ai.base import BaseAIProvider
from blindspot.browser import BrowserInspectionResult, inspect_website
from blindspot.config.loader import load_config
from blindspot.core.validation import validate_context, validate_url
from blindspot.execution.models import ExecutionRunResult
from blindspot.execution.runner import execute_persona_tasks
from blindspot.execution.safety import validate_navigation_url
from blindspot.personas.generator import generate_personas_and_tasks
from blindspot.personas.models import PersonaPlan
from blindspot.reporting.generator import generate_ux_report
from blindspot.reporting.models import BlindSpotReport


@dataclass
class PipelineConfig:
    """Configuration options for a complete BlindSpot testing run."""

    url: str
    context: str
    output_dir: Optional[Path] = None
    personas: int = 3
    browser: str = "chromium"
    headless: bool = True
    max_actions: int = 8
    skip_ai: bool = False
    skip_execution: bool = False
    skip_report: bool = False
    ai_provider: Optional[str] = None
    ai_model: Optional[str] = None
    allow_local: bool = False


@dataclass
class PipelineResult:
    """Result of an end-to-end BlindSpot testing run."""

    run_id: str
    target_url: str
    output_dir: Path
    status: str  # "completed", "cancelled", "failed"
    inspection_result: Optional[BrowserInspectionResult] = None
    plan: Optional[PersonaPlan] = None
    execution_result: Optional[ExecutionRunResult] = None
    report: Optional[BlindSpotReport] = None
    json_path: Optional[str] = None
    html_path: Optional[str] = None
    error_message: Optional[str] = None


def generate_run_id() -> str:
    """Generate a readable, timestamped, unique test run ID."""
    now_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    rand_suffix = secrets.token_hex(3)
    return f"run_{now_str}_{rand_suffix}"


def run_pipeline(
    config: PipelineConfig,
    on_event: Optional[Callable[[Dict[str, Any]], None]] = None,
    cancel_check: Optional[Callable[[], bool]] = None,
) -> PipelineResult:
    """Execute the full BlindSpot testing pipeline with real-time event reporting.

    Stages:
    1. Input Validation & SSRF Safety
    2. Browser Inspection & DOM Extraction
    3. AI Persona & Task Synthesis
    4. Autonomous Persona Browser Task Execution
    5. Evidence Aggregation & UX Report Generation
    """

    def emit(event_type: str, data: Optional[Dict[str, Any]] = None) -> None:
        if on_event:
            payload = {
                "type": event_type,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            if data:
                payload.update(data)
            try:
                on_event(payload)
            except Exception:
                pass

    # 1. Input Validation
    url_res = validate_url(config.url)
    if not url_res.is_valid:
        raise ValueError(f"Invalid URL: {url_res.error_message}")

    # SSRF & Private Network Defense
    is_safe_url, ssrf_reason = validate_navigation_url(config.url, allow_local=config.allow_local)
    if not is_safe_url:
        raise ValueError(f"Security Policy Blocked: {ssrf_reason}")

    context_res, resolved_context = validate_context(config.context)
    if not context_res.is_valid:
        raise ValueError(f"Invalid Context: {context_res.error_message}")

    run_id = generate_run_id()
    if config.output_dir:
        run_output_dir = Path(config.output_dir)
    else:
        run_output_dir = Path("reports") / run_id

    run_output_dir.mkdir(parents=True, exist_ok=True)

    result = PipelineResult(
        run_id=run_id,
        target_url=config.url.strip(),
        output_dir=run_output_dir,
        status="running",
    )

    emit("pipeline_start", {
        "run_id": run_id,
        "target_url": config.url.strip(),
        "output_dir": str(run_output_dir),
        "personas_count": config.personas,
        "headless": config.headless,
    })

    try:
        # Check cancellation
        if cancel_check and cancel_check():
            result.status = "cancelled"
            emit("pipeline_cancelled", {"run_id": run_id})
            return result

        # 2. Browser Inspection
        emit("stage_start", {"stage": "inspection", "message": "Launching browser inspection..."})
        inspection = inspect_website(
            url=config.url.strip(),
            context=resolved_context,
            output_dir=run_output_dir,
            browser_type=config.browser,
            headless=config.headless,
            allow_local=config.allow_local,
        )
        result.inspection_result = inspection
        emit("stage_finish", {
            "stage": "inspection",
            "title": inspection.title,
            "final_url": inspection.final_url,
            "total_elements": inspection.summary.total_interactive_elements,
            "links_count": inspection.summary.links_count,
            "buttons_count": inspection.summary.buttons_count,
            "screenshot_path": inspection.screenshot_path,
        })

        if cancel_check and cancel_check():
            result.status = "cancelled"
            emit("pipeline_cancelled", {"run_id": run_id})
            return result

        # 3. AI Persona Generation
        provider_instance: Optional[BaseAIProvider] = None
        plan: Optional[PersonaPlan] = None
        if not config.skip_ai:
            emit("stage_start", {"stage": "personas", "message": "Synthesizing AI user personas & test tasks..."})
            loaded_cfg = load_config(provider=config.ai_provider, model=config.ai_model)
            ai_cfg = loaded_cfg.ai
            effective_model = (
                config.ai_model
                or (ai_cfg.tasks.persona_generation if ai_cfg.tasks else None)
                or ai_cfg.model
            )
            effective_cfg = ai_cfg.model_copy(update={"model": effective_model})
            provider_instance = create_provider(effective_cfg)

            plan = generate_personas_and_tasks(
                inspection_result=inspection,
                provider=provider_instance,
                num_personas=config.personas,
                output_dir=run_output_dir,
            )
            result.plan = plan
            emit("stage_finish", {
                "stage": "personas",
                "personas_count": len(plan.personas),
                "total_tasks": sum(len(p.tasks) for p in plan.personas),
                "personas": [
                    {
                        "id": p.id,
                        "name": p.name,
                        "experience": getattr(p, "experience_level", "Standard"),
                        "goals": getattr(p, "goals", []),
                        "tasks_count": len(p.tasks),
                    }
                    for p in plan.personas
                ],
            })

        if cancel_check and cancel_check():
            result.status = "cancelled"
            emit("pipeline_cancelled", {"run_id": run_id})
            return result

        # 4. Browser Task Execution
        execution_res: Optional[ExecutionRunResult] = None
        if not config.skip_execution and plan and provider_instance:
            emit("stage_start", {"stage": "execution", "message": "Running automated persona browser tasks..."})
            execution_res = execute_persona_tasks(
                plan=plan,
                provider=provider_instance,
                output_dir=run_output_dir,
                browser_type=config.browser,
                headless=config.headless,
                max_actions_per_task=config.max_actions,
                allow_local=config.allow_local,
                on_event=on_event,
                cancel_check=cancel_check,
            )
            result.execution_result = execution_res
            emit("stage_finish", {
                "stage": "execution",
                "total_tasks": execution_res.total_tasks,
                "passed_tasks": execution_res.passed_tasks,
                "failed_tasks": execution_res.failed_tasks,
                "inconclusive_tasks": execution_res.inconclusive_tasks,
            })

        if cancel_check and cancel_check():
            result.status = "cancelled"
            emit("pipeline_cancelled", {"run_id": run_id})
            return result

        # 5. UX Report Generation
        if not config.skip_report:
            emit("stage_start", {"stage": "reporting", "message": "Aggregating evidence & generating UX reports..."})
            report, json_path, html_path = generate_ux_report(
                inspection_result=inspection,
                plan=plan,
                execution_result=execution_res,
                provider=provider_instance,
                output_dir=run_output_dir,
                context=resolved_context,
            )
            result.report = report
            result.json_path = json_path
            result.html_path = html_path
            emit("stage_finish", {
                "stage": "reporting",
                "report_id": report.report_id,
                "verified_issues": report.verified_issues_count,
                "usability_observations": report.usability_observations_count,
                "potential_improvements": report.potential_improvements_count,
                "json_path": json_path,
                "html_path": html_path,
            })

        result.status = "completed"
        emit("pipeline_finish", {
            "run_id": run_id,
            "status": "completed",
            "report_id": result.report.report_id if result.report else None,
            "json_path": result.json_path,
            "html_path": result.html_path,
        })
        return result

    except Exception as exc:
        result.status = "failed"
        result.error_message = str(exc)
        emit("pipeline_error", {
            "run_id": run_id,
            "error": str(exc),
        })
        raise
