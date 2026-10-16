"""Responsive, self-contained HTML report renderer for BlindSpot UX findings."""

import html
from pathlib import Path
from typing import List, Optional
from blindspot.reporting.models import BlindSpotReport, FindingCategory, SeverityLevel, UXFinding


def _esc(val: Optional[str]) -> str:
    """Safely escape text for HTML output."""
    if val is None:
        return ""
    return html.escape(str(val))


def _severity_badge_class(severity: SeverityLevel) -> str:
    mapping = {
        SeverityLevel.CRITICAL: "badge-critical",
        SeverityLevel.HIGH: "badge-high",
        SeverityLevel.MEDIUM: "badge-medium",
        SeverityLevel.LOW: "badge-low",
        SeverityLevel.INFORMATIONAL: "badge-info",
    }
    return mapping.get(severity, "badge-info")


def _category_badge_class(category: FindingCategory) -> str:
    mapping = {
        FindingCategory.VERIFIED_ISSUE: "badge-verified",
        FindingCategory.USABILITY_OBSERVATION: "badge-observation",
        FindingCategory.POTENTIAL_IMPROVEMENT: "badge-improvement",
    }
    return mapping.get(category, "badge-observation")


def render_finding_card(finding: UXFinding, output_dir: Optional[Path] = None) -> str:
    """Render an individual finding card with badges, evidence, reproduction steps, and screenshots."""
    sev_class = _severity_badge_class(finding.severity)
    cat_class = _category_badge_class(finding.category)

    # Screenshots preview
    screenshot_html = ""
    if finding.screenshot_paths:
        screenshot_items: List[str] = []
        for sp in finding.screenshot_paths:
            p = Path(sp)
            # Compute relative path if inside output_dir
            rel_src = sp
            if output_dir:
                try:
                    rel_src = p.relative_to(output_dir).as_posix()
                except ValueError:
                    rel_src = p.name

            # Check if exists on disk
            exists = p.exists() if hasattr(p, "exists") else False
            if exists:
                screenshot_items.append(
                    f'<div class="screenshot-box">'
                    f'  <a href="{_esc(rel_src)}" target="_blank" rel="noopener">'
                    f'    <img src="{_esc(rel_src)}" alt="Evidence screenshot" loading="lazy" />'
                    f'  </a>'
                    f'  <span class="screenshot-label">{_esc(p.name)}</span>'
                    f'</div>'
                )
            else:
                screenshot_items.append(
                    f'<div class="screenshot-box missing">'
                    f'  <div class="placeholder-icon">📷</div>'
                    f'  <span class="screenshot-label">{_esc(p.name)} (checkpoint logged)</span>'
                    f'</div>'
                )
        if screenshot_items:
            screenshot_html = (
                '<div class="finding-section">'
                '  <h4 class="section-subtitle">Visual Evidence</h4>'
                '  <div class="screenshots-grid">' + "".join(screenshot_items) + '</div>'
                '</div>'
            )

    # Reproduction steps
    repro_html = ""
    if finding.reproduction_steps:
        steps_list = "".join(f"<li>{_esc(step)}</li>" for step in finding.reproduction_steps)
        repro_html = (
            '<div class="finding-section">'
            '  <h4 class="section-subtitle">Reproduction Steps</h4>'
            f'  <ol class="repro-list">{steps_list}</ol>'
            '</div>'
        )

    # Supporting evidence
    evidence_html = ""
    if finding.supporting_evidence:
        ev_items = "".join(f"<li><code>{_esc(ev)}</code></li>" for ev in finding.supporting_evidence)
        evidence_html = (
            '<div class="finding-section">'
            '  <h4 class="section-subtitle">Supporting Evidence</h4>'
            f'  <ul class="evidence-list">{ev_items}</ul>'
            '</div>'
        )

    # Persona / Task tags
    meta_tags: List[str] = []
    if finding.persona_ids:
        meta_tags.extend(f'<span class="tag persona-tag">Persona: {_esc(pid)}</span>' for pid in finding.persona_ids)
    if finding.task_ids:
        meta_tags.extend(f'<span class="tag task-tag">Task: {_esc(tid)}</span>' for tid in finding.task_ids)
    if finding.affected_page_url:
        meta_tags.append(f'<span class="tag url-tag">URL: {_esc(finding.affected_page_url)}</span>')

    tags_html = f'<div class="tags-container">{"".join(meta_tags)}</div>' if meta_tags else ""

    confidence_pct = int(finding.confidence * 100)

    return f"""
    <article class="finding-card severity-{finding.severity.value.lower()}" id="{_esc(finding.id)}">
      <header class="card-header">
        <div class="header-left">
          <span class="rank-badge">#{finding.priority_rank}</span>
          <span class="badge {cat_class}">{_esc(finding.category.label)}</span>
          <span class="badge {sev_class}">{_esc(finding.severity.value)}</span>
          <span class="confidence-badge" title="Confidence: {confidence_pct}%">Confidence: {confidence_pct}%</span>
        </div>
        <div class="priority-score">Score: {finding.priority_score}</div>
      </header>

      <h3 class="card-title">{_esc(finding.title)}</h3>
      <p class="card-desc">{_esc(finding.description)}</p>

      {tags_html}
      {repro_html}
      {evidence_html}
      {screenshot_html}

      <div class="recommendation-box">
        <div class="rec-item">
          <strong>Recommended Fix:</strong> {_esc(finding.suggested_improvement)}
        </div>
        <div class="rec-item benefit">
          <strong>Expected Benefit:</strong> {_esc(finding.expected_benefit)}
        </div>
      </div>

      <footer class="card-footer">
        <span class="reasoning-text"><em>Priority Rationale:</em> {_esc(finding.priority_reasoning)}</span>
      </footer>
    </article>
    """


