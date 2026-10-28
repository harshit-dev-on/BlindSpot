"""Markdown report renderer for BlindSpot UX findings and user journeys.

Generates a clean, GitHub-flavored Markdown document summarizing the entire audit,
including executive metrics, persona profiles, step-by-step execution traces, and
prioritized usability/accessibility findings.
"""

from pathlib import Path
from typing import List, Optional

from blindspot.execution.models import ExecutionRunResult
from blindspot.reporting.models import BlindSpotReport, FindingCategory, SeverityLevel, UXFinding


def _severity_icon(severity: SeverityLevel) -> str:
    icons = {
        SeverityLevel.CRITICAL: "🔴 **CRITICAL**",
        SeverityLevel.HIGH: "🟠 **HIGH**",
        SeverityLevel.MEDIUM: "🟡 **MEDIUM**",
        SeverityLevel.LOW: "🔵 **LOW**",
        SeverityLevel.INFORMATIONAL: "⚪ **INFO**",
    }
    return icons.get(severity, str(severity))


def _category_icon(category: FindingCategory) -> str:
    icons = {
        FindingCategory.VERIFIED_ISSUE: "🚨 Objectively Verified Issue",
        FindingCategory.USABILITY_OBSERVATION: "👁️ Usability Observation",
        FindingCategory.POTENTIAL_IMPROVEMENT: "💡 Potential Improvement",
    }
    return icons.get(category, str(category))


