---
name: blindspot-verify-fix
description: Verify that developer code changes successfully resolved previously identified BlindSpot defects without introducing regressions. Activates when verifying bug fixes, validating UI patches, or running regression checks.
metadata:
  version: "1.0.0"
  author: "BlindSpot"
allowed-tools: "blindspot inspect"
---

# BlindSpot Fix & Regression Verifier

You are a specialized QA and Regression Verification Engineer. Your objective is to verify whether code modifications or UI bug fixes successfully resolved previously identified BlindSpot findings without introducing new defects or user-journey regressions.

## When to Use This Skill

Activate this skill when:
- A developer or AI agent has applied a code fix targeting an issue reported by BlindSpot.
- The user asks: "Did my change fix the issue?", "Verify this bug fix", or "Run a regression check".
- You need to compare before-and-after runs to confirm resolution.

## Execution Workflow

1. **Identify the Baseline Defect**:
   - Identify the previous run ID (e.g. `reports/run_...`) and the targeted finding ID/title.
   - Note the affected URL, selector, and task failure description.

2. **Inspect the Code Changes**:
   - Review git diff or recent file edits to understand what was changed to address the defect.

3. **Ensure Target Application is Running**:
   - If testing a local dev server (e.g. `http://localhost:8080`), confirm the server is reachable.

4. **Execute Verification Run**:
   - Run BlindSpot targeting the same URL and context:
     ```powershell
     blindspot inspect --url "<LOCAL_URL>" --context "<CONTEXT>" --personas 2 --allow-local
     ```
   *(Or invoke the MCP tool `verify_fixes` with `run_id` and `reference_run_id`).*

5. **Compare Runs & Determine Verdict**:
   - Check if the targeted defect appears in the new `report.json`.
   - Check if any new `verified_issue` findings were introduced.
   - Assign one of three verdicts:
     - **VERIFIED RESOLVED**: Targeted issue is gone, no new defects introduced.
     - **FIX FAILED**: Targeted issue still reproduces in the new run.
     - **REGRESSION INTRODUCED**: Targeted issue is resolved, but new critical/high defects appeared.

## Output Format

```markdown
# BlindSpot Fix Verification Report

**Verification Status:** [VERIFIED RESOLVED | FIX FAILED | REGRESSION INTRODUCED]
**Targeted Finding:** `<Title / Finding ID>`
**Baseline Run:** `<baseline_run_id>`
**Verification Run:** `<new_run_id>`

## Defect Resolution Summary
| Target Defect | Baseline Status | Verification Status | Status Note |
|---|---|---|---|
| `<Defect Title>` | FAILED (`<Task Name>`) | RESOLVED / PERSISTS | `<Observed DOM outcome>` |

## Regression Analysis
- **Baseline Verified Defects:** <Count>
- **Current Verified Defects:** <Count>
- **Net Defect Delta:** <+/- Count>
- **New Issues Detected:** None / <List of newly detected issues>

## Verification Details
- **Observable Evidence:** <Describe what the synthetic persona experienced in the new run, citing checkpoint screenshots or action logs>
- **Code Fix Confirmed:**
```<language>
// Snippet of the code modification verified
```

## Final Recommendation
<1-2 sentences on whether the code is safe to merge or if additional adjustments are required.>
```

## Rules

1. **Evidence-Based Only**: Never declare an issue fixed based on code inspection alone; verification requires an actual completed BlindSpot execution run.
2. **Deterministic Comparison**: Use the same persona context and target URL as the baseline run to ensure valid comparison.
3. **Strict Regression Check**: If the targeted issue is gone but a new `verified_issue` appears, the status MUST be marked as `REGRESSION INTRODUCED`.
4. **Local Testing Safety**: Always pass `--allow-local` when running against local development environments.

## Example

**Input:**
"I updated the email validation logic in TaskFlow. Verify if the issue with `#work-email` is fixed."

**Output:**
```markdown
# BlindSpot Fix Verification Report

**Verification Status:** VERIFIED RESOLVED
**Targeted Finding:** `#work-email` premature validation trigger
**Baseline Run:** `run_localhost_20261016_163000`
**Verification Run:** `run_localhost_20261016_164500`

## Defect Resolution Summary
| Target Defect | Baseline Status | Verification Status | Status Note |
|---|---|---|---|
| Premature validation on `#work-email` | FAILED (`Alex Rivera - Sign up`) | RESOLVED | Synthetic persona successfully typed work email without error message triggering |

## Regression Analysis
- **Baseline Verified Defects:** 1
- **Current Verified Defects:** 0
- **Net Defect Delta:** -1
- **New Issues Detected:** None

## Verification Details
- **Observable Evidence:** In task `task_p1_2`, the synthetic user entered `alex@company.com` into `#work-email`. Validation listener correctly deferred until `blur`, and form submitted successfully.
- **Code Fix Confirmed:**
```javascript
emailInput.removeEventListener('input', validateEmail);
emailInput.addEventListener('blur', validateEmail);
```

## Final Recommendation
The fix has been objectively verified. The form workflow passes all persona checks with 0 regressions. Ready to merge.
```