def render_html_report(report: BlindSpotReport, output_dir: Optional[Path] = None) -> str:
    """Generate the complete, responsive HTML report string."""
    metrics = report.task_metrics

    # Group findings by category
    verified = [f for f in report.findings if f.category == FindingCategory.VERIFIED_ISSUE]
    usability = [f for f in report.findings if f.category == FindingCategory.USABILITY_OBSERVATION]
    improvements = [f for f in report.findings if f.category == FindingCategory.POTENTIAL_IMPROVEMENT]

    verified_cards = "".join(render_finding_card(f, output_dir) for f in verified) if verified else "<p class='empty-state'>No objectively verified defects detected.</p>"
    usability_cards = "".join(render_finding_card(f, output_dir) for f in usability) if usability else "<p class='empty-state'>No usability friction points flagged.</p>"
    improvements_cards = "".join(render_finding_card(f, output_dir) for f in improvements) if improvements else "<p class='empty-state'>No potential improvements identified.</p>"

    # Personas list items
    persona_rows = ""
    for p in report.personas_summary:
        persona_rows += f"""
        <tr>
          <td><strong>{_esc(p.get('name'))}</strong> <span class="dim">({_esc(p.get('id'))})</span></td>
          <td>{_esc(p.get('experience'))}</td>
          <td>{_esc(p.get('style_or_needs'))}</td>
          <td>{_esc(str(p.get('tasks_count', 0)))} tasks</td>
        </tr>
        """

    # Limitations list
    limitations_items = "".join(f"<li>{_esc(lim)}</li>" for lim in report.limitations)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>BlindSpot UX Report - {_esc(report.target_url)}</title>
  <style>
    :root {{
      --bg: #0b0f19;
      --card-bg: #131b2e;
      --card-border: #1e293b;
      --header-bg: #101827;
      --text-main: #f1f5f9;
      --text-muted: #94a3b8;
      --accent: #38bdf8;
      --accent-glow: rgba(56, 189, 248, 0.15);
      --red: #ef4444;
      --orange: #f97316;
      --yellow: #eab308;
      --green: #22c55e;
      --blue: #3b82f6;
      --slate: #64748b;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background-color: var(--bg);
      color: var(--text-main);
      line-height: 1.6;
      padding-bottom: 4rem;
    }}
    header.site-header {{
      background: var(--header-bg);
      border-bottom: 1px solid var(--card-border);
      padding: 2rem 1.5rem;
      margin-bottom: 2rem;
    }}
    .container {{ max-width: 1100px; margin: 0 auto; padding: 0 1rem; }}
    .header-content {{ display: flex; flex-direction: column; gap: 0.5rem; }}
    .brand {{ font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1.5px; color: var(--accent); font-weight: 700; }}
    .title {{ font-size: 1.85rem; font-weight: 800; color: #fff; word-break: break-all; }}
    .meta-line {{ display: flex; flex-wrap: wrap; gap: 1rem; font-size: 0.9rem; color: var(--text-muted); }}

    /* KPI Stats Bar */
    .kpi-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
      gap: 1rem;
      margin-bottom: 2.5rem;
    }}
    .kpi-card {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 8px;
      padding: 1rem;
      text-align: center;
    }}
    .kpi-val {{ font-size: 1.8rem; font-weight: 800; color: #fff; }}
    .kpi-val.green {{ color: var(--green); }}
    .kpi-val.red {{ color: var(--red); }}
    .kpi-val.orange {{ color: var(--orange); }}
    .kpi-val.accent {{ color: var(--accent); }}
    .kpi-label {{ font-size: 0.75rem; text-transform: uppercase; color: var(--text-muted); font-weight: 600; letter-spacing: 0.5px; }}

    /* Disclaimer Alert */
    .disclaimer-banner {{
      background: rgba(30, 41, 59, 0.7);
      border-left: 4px solid var(--accent);
      padding: 1rem 1.25rem;
      border-radius: 4px;
      margin-bottom: 2.5rem;
      font-size: 0.9rem;
      color: #cbd5e1;
    }}
    .disclaimer-banner strong {{ color: var(--accent); }}

    /* Headings */
    h2.section-title {{
      font-size: 1.35rem;
      font-weight: 700;
      margin-bottom: 1.25rem;
      color: #fff;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }}
    .category-group {{ margin-bottom: 3rem; }}

    /* Cards */
    .finding-card {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 10px;
      padding: 1.5rem;
      margin-bottom: 1.5rem;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
      transition: border-color 0.2s ease;
    }}
    .finding-card:hover {{ border-color: rgba(56, 189, 248, 0.4); }}
    .card-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 0.75rem;
      margin-bottom: 0.75rem;
    }}
    .header-left {{ display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap; }}
    .rank-badge {{
      background: #0f172a;
      color: var(--accent);
      border: 1px solid var(--accent);
      padding: 0.15rem 0.5rem;
      border-radius: 4px;
      font-weight: 700;
      font-size: 0.8rem;
    }}
    .badge {{
      display: inline-block;
      padding: 0.2rem 0.65rem;
      border-radius: 9999px;
      font-size: 0.75rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}
    .badge-verified {{ background: rgba(239, 68, 68, 0.2); color: #fca5a5; border: 1px solid rgba(239, 68, 68, 0.4); }}
    .badge-observation {{ background: rgba(249, 115, 22, 0.2); color: #fdba74; border: 1px solid rgba(249, 115, 22, 0.4); }}
    .badge-improvement {{ background: rgba(56, 189, 248, 0.2); color: #7dd3fc; border: 1px solid rgba(56, 189, 248, 0.4); }}

    .badge-critical {{ background: #dc2626; color: #fff; }}
    .badge-high {{ background: #ea580c; color: #fff; }}
    .badge-medium {{ background: #ca8a04; color: #fff; }}
    .badge-low {{ background: #2563eb; color: #fff; }}
    .badge-info {{ background: #475569; color: #fff; }}

    .confidence-badge {{ font-size: 0.75rem; color: var(--text-muted); background: #0f172a; padding: 0.2rem 0.5rem; border-radius: 4px; }}
    .priority-score {{ font-size: 0.85rem; font-weight: 700; color: var(--accent); }}

    .card-title {{ font-size: 1.15rem; font-weight: 700; color: #fff; margin-bottom: 0.5rem; }}
    .card-desc {{ color: #cbd5e1; font-size: 0.95rem; margin-bottom: 1rem; }}

    /* Tags */
    .tags-container {{ display: flex; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 1rem; }}
    .tag {{ font-size: 0.75rem; padding: 0.15rem 0.5rem; border-radius: 4px; background: #0f172a; color: var(--text-muted); border: 1px solid var(--card-border); }}
    .tag.persona-tag {{ border-color: rgba(168, 85, 247, 0.4); color: #d8b4fe; }}
    .tag.task-tag {{ border-color: rgba(59, 130, 246, 0.4); color: #93c5fd; }}
    .tag.url-tag {{ border-color: rgba(34, 197, 94, 0.4); color: #86efac; word-break: break-all; }}

    .finding-section {{ margin: 1rem 0; }}
    .section-subtitle {{ font-size: 0.85rem; text-transform: uppercase; color: var(--text-muted); letter-spacing: 0.5px; margin-bottom: 0.5rem; }}
    .repro-list, .evidence-list {{ margin-left: 1.25rem; font-size: 0.9rem; color: #cbd5e1; }}
    .repro-list li, .evidence-list li {{ margin-bottom: 0.35rem; }}
    code {{ background: #0b0f19; padding: 0.15rem 0.4rem; border-radius: 4px; font-size: 0.85rem; color: #e2e8f0; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; }}

    /* Recommendations Box */
    .recommendation-box {{
      background: #0f172a;
      border: 1px solid #1e293b;
      border-radius: 6px;
      padding: 1rem;
      margin: 1.25rem 0;
    }}
    .rec-item {{ font-size: 0.92rem; color: #e2e8f0; margin-bottom: 0.5rem; }}
    .rec-item.benefit {{ color: #a7f3d0; margin-bottom: 0; }}
    .rec-item strong {{ color: #fff; }}

    /* Screenshots Grid */
    .screenshots-grid {{ display: flex; flex-wrap: wrap; gap: 1rem; margin-top: 0.5rem; }}
    .screenshot-box {{
      width: 200px;
      border: 1px solid var(--card-border);
      border-radius: 6px;
      overflow: hidden;
      background: #0b0f19;
      display: flex;
      flex-direction: column;
    }}
    .screenshot-box img {{ width: 100%; height: 120px; object-fit: cover; display: block; border-bottom: 1px solid var(--card-border); }}
    .screenshot-box.missing {{ height: 120px; display: flex; align-items: center; justify-content: center; text-align: center; color: var(--text-muted); padding: 0.5rem; }}
    .placeholder-icon {{ font-size: 1.5rem; margin-bottom: 0.25rem; }}
    .screenshot-label {{ font-size: 0.7rem; color: var(--text-muted); padding: 0.25rem 0.5rem; word-break: break-all; }}

    .card-footer {{ font-size: 0.8rem; color: var(--text-muted); border-top: 1px solid #1e293b; padding-top: 0.75rem; }}
    .empty-state {{ color: var(--text-muted); font-style: italic; padding: 1rem 0; }}

    /* Personas Table */
    table.data-table {{ width: 100%; border-collapse: collapse; margin-top: 0.75rem; font-size: 0.9rem; }}
    table.data-table th, table.data-table td {{ padding: 0.75rem 1rem; text-align: left; border-bottom: 1px solid var(--card-border); }}
    table.data-table th {{ background: #0f172a; color: var(--text-muted); text-transform: uppercase; font-size: 0.75rem; }}
    table.data-table tr:hover td {{ background: rgba(255, 255, 255, 0.02); }}
    .dim {{ color: var(--text-muted); font-size: 0.8rem; }}

    /* Limitations Box */
    .limitations-box {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 8px;
      padding: 1.5rem;
      margin-top: 2rem;
    }}
    .limitations-box ul {{ margin-left: 1.5rem; color: var(--text-muted); font-size: 0.85rem; }}
    .limitations-box li {{ margin-bottom: 0.5rem; }}
  </style>
</head>
<body>

  <header class="site-header">
    <div class="container header-content">
      <span class="brand">BlindSpot Automated UX Testing Report</span>
      <h1 class="title">{_esc(report.target_url)}</h1>
      <div class="meta-line">
        <span><strong>Context:</strong> {_esc(report.context)}</span>
        <span>•</span>
        <span><strong>Generated:</strong> {_esc(report.generated_at[:19].replace('T', ' '))} UTC</span>
        <span>•</span>
        <span><strong>Engine:</strong> {_esc(report.browser)} ({'Headless' if report.headless else 'Headed'})</span>
      </div>
    </div>
  </header>

  <main class="container">

    <!-- KPI Summary Grid -->
    <section class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-val accent">{report.task_metrics.total_personas}</div>
        <div class="kpi-label">Simulated Personas</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-val">{report.task_metrics.total_tasks}</div>
        <div class="kpi-label">Tasks Executed</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-val green">{report.task_metrics.passed_tasks}</div>
        <div class="kpi-label">Tasks Passed</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-val red">{report.task_metrics.failed_tasks}</div>
        <div class="kpi-label">Tasks Failed</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-val orange">{report.task_metrics.inconclusive_tasks}</div>
        <div class="kpi-label">Inconclusive</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-val red">{report.verified_issues_count}</div>
        <div class="kpi-label">Verified Defects</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-val orange">{report.usability_observations_count}</div>
        <div class="kpi-label">UX Observations</div>
      </div>
    </section>

    <!-- Methodology & Statistical Disclaimer -->
    <div class="disclaimer-banner">
      <strong>Research Methodology Notice:</strong> {_esc(report.disclaimer)}
    </div>

    <!-- Group 1: Objectively Verified Issues -->
    <section class="category-group" id="verified-issues">
      <h2 class="section-title">
        <span style="color: var(--red);">●</span> Objectively Verified Defects ({report.verified_issues_count})
      </h2>
      <p class="card-desc">Functional bugs, navigation failures, action crashes, and structural accessibility defects confirmed by browser execution.</p>
      {verified_cards}
    </section>

    <!-- Group 2: Usability Observations -->
    <section class="category-group" id="usability-observations">
      <h2 class="section-title">
        <span style="color: var(--orange);">●</span> Usability Observations ({report.usability_observations_count})
      </h2>
      <p class="card-desc">Friction points, ambiguous calls to action, confusing flow steps, or feedback deficiencies observed during simulated journeys.</p>
      {usability_cards}
    </section>

    <!-- Group 3: Potential Improvements -->
    <section class="category-group" id="potential-improvements">
      <h2 class="section-title">
        <span style="color: var(--accent);">●</span> Potential Improvements ({report.potential_improvements_count})
      </h2>
      <p class="card-desc">Constructive opportunities to enhance overall user delight, streamline journeys, and elevate conversion.</p>
      {improvements_cards}
    </section>

    <!-- Tested Personas Overview -->
    <section class="category-group" id="personas-overview">
      <h2 class="section-title">Simulated Persona Profiles</h2>
      <div class="finding-card" style="padding: 0; overflow-x: auto;">
        <table class="data-table">
          <thead>
            <tr>
              <th>Persona Archetype</th>
              <th>Proficiency</th>
              <th>Browsing Style / Needs</th>
              <th>Assigned Tasks</th>
            </tr>
          </thead>
          <tbody>
            {persona_rows}
          </tbody>
        </table>
      </div>
    </section>

    <!-- Limitations -->
    <section class="limitations-box">
      <h3 style="font-size: 1rem; color: #fff; margin-bottom: 0.75rem;">Audit Limitations & Boundary Conditions</h3>
      <ul>
        {limitations_items}
      </ul>
    </section>

  </main>

</body>
</html>"""