def render_markdown_report(
    report: BlindSpotReport,
    execution_result: Optional[ExecutionRunResult] = None,
    output_dir: Optional[Path] = None,
) -> str:
    """Render a comprehensive GitHub-Flavored Markdown audit report."""
    md: List[str] = []

    # Title & Header
    md.append(f"# 🔍 BlindSpot UX & Accessibility Audit Report")
    md.append("")
    md.append(f"> **Report ID:** `{report.report_id}`  ")
    md.append(f"> **Target Website:** [{report.target_url}]({report.target_url})  ")
    md.append(f"> **Generated:** `{report.generated_at}`  ")
    md.append(f"> **Browser Engine:** `{report.browser}` ({'Headless' if report.headless else 'Visible Window'})  ")
    if report.context:
        md.append(f"> **Testing Context:** {report.context}")
    md.append("")
    md.append("---")
    md.append("")

    # 1. Executive Summary & Metrics
    md.append("## 📊 Executive Summary")
    md.append("")
    metrics = report.task_metrics
    md.append("| Metric | Count | Status |")
    md.append("| :--- | :---: | :--- |")
    md.append(f"| **Simulated Personas** | **{metrics.total_personas}** | Configured profiles |")
    md.append(f"| **Total User Tasks** | **{metrics.total_tasks}** | Evaluated browser journeys |")
    md.append(f"| **Passed Tasks** | **{metrics.passed_tasks}** | ✅ Meets observable success criteria |")
    md.append(f"| **Failed Tasks** | **{metrics.failed_tasks}** | ❌ Blocked or hit action limit |")
    md.append(f"| **Inconclusive Tasks** | **{metrics.inconclusive_tasks}** | ⚠️ Partial or unconfirmed completion |")
    md.append("")

    # Findings tally
    verified_cnt = sum(1 for f in report.findings if f.category == FindingCategory.VERIFIED_ISSUE)
    obs_cnt = sum(1 for f in report.findings if f.category == FindingCategory.USABILITY_OBSERVATION)
    imp_cnt = sum(1 for f in report.findings if f.category == FindingCategory.POTENTIAL_IMPROVEMENT)

    md.append("### 🏷️ Identified Usability & Accessibility Findings")
    md.append("")
    md.append(f"- 🚨 **Objectively Verified Issues:** {verified_cnt}")
    md.append(f"- 👁️ **Usability Observations:** {obs_cnt}")
    md.append(f"- 💡 **Potential Improvements:** {imp_cnt}")
    md.append(f"- **Total Identified Findings:** {len(report.findings)}")
    md.append("")
    md.append("---")
    md.append("")

    # 2. Simulated Personas
    if report.personas_summary:
        md.append("## 👥 Simulated User Personas")
        md.append("")
        md.append("| Persona | Experience | Accessibility & Needs | Tasks |")
        md.append("| :--- | :--- | :--- | :---: |")
        for p in report.personas_summary:
            md.append(f"| **{p.get('name', 'Persona')}** | {p.get('experience', 'Standard')} | {p.get('style_or_needs', 'Standard Desktop')} | {p.get('tasks_count', 0)} |")
        md.append("")
        md.append("---")
        md.append("")

    # 3. User Journey Execution Details
    if execution_result and execution_result.personas:
        md.append("## 🚀 Step-by-Step User Journey Execution")
        md.append("")
        for persona_res in execution_result.personas:
            md.append(f"### Persona: {persona_res.persona_name}")
            md.append("")
            tasks_list = getattr(persona_res, "task_results", None) or getattr(persona_res, "tasks", [])
            for task_res in tasks_list:
                status_badge = "✅ PASSED" if task_res.status.value == "success" else ("❌ FAILED" if task_res.status.value == "failure" else "⚠️ INCONCLUSIVE")
                md.append(f"#### Task: {task_res.task_objective}")
                md.append(f"- **Status:** {status_badge}")
                md.append(f"- **Steps Taken:** {len(task_res.actions_taken)} actions")
                md.append(f"- **Initial URL:** `{task_res.initial_url}`")
                md.append(f"- **Final URL:** `{task_res.final_url}`")
                if task_res.error_message:
                    md.append(f"- **Failure Detail:** {task_res.error_message}")
                if task_res.evidence:
                    md.append(f"- **Observed Evidence:**")
                    for ev in task_res.evidence:
                        md.append(f"  - {ev}")

                # Step details table
                if task_res.actions_taken:
                    md.append("")
                    md.append("| Step | Action | Target / Details | Reasoning | Outcome |")
                    md.append("| :---: | :--- | :--- | :--- | :---: |")
                    for act in task_res.actions_taken:
                        act_type = getattr(act.action, "action", "")
                        if hasattr(act_type, "value"):
                            act_type = act_type.value
                        target = getattr(act.action, "target", "") or ""
                        val = getattr(act.action, "value", "") or getattr(act.action, "text", "") or ""
                        details = f"`{target}` {val}".strip() if target or val else "—"
                        reason = getattr(act.action, "reasoning", "") or ""
                        res_icon = "✓" if act.success else "✖"
                        md.append(f"| {act.step} | **{act_type}** | {details} | {reason} | {res_icon} |")
                md.append("")
        md.append("---")
        md.append("")

    # 4. Prioritized Findings
    md.append("## 🏆 Prioritized UX & Accessibility Findings")
    md.append("")
    if not report.findings:
        md.append("🎉 *No critical UX defects or accessibility violations identified during this session.*")
        md.append("")
    else:
        for idx, finding in enumerate(report.findings, start=1):
            md.append(f"### #{idx}. {finding.title}")
            md.append("")
            md.append(f"- **Severity:** {_severity_icon(finding.severity)}")
            md.append(f"- **Category:** {_category_icon(finding.category)}")
            md.append(f"- **Confidence:** `{int(finding.confidence * 100)}%`")
            if finding.affected_page_url:
                md.append(f"- **Affected URL:** [{finding.affected_page_url}]({finding.affected_page_url})")
            md.append("")
            md.append(f"**Description:**  \n{finding.description}")
            md.append("")

            if finding.supporting_evidence:
                md.append("**Supporting Evidence:**")
                for ev in finding.supporting_evidence:
                    md.append(f"- {ev}")
                md.append("")

            if finding.reproduction_steps:
                md.append("**Reproduction Steps:**")
                for step_idx, step_desc in enumerate(finding.reproduction_steps, start=1):
                    md.append(f"{step_idx}. {step_desc}")
                md.append("")

            if finding.suggested_improvement:
                md.append(f"> 💡 **Suggested Remediation:**  \n> {finding.suggested_improvement}")
                if finding.expected_benefit:
                    md.append(f"> \n> **Expected User Benefit:** {finding.expected_benefit}")
                md.append("")

            md.append("---")
            md.append("")

    # 5. Technical Inspection Summary
    insp = report.inspection_summary
    if insp:
        md.append("## 🛠️ Technical & DOM Inspection Summary")
        md.append("")
        md.append(f"- **Page Title:** `{insp.get('title', 'Unknown')}`")
        md.append(f"- **Final URL:** [{insp.get('final_url', report.target_url)}]({insp.get('final_url', report.target_url)})")
        md.append(f"- **Total Interactive Elements:** `{insp.get('total_interactive_elements', 0)}`")
        md.append(f"  - Links: `{insp.get('links_count', 0)}`")
        md.append(f"  - Buttons: `{insp.get('buttons_count', 0)}`")
        md.append(f"  - Form Inputs / Fields: `{insp.get('form_fields_count', 0)}`")
        vp = insp.get("viewport", {})
        if vp:
            md.append(f"- **Tested Viewport:** `{vp.get('width', 1280)}x{vp.get('height', 800)}`")
        md.append("")

    # Footer
    md.append("---")
    md.append("*Generated automatically by BlindSpot Autonomous UX & Accessibility Audit Agent.*")
    md.append("")

    return "\n".join(md)
