"""Request and response models for the BlindSpot web demonstration API."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CreateRunRequest(BaseModel):
    """Payload to trigger an automated BlindSpot testing run."""

    url: str = Field(..., description="Target website URL to inspect and test.")
    context: str = Field(..., description="Contextual description of the website purpose and audience.")
    personas: int = Field(default=3, ge=1, le=5, description="Number of synthetic personas to generate (1-5).")
    headed: bool = Field(default=False, description="Run browser in visible window for live demonstration.")
    browser: str = Field(default="chromium", description="Browser engine: chromium, firefox, or webkit.")
    ai_provider: Optional[str] = Field(default=None, description="Optional override for AI provider.")
    ai_model: Optional[str] = Field(default=None, description="Optional override for AI model identifier.")
    output_dir: Optional[str] = Field(default=None, description="Optional custom directory for artifacts.")
    iteration: Optional[str] = Field(default=None, description="Optional iteration name or number (e.g. 'iteration_1').")


class RunStatusResponse(BaseModel):
    """Detailed status and current progress for a specific test run."""

    run_id: str
    status: str  # queued, running, completed, failed, cancelled
    target_url: str
    created_at: str
    stage: Optional[str] = None
    progress_message: Optional[str] = None
    error_message: Optional[str] = None
    report_id: Optional[str] = None
    has_report: bool = False
    has_execution: bool = False
    metrics: Optional[Dict[str, Any]] = None
    latest_screenshot: Optional[str] = None


class RunListItem(BaseModel):
    """Brief summary item for listing past and active test runs."""

    run_id: str
    status: str
    target_url: str
    created_at: str
    has_report: bool = False
    findings_count: int = 0
    passed_tasks: int = 0
    total_tasks: int = 0


class CancelResponse(BaseModel):
    """Response confirming test cancellation."""

    run_id: str
    status: str
    message: str
