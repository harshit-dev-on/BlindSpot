"""In-memory job management and background execution coordinator for the web interface."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import threading
from typing import Any, Dict, List, Optional

from blindspot.core.runner import PipelineConfig, PipelineResult, generate_run_id, run_pipeline
from blindspot.web.models import CreateRunRequest, RunListItem, RunStatusResponse


RUN_ID_REGEX = re.compile(r"^[a-zA-Z0-9_-]+$")


@dataclass
class RunRecord:
    """State tracking for a web-managed BlindSpot test run."""

    run_id: str
    target_url: str
    context: str
    created_at: str
    config: CreateRunRequest
    output_dir: Path
    status: str = "queued"  # queued, running, completed, failed, cancelled
    stage: Optional[str] = "initialization"
    progress_message: Optional[str] = "Test run queued..."
    error_message: Optional[str] = None
    latest_screenshot: Optional[str] = None
    cancel_event: threading.Event = field(default_factory=threading.Event)
    events: List[Dict[str, Any]] = field(default_factory=list)
    result: Optional[PipelineResult] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    thread: Optional[threading.Thread] = None


class RunManager:
    """Coordinates active test runs, background threads, and event tracking."""

    def __init__(self, reports_root: Optional[Path] = None, max_concurrent: int = 1) -> None:
        if reports_root is None:
            default_dir = Path(os.environ.get("BLINDSPOT_REPORTS_DIR", "blindspot_reports" if Path("blindspot_reports").is_dir() else "reports"))
            self.reports_root = default_dir.resolve()
        else:
            self.reports_root = reports_root.resolve()
        self.max_concurrent = max_concurrent
        self._runs: Dict[str, RunRecord] = {}
        self._lock = threading.Lock()
        self._active_count = 0

    def create_run(self, req: CreateRunRequest) -> RunRecord:
        """Create and queue a new test run record."""
        run_id = generate_run_id()
        if req.output_dir:
            run_dir = Path(req.output_dir).resolve()
        elif req.iteration:
            iter_name = str(req.iteration).strip()
            if not iter_name.startswith("iteration"):
                iter_name = f"iteration_{iter_name}"
            run_dir = (self.reports_root / iter_name).resolve()
        else:
            run_dir = (self.reports_root / run_id).resolve()
        run_dir.mkdir(parents=True, exist_ok=True)

        record = RunRecord(
            run_id=run_id,
            target_url=req.url.strip(),
            context=req.context.strip(),
            created_at=datetime.now(timezone.utc).isoformat(),
            config=req,
            output_dir=run_dir,
            status="queued",
            progress_message="Run created and queued for execution...",
        )

        with self._lock:
            self._runs[run_id] = record

        return record

    def start_run_background(self, run_id: str) -> None:
        """Launch test run in a background daemon thread."""
        with self._lock:
            record = self._runs.get(run_id)
            if not record:
                raise KeyError(f"Run '{run_id}' not found.")

        def worker() -> None:
            record.status = "running"
            record.stage = "inspection"
            record.progress_message = "Starting website inspection..."

            def on_event(event: Dict[str, Any]) -> None:
                with self._lock:
                    record.events.append(event)
                    etype = event.get("type", "")
                    if etype == "stage_start":
                        record.stage = event.get("stage")
                        record.progress_message = event.get("message", f"Starting {record.stage}...")
                    elif etype == "stage_finish":
                        if event.get("stage") == "inspection":
                            rel_shot = event.get("screenshot_path")
                            if rel_shot:
                                record.latest_screenshot = Path(rel_shot).name
                        elif event.get("stage") == "execution":
                            record.metrics["total_tasks"] = event.get("total_tasks", 0)
                            record.metrics["passed_tasks"] = event.get("passed_tasks", 0)
                            record.metrics["failed_tasks"] = event.get("failed_tasks", 0)
                        elif event.get("stage") == "reporting":
                            record.metrics["verified_issues"] = event.get("verified_issues", 0)
                            record.metrics["usability_observations"] = event.get("usability_observations", 0)
                            record.metrics["potential_improvements"] = event.get("potential_improvements", 0)
                    elif etype == "action_step":
                        shot = event.get("screenshot_path")
                        if shot:
                            # Relative filename or relative path
                            record.latest_screenshot = Path(shot).name
                        record.progress_message = f"{event.get('persona_name')}: {event.get('action')} on {event.get('page_url')}"
                    elif etype == "pipeline_error":
                        record.error_message = event.get("error")

            def cancel_check() -> bool:
                return record.cancel_event.is_set()

            pipe_cfg = PipelineConfig(
                url=record.target_url,
                context=record.context,
                output_dir=record.output_dir,
                personas=record.config.personas,
                browser=record.config.browser,
                headless=not record.config.headed,
                max_actions=8,
                ai_provider=record.config.ai_provider,
                ai_model=record.config.ai_model,
            )

            try:
                result = run_pipeline(
                    config=pipe_cfg,
                    on_event=on_event,
                    cancel_check=cancel_check,
                )
                with self._lock:
                    record.result = result
                    if cancel_check():
                        record.status = "cancelled"
                        record.progress_message = "Test execution was cancelled by user."
                    else:
                        record.status = "completed"
                        record.progress_message = "Test run completed successfully."
            except Exception as exc:
                with self._lock:
                    if cancel_check():
                        record.status = "cancelled"
                        record.progress_message = "Test execution was cancelled."
                    else:
                        record.status = "failed"
                        record.error_message = str(exc)
                        record.progress_message = f"Test run failed: {exc}"

        thread = threading.Thread(target=worker, daemon=True)
        record.thread = thread
        thread.start()

    def get_run(self, run_id: str) -> Optional[RunRecord]:
        """Retrieve in-memory record for a run."""
        with self._lock:
            return self._runs.get(run_id)

    def cancel_run(self, run_id: str) -> bool:
        """Signal cancellation for an active run."""
        with self._lock:
            record = self._runs.get(run_id)
            if not record:
                return False
            record.cancel_event.set()
            if record.status in ("queued", "running"):
                record.status = "cancelled"
                record.progress_message = "Cancellation requested..."
            return True

    def list_runs(self) -> List[RunListItem]:
        """List active and historical runs from disk."""
        items: List[RunListItem] = []
        seen_ids = set()

        # 1. Active in-memory runs
        with self._lock:
            for rid, rec in self._runs.items():
                seen_ids.add(rid)
                findings = (
                    rec.metrics.get("verified_issues", 0)
                    + rec.metrics.get("usability_observations", 0)
                    + rec.metrics.get("potential_improvements", 0)
                )
                items.append(
                    RunListItem(
                        run_id=rec.run_id,
                        status=rec.status,
                        target_url=rec.target_url,
                        created_at=rec.created_at,
                        has_report=(rec.output_dir / "report.json").exists(),
                        findings_count=findings,
                        passed_tasks=rec.metrics.get("passed_tasks", 0),
                        total_tasks=rec.metrics.get("total_tasks", 0),
                    )
                )

        # 2. Historical completed runs from reports directory
        if self.reports_root.exists():
            for folder in sorted(self.reports_root.iterdir(), reverse=True):
                if not folder.is_dir() or folder.name in seen_ids:
                    continue
                rep_json = folder / "report.json"
                if rep_json.exists():
                    try:
                        with open(rep_json, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        metrics = data.get("task_metrics", {})
                        findings = len(data.get("findings", []))
                        items.append(
                            RunListItem(
                                run_id=folder.name,
                                status="completed",
                                target_url=data.get("target_url", "Unknown"),
                                created_at=data.get("execution_timestamp", folder.name),
                                has_report=True,
                                findings_count=findings,
                                passed_tasks=metrics.get("passed_tasks", 0),
                                total_tasks=metrics.get("total_tasks", 0),
                            )
                        )
                    except Exception:
                        pass

        return sorted(items, key=lambda x: x.created_at, reverse=True)

    def resolve_safe_file_path(self, run_id: str, filename: str) -> Optional[Path]:
        """Validate and resolve a file path inside a run directory, preventing path traversal.

        Guarantees:
        - run_id is alphanumeric/dashes/underscores.
        - Resolved path is strictly a descendant of the run directory.
        - File exists and is a regular file.
        """
        if not RUN_ID_REGEX.match(run_id):
            return None

        run_dir = (self.reports_root / run_id).resolve()
        if not run_dir.exists() or not run_dir.is_dir():
            return None

        # Resolve candidate
        candidate = (run_dir / filename).resolve()
        try:
            # Check containment
            if not candidate.is_relative_to(run_dir):
                return None
        except (AttributeError, ValueError):
            if not str(candidate).startswith(str(run_dir)):
                return None

        if not candidate.exists() or not candidate.is_file():
            # If not found directly in run_dir, check in evidence/ subfolders for screenshots
            if not filename.startswith("evidence/"):
                for p in run_dir.rglob(filename):
                    if p.is_file():
                        return p.resolve()
            return None

        return candidate


# Singleton instance
job_manager = RunManager()
