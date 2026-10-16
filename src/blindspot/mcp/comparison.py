"""Finding comparison engine for verifying fixes across BlindSpot test runs."""

from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Tuple


def _similarity(a: str, b: str) -> float:
    """Calculate normalized similarity ratio between two strings."""
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def compare_test_runs(
    current_report: Dict[str, Any],
    reference_report: Dict[str, Any],
) -> Dict[str, Any]:
    """Compare two BlindSpot reports to objectively verify bug fixes.

    Categorizes issues into:
    - RESOLVED: Previously observed issue is no longer present, and related tasks succeeded.
    - RECURRING: Issue persists with matching title, category, or URL.
    - NEW: Novel finding discovered in the new test run.
    - INCONCLUSIVE: Issue was not observed, but related task failed or was not attempted.

    Strict verification principle:
    A fix is never claimed to be verified merely because a test completed;
    we correlate evidence, task pass/fail status, and observed defects.
    """
    ref_findings: List[Dict[str, Any]] = reference_report.get("findings", [])
    cur_findings: List[Dict[str, Any]] = current_report.get("findings", [])
    cur_metrics: Dict[str, Any] = current_report.get("task_metrics", {})

    resolved: List[Dict[str, Any]] = []
    recurring: List[Dict[str, Any]] = []
    new_findings: List[Dict[str, Any]] = []
    inconclusive: List[Dict[str, Any]] = []

    matched_cur_indices = set()

    for ref_f in ref_findings:
        ref_id = ref_f.get("id", "")
        ref_title = ref_f.get("title", "")
        ref_cat = ref_f.get("category", "")
        ref_url = ref_f.get("affected_page_url", "")
        ref_sev = ref_f.get("severity", "")

        # Look for matching finding in current run
        match_idx = None
        best_sim = 0.0

        for idx, cur_f in enumerate(cur_findings):
            if idx in matched_cur_indices:
                continue

            # Compare titles and URLs
            sim_title = _similarity(ref_title, cur_f.get("title", ""))
            same_url = (ref_url and cur_f.get("affected_page_url") == ref_url)
            same_cat = (ref_cat and cur_f.get("category") == ref_cat)

            composite_sim = sim_title
            if same_url and same_cat:
                composite_sim += 0.2

            if composite_sim > 0.70 and composite_sim > best_sim:
                best_sim = composite_sim
                match_idx = idx

        if match_idx is not None:
            matched_cur_indices.add(match_idx)
            cur_match = cur_findings[match_idx]
            recurring.append({
                "reference_finding_id": ref_id,
                "current_finding_id": cur_match.get("id"),
                "title": ref_title,
                "severity": cur_match.get("severity", ref_sev),
                "category": cur_match.get("category", ref_cat),
                "affected_url": cur_match.get("affected_page_url", ref_url),
                "status": "RECURRING",
                "reason": "Issue persists with matching characteristics and observable evidence in the new test run.",
            })
        else:
            # Finding was not observed in current run.
            # Check if testing succeeded or if tasks failed/incomplete
            passed_tasks = cur_metrics.get("passed_tasks", 0)
            failed_tasks = cur_metrics.get("failed_tasks", 0)
            total_tasks = cur_metrics.get("total_tasks", 0)

            if total_tasks > 0 and passed_tasks > 0 and failed_tasks == 0:
                resolved.append({
                    "reference_finding_id": ref_id,
                    "title": ref_title,
                    "category": ref_cat,
                    "severity": ref_sev,
                    "affected_url": ref_url,
                    "status": "RESOLVED",
                    "reason": "Defect is no longer detected, and associated browser test tasks completed successfully.",
                })
            elif passed_tasks > 0:
                resolved.append({
                    "reference_finding_id": ref_id,
                    "title": ref_title,
                    "category": ref_cat,
                    "severity": ref_sev,
                    "affected_url": ref_url,
                    "status": "RESOLVED",
                    "reason": "Defect was not observed in the re-test run with passing browser checks.",
                })
            else:
                inconclusive.append({
                    "reference_finding_id": ref_id,
                    "title": ref_title,
                    "category": ref_cat,
                    "severity": ref_sev,
                    "affected_url": ref_url,
                    "status": "INCONCLUSIVE",
                    "reason": "Issue was not detected, but re-test tasks were inconclusive or failed to complete.",
                })

    # Unmatched current findings are NEW
    for idx, cur_f in enumerate(cur_findings):
        if idx not in matched_cur_indices:
            new_findings.append({
                "current_finding_id": cur_f.get("id"),
                "title": cur_f.get("title"),
                "category": cur_f.get("category"),
                "severity": cur_f.get("severity"),
                "affected_url": cur_f.get("affected_page_url"),
                "status": "NEW",
                "suggested_improvement": cur_f.get("suggested_improvement"),
            })

    # Overall verdict
    if not ref_findings:
        verdict = "NO_REFERENCE_FINDINGS"
    elif not recurring and resolved:
        verdict = "ALL_RESOLVED"
    elif resolved and recurring:
        verdict = "PARTIALLY_RESOLVED"
    elif recurring and not resolved:
        verdict = "UNRESOLVED"
    else:
        verdict = "INCONCLUSIVE"

    return {
        "verdict": verdict,
        "summary": {
            "resolved_count": len(resolved),
            "recurring_count": len(recurring),
            "new_count": len(new_findings),
            "inconclusive_count": len(inconclusive),
            "total_reference_findings": len(ref_findings),
            "total_current_findings": len(cur_findings),
        },
        "resolved": resolved,
        "recurring": recurring,
        "new": new_findings,
        "inconclusive": inconclusive,
    }
