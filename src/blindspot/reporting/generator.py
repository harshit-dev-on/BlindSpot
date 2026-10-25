"""Orchestrates UX evidence aggregation, analysis, prioritization, and report file generation."""

import json
from pathlib import Path
from typing import Optional, Tuple
from uuid import uuid4

from blindspot.ai.base import BaseAIProvider
from blindspot.runtime import BrowserInspectionResult
from blindspot.execution.models import ExecutionRunResult
from blindspot.personas.models import PersonaPlan
from blindspot.reporting.analysis import (
    AIUXAnalyzer,
    DeduplicatorAndPrioritizer,
    EvidenceAggregator,
)
from blindspot.reporting.html_renderer import render_html_report
from blindspot.reporting.models import BlindSpotReport, TaskMetricSummary
from blindspot.reporting.sarif import write_sarif_file


def generate_ux_report(
    inspection_result: Optional[BrowserInspectionResult] = None,
    plan: Optional[PersonaPlan] = None,
    execution_result: Optional[ExecutionRunResult] = None,
    provider: Optional[BaseAIProvider] = None,
    output_dir: Optional[Path] = None,
    context: Optional[str] = None,
) -> Tuple[BlindSpotReport, Path, Path]:
    """Aggregate all run artifacts, run UX analysis, prioritize findings, and generate report.json and report.html."""
    out_dir = output_dir or Path.cwd()
    out_dir.mkdir(parents=True, exist_ok=True)

    target_url = (
        (execution_result.target_url if execution_result else None)
        or (inspection_result.final_url if inspection_result else None)
        or (inspection_result.requested_url if inspection_result else None)
        or "https://unknown.target"
    )

    ctx_text = context or (inspection_result.context if inspection_result else "General Website")

    # 1. Aggregate evidence and extract objective findings
    aggregator = EvidenceAggregator(
        inspection_result=inspection_result,
        plan=plan,
        execution_result=execution_result,
    )
    objective_findings = aggregator.extract_objective_findings()

    # 2. Run AI qualitative UX analysis (with fallback if model unavailable or fails)
    ai_findings = []
    if provider:
        analyzer = AIUXAnalyzer(provider)
        ai_findings = analyzer.analyze(
            target_url=target_url,
            context=ctx_text,
            aggregator=aggregator,
        )

    # 3. Deduplicate combined findings
    combined = objective_findings + ai_findings
    dedup = DeduplicatorAndPrioritizer()
    unique_findings = dedup.deduplicate(combined)

    # 4. Score and prioritize
    prioritized_findings = dedup.prioritize(unique_findings, execution_result=execution_result)

    # 5. Compile persona summaries
    personas_summary = []
    if plan and plan.personas:
        for p in plan.personas:
            personas_summary.append({
                "id": p.id,
                "name": p.name,
                "experience": p.experience_level,
                "style_or_needs": getattr(p, "accessibility_needs", None) or "Standard",
                "tasks_count": len(p.tasks),
            })

    # 6. Compute task metrics
    metrics = TaskMetricSummary(
        total_personas=len(personas_summary),
        total_tasks=(
            execution_result.total_tasks
            if execution_result
            else (sum(p["tasks_count"] for p in personas_summary) if personas_summary else 0)
        ),
        passed_tasks=execution_result.passed_tasks if execution_result else 0,
        failed_tasks=execution_result.failed_tasks if execution_result else 0,
        inconclusive_tasks=execution_result.inconclusive_tasks if execution_result else 0,
    )

    # 7. Inspection summary dict
    insp_summary = {}
    if inspection_result:
        insp_summary = {
            "title": inspection_result.title,
            "final_url": inspection_result.final_url,
            "total_interactive_elements": inspection_result.summary.total_interactive_elements,
            "links_count": inspection_result.summary.links_count,
            "buttons_count": inspection_result.summary.buttons_count,
            "form_fields_count": inspection_result.summary.form_fields_count,
            "viewport": {
                "width": inspection_result.viewport.width,
                "height": inspection_result.viewport.height,
            },
        }

    # 8. Build complete report model
    report = BlindSpotReport(
        report_id=f"rep_{uuid4().hex[:8]}",
        target_url=target_url,
        context=ctx_text,
        browser=execution_result.browser if execution_result else (inspection_result.browser if inspection_result else "chromium"),
        headless=execution_result.headless if execution_result else True,
        inspection_summary=insp_summary,
        task_metrics=metrics,
        personas_summary=personas_summary,
        findings=prioritized_findings,
    )

    # 9. Save report.json
    json_path = out_dir / "report.json"
    json_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")

    # 10. Save report.html
    html_path = out_dir / "report.html"
    html_content = render_html_report(report, output_dir=out_dir)
    html_path.write_text(html_content, encoding="utf-8")

    # 11. Save findings.sarif for CI/CD & GitHub Code Scanning
    try:
        findings_dicts = [f.model_dump() for f in prioritized_findings]
        write_sarif_file(
            findings=findings_dicts,
            output_path=out_dir / "findings.sarif",
            target_url=target_url,
        )
    except Exception:
        pass

    return report, json_path, html_path

