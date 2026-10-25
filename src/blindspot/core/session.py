"""Session, state, and coverage tracking for BlindSpot test runs."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
import json
import logging
from pathlib import Path
import secrets
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class ScanMode(str, Enum):
    """Intensity and depth of UX/Accessibility audit."""

    QUICK = "quick"         # 1-2 personas, core smoke journey (~2-3 mins)
    STANDARD = "standard"   # 3 personas, standard heuristic & a11y evaluation
    DEEP = "deep"           # 4-6 diverse personas, edge-case testing, WCAG 2.2 AA audit


@dataclass
class TokenBudget:
    """Tracks token consumption and ensures tests remain within budgetary ceilings."""

    max_budget_dollars: Optional[float] = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_dollars: float = 0.0

    # Rough cost estimates per 1M tokens (blended average for fast models)
    PROMPT_COST_PER_M: float = 0.15
    COMPLETION_COST_PER_M: float = 0.60

    def record_usage(self, prompt_tokens: int, completion_tokens: int) -> None:
        """Record newly consumed tokens and update cost."""
        self.prompt_tokens += prompt_tokens
        self.completion_tokens += completion_tokens
        self.total_tokens = self.prompt_tokens + self.completion_tokens

        cost = (
            (self.prompt_tokens / 1_000_000) * self.PROMPT_COST_PER_M
            + (self.completion_tokens / 1_000_000) * self.COMPLETION_COST_PER_M
        )
        self.estimated_cost_dollars = round(cost, 4)

    def is_exceeded(self) -> bool:
        """Check if expenditure exceeds the configured dollar ceiling."""
        if self.max_budget_dollars is None:
            return False
        return self.estimated_cost_dollars >= self.max_budget_dollars


@dataclass
class CoverageTracker:
    """Tracks pages, interactive elements, forms, and WCAG criteria covered during run."""

    urls_discovered: Set[str] = field(default_factory=set)
    urls_visited: Set[str] = field(default_factory=set)
    elements_discovered_count: int = 0
    elements_interacted: Set[str] = field(default_factory=set)
    forms_tested: Set[str] = field(default_factory=set)
    wcag_criteria_evaluated: Set[str] = field(default_factory=set)

    def record_visit(self, url: str) -> None:
        self.urls_visited.add(url)
        self.urls_discovered.add(url)

    def record_interaction(self, element_id: str) -> None:
        if element_id:
            self.elements_interacted.add(element_id)

    def record_wcag(self, criterion: str) -> None:
        if criterion:
            self.wcag_criteria_evaluated.add(criterion)

    @property
    def element_coverage_ratio(self) -> float:
        if self.elements_discovered_count == 0:
            return 0.0
        return round(len(self.elements_interacted) / self.elements_discovered_count, 3)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "urls_discovered": sorted(list(self.urls_discovered)),
            "urls_visited": sorted(list(self.urls_visited)),
            "elements_discovered_count": self.elements_discovered_count,
            "elements_interacted_count": len(self.elements_interacted),
            "element_coverage_ratio": self.element_coverage_ratio,
            "forms_tested": sorted(list(self.forms_tested)),
            "wcag_criteria_evaluated": sorted(list(self.wcag_criteria_evaluated)),
        }


@dataclass
class RunSession:
    """Central lifecycle session managing a BlindSpot test run from start to finish."""

    run_id: str
    target_url: str
    scan_mode: ScanMode = ScanMode.STANDARD
    output_dir: Optional[Path] = None
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: Optional[datetime] = None
    status: str = "running"  # "running", "completed", "failed", "cancelled"
    budget: TokenBudget = field(default_factory=TokenBudget)
    coverage: CoverageTracker = field(default_factory=CoverageTracker)
    findings_count: int = 0
    usability_issues_count: int = 0
    accessibility_issues_count: int = 0
    notes: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        target_url: str,
        scan_mode: ScanMode = ScanMode.STANDARD,
        max_budget_dollars: Optional[float] = None,
        output_dir: Optional[Path] = None,
    ) -> RunSession:
        """Create a new initialized RunSession with unique run_id."""
        now_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        rand_id = secrets.token_hex(3)
        run_id = f"blindspot_{now_str}_{rand_id}"

        budget = TokenBudget(max_budget_dollars=max_budget_dollars)
        coverage = CoverageTracker()
        coverage.record_visit(target_url)

        return cls(
            run_id=run_id,
            target_url=target_url,
            scan_mode=scan_mode,
            output_dir=output_dir,
            budget=budget,
            coverage=coverage,
        )

    def complete(self, status: str = "completed") -> None:
        """Finalize the session lifecycle."""
        self.ended_at = datetime.now(timezone.utc)
        self.status = status

    @property
    def duration_seconds(self) -> float:
        """Calculate elapsed session run time in seconds."""
        end = self.ended_at or datetime.now(timezone.utc)
        return round((end - self.started_at).total_seconds(), 2)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize run session state to dictionary."""
        return {
            "run_id": self.run_id,
            "target_url": self.target_url,
            "scan_mode": self.scan_mode.value,
            "status": self.status,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "duration_seconds": self.duration_seconds,
            "budget": {
                "max_budget_dollars": self.budget.max_budget_dollars,
                "prompt_tokens": self.budget.prompt_tokens,
                "completion_tokens": self.budget.completion_tokens,
                "total_tokens": self.budget.total_tokens,
                "estimated_cost_dollars": self.budget.estimated_cost_dollars,
                "budget_exceeded": self.budget.is_exceeded(),
            },
            "coverage": self.coverage.to_dict(),
            "findings_count": self.findings_count,
            "usability_issues_count": self.usability_issues_count,
            "accessibility_issues_count": self.accessibility_issues_count,
            "notes": self.notes,
        }

    def save_state(self, filepath: Optional[Path] = None) -> Path:
        """Persist session state to a JSON file."""
        target_path = filepath
        if target_path is None:
            base_dir = self.output_dir or Path(f"reports/{self.run_id}")
            base_dir.mkdir(parents=True, exist_ok=True)
            target_path = base_dir / "run_state.json"

        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

        return target_path
