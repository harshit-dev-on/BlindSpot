"""Data models for UX analysis findings, severity, categorization, and reports."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class FindingCategory(str, Enum):
    """Classification category distinguishing objective bugs from subjective UX advice."""

    VERIFIED_ISSUE = "verified_issue"
    USABILITY_OBSERVATION = "usability_observation"
    POTENTIAL_IMPROVEMENT = "potential_improvement"

    @property
    def label(self) -> str:
        labels = {
            FindingCategory.VERIFIED_ISSUE: "Objectively Verified Issue",
            FindingCategory.USABILITY_OBSERVATION: "Usability Observation",
            FindingCategory.POTENTIAL_IMPROVEMENT: "Potential Improvement",
        }
        return labels.get(self, self.value)


class SeverityLevel(str, Enum):
    """Documented severity level indicating impact on user experience and task success."""

    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    INFORMATIONAL = "Informational"

    @property
    def weight(self) -> int:
        weights = {
            SeverityLevel.CRITICAL: 50,
            SeverityLevel.HIGH: 35,
            SeverityLevel.MEDIUM: 20,
            SeverityLevel.LOW: 10,
            SeverityLevel.INFORMATIONAL: 5,
        }
        return weights.get(self, 0)


class UXFinding(BaseModel):
    """A validated usability finding with evidence, reproduction steps, and severity."""

    id: str = Field(..., description="Unique finding identifier (e.g. 'finding_1')")
    title: str = Field(..., description="Concise, descriptive title of the usability finding")
    category: FindingCategory = Field(
        ...,
        description="Category: verified_issue (objective defect), usability_observation, or potential_improvement",
    )
    description: str = Field(..., description="Detailed description of what occurred and why it matters")
    severity: SeverityLevel = Field(
        ...,
        description="Severity: Critical, High, Medium, Low, or Informational",
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence score between 0.0 (unconfirmed heuristic) and 1.0 (verified fact)",
    )
    affected_page_url: str = Field(default="", description="Relevant page URL where the issue was observed")
    supporting_evidence: List[str] = Field(
        default_factory=list,
        description="Observable facts, error messages, keyword matches, or DOM elements supporting the finding",
    )
    persona_ids: List[str] = Field(
        default_factory=list,
        description="IDs of simulated personas affected by or encountering this finding",
    )
    task_ids: List[str] = Field(
        default_factory=list,
        description="IDs of assigned tasks during which this finding arose",
    )
    reproduction_steps: List[str] = Field(
        default_factory=list,
        description="Sequential steps to reproduce or observe the finding",
    )
    suggested_improvement: str = Field(
        ...,
        description="Actionable, concrete design or engineering recommendation to resolve the issue",
    )
    expected_benefit: str = Field(
        ...,
        description="Explanation of how the suggested improvement enhances the user experience",
    )
    screenshot_paths: List[str] = Field(
        default_factory=list,
        description="File paths to evidence screenshots captured at the moment of discovery",
    )
    priority_rank: int = Field(default=0, description="Assigned priority ranking (1 = highest priority)")
    priority_score: float = Field(default=0.0, description="Calculated composite priority score")
    priority_reasoning: str = Field(default="", description="Explanation of why this priority rank was assigned")

    @field_validator("category", mode="before")
    @classmethod
    def normalize_category(cls, val: Any) -> FindingCategory:
        if isinstance(val, FindingCategory):
            return val
        if isinstance(val, str):
            clean = val.lower().strip()
            for cat in FindingCategory:
                if cat.value == clean or cat.name.lower() == clean:
                    return cat
                if "verified" in clean or "issue" in clean or "bug" in clean or "defect" in clean:
                    return FindingCategory.VERIFIED_ISSUE
                if "observation" in clean or "usability" in clean:
                    return FindingCategory.USABILITY_OBSERVATION
                if "improvement" in clean or "suggestion" in clean:
                    return FindingCategory.POTENTIAL_IMPROVEMENT
        return FindingCategory.USABILITY_OBSERVATION

    @field_validator("severity", mode="before")
    @classmethod
    def normalize_severity(cls, val: Any) -> SeverityLevel:
        if isinstance(val, SeverityLevel):
            return val
        if isinstance(val, str):
            clean = val.capitalize().strip()
            for sev in SeverityLevel:
                if sev.value == clean or sev.name == clean.upper():
                    return sev
        return SeverityLevel.MEDIUM


class UXFindingDraft(BaseModel):
    """Schema for individual findings returned by the AI analysis prompt."""

    title: str = Field(..., description="Concise title of the usability finding")
    category: FindingCategory = Field(
        ...,
        description="verified_issue, usability_observation, or potential_improvement",
    )
    description: str = Field(..., description="Detailed description of what occurred")
    severity: SeverityLevel = Field(..., description="Critical, High, Medium, Low, or Informational")
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    affected_page_url: str = Field(default="")
    supporting_evidence: List[str] = Field(default_factory=list)
    persona_ids: List[str] = Field(default_factory=list)
    task_ids: List[str] = Field(default_factory=list)
    reproduction_steps: List[str] = Field(default_factory=list)
    suggested_improvement: str = Field(..., description="Actionable recommendation")
    expected_benefit: str = Field(..., description="Expected UX benefit")


class AIFindingsOutput(BaseModel):
    """Validated structured output payload returned by the AI UX analyzer."""

    findings: List[UXFindingDraft] = Field(
        default_factory=list,
        description="List of usability observations and potential improvements identified by the model",
    )


class TaskMetricSummary(BaseModel):
    """Aggregate statistics of task execution outcomes."""

    total_personas: int = 0
    total_tasks: int = 0
    passed_tasks: int = 0
    failed_tasks: int = 0
    inconclusive_tasks: int = 0

    @property
    def pass_rate_percent(self) -> float:
        if self.total_tasks == 0:
            return 0.0
        return round((self.passed_tasks / self.total_tasks) * 100, 1)


class BlindSpotReport(BaseModel):
    """Complete machine-readable UX inspection and testing report."""

    report_id: str
    generated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    target_url: str
    context: str
    browser: str = "chromium"
    headless: bool = True
    inspection_summary: Dict[str, Any] = Field(default_factory=dict)
    task_metrics: TaskMetricSummary = Field(default_factory=TaskMetricSummary)
    personas_summary: List[Dict[str, Any]] = Field(default_factory=list)
    findings: List[UXFinding] = Field(default_factory=list)
    limitations: List[str] = Field(
        default_factory=lambda: [
            "Simulated persona testing provides qualitative heuristic insights and does not replace empirical usability testing with human participants.",
            "Accessibility evaluation is limited to structural DOM heuristics and does not constitute full WCAG 2.2 AA certification.",
            "Testing was executed in an automated browser environment; client anti-bot systems or dynamic third-party scripts may affect observations.",
        ]
    )
    disclaimer: str = (
        "Simulated user personas are synthetic models used for heuristic discovery. "
        "Their actions and feedback do not constitute real user data or claim statistical significance."
    )

    @property
    def verified_issues_count(self) -> int:
        return sum(1 for f in self.findings if f.category == FindingCategory.VERIFIED_ISSUE)

    @property
    def usability_observations_count(self) -> int:
        return sum(1 for f in self.findings if f.category == FindingCategory.USABILITY_OBSERVATION)

    @property
    def potential_improvements_count(self) -> int:
        return sum(1 for f in self.findings if f.category == FindingCategory.POTENTIAL_IMPROVEMENT)
