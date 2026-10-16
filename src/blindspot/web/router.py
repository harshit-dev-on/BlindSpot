"""FastAPI API endpoints for starting tests, streaming progress, and retrieving reports."""

import asyncio
import json
from pathlib import Path
from typing import List, Optional
from urllib.parse import unquote

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse

from blindspot.core.validation import validate_context, validate_url
from blindspot.execution.safety import validate_navigation_url
from blindspot.web.manager import RUN_ID_REGEX, job_manager
from blindspot.web.models import (
    CancelResponse,
    CreateRunRequest,
    RunListItem,
    RunStatusResponse,
)

api_router = APIRouter(prefix="/api", tags=["BlindSpot Web API"])


@api_router.post(
    "/runs",
    response_model=RunStatusResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start an automated BlindSpot UX test run",
)
def create_and_start_run(payload: CreateRunRequest) -> RunStatusResponse:
    """Validate target URL and start background website testing."""
    # 1. URL syntax validation
    url_res = validate_url(payload.url)
    if not url_res.is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid URL: {url_res.error_message}",
        )

    # 2. SSRF, Localhost, and Private IP Protection
    is_safe, ssrf_err = validate_navigation_url(payload.url)
    if not is_safe:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Security Policy Blocked: {ssrf_err}",
        )

    # 3. Context validation
    ctx_res, _ = validate_context(payload.context)
    if not ctx_res.is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid Context: {ctx_res.error_message}",
        )

    # 4. Create and start background job
    record = job_manager.create_run(payload)
    job_manager.start_run_background(record.run_id)

    return RunStatusResponse(
        run_id=record.run_id,
        status=record.status,
        target_url=record.target_url,
        created_at=record.created_at,
        stage=record.stage,
        progress_message=record.progress_message,
    )


@api_router.get(
    "/runs",
    response_model=List[RunListItem],
    summary="List all active and completed test runs",
)
def list_test_runs() -> List[RunListItem]:
    """Retrieve all available runs with high-level summaries."""
    return job_manager.list_runs()


@api_router.get(
    "/runs/{run_id}",
    response_model=RunStatusResponse,
    summary="Get status and metrics for a specific test run",
)
def get_run_status(run_id: str) -> RunStatusResponse:
    """Check the real-time status, stage, and metrics of a test run."""
    if not RUN_ID_REGEX.match(run_id):
        raise HTTPException(status_code=400, detail="Malformed run ID format.")

    record = job_manager.get_run(run_id)
    if record:
        has_report = (record.output_dir / "report.json").exists()
        has_exec = (record.output_dir / "execution_results.json").exists()
        return RunStatusResponse(
            run_id=record.run_id,
            status=record.status,
            target_url=record.target_url,
            created_at=record.created_at,
            stage=record.stage,
            progress_message=record.progress_message,
            error_message=record.error_message,
            report_id=record.result.report.report_id if (record.result and record.result.report) else None,
            has_report=has_report,
            has_execution=has_exec,
            metrics=record.metrics,
            latest_screenshot=record.latest_screenshot,
        )

    # Check on-disk historical run
    run_dir = job_manager.reports_root / run_id
    if run_dir.exists() and run_dir.is_dir():
        rep_file = run_dir / "report.json"
        if rep_file.exists():
            try:
                with open(rep_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return RunStatusResponse(
                    run_id=run_id,
                    status="completed",
                    target_url=data.get("target_url", "Unknown"),
                    created_at=data.get("execution_timestamp", run_id),
                    stage="reporting",
                    progress_message="Historical run completed.",
                    has_report=True,
                    has_execution=True,
                    report_id=data.get("report_id"),
                    metrics=data.get("task_metrics", {}),
                    latest_screenshot="screenshot.png" if (run_dir / "screenshot.png").exists() else None,
                )
            except Exception:
                pass

    raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")


@api_router.get(
    "/runs/{run_id}/events",
    summary="Stream real-time progress events for a run (SSE or JSON polling)",
)
async def get_run_events(
    run_id: str,
    since: int = Query(default=0, ge=0, description="Event index offset for polling"),
    stream: bool = Query(default=True, description="Stream via Server-Sent Events (SSE)"),
):
    """Subscribe to real-time events or poll recent progress updates."""
    if not RUN_ID_REGEX.match(run_id):
        raise HTTPException(status_code=400, detail="Malformed run ID format.")

    record = job_manager.get_run(run_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Active run '{run_id}' not found.")

    if not stream:
        # Polling mode: return JSON slice of events
        events_slice = record.events[since:]
        return JSONResponse(content={
            "run_id": run_id,
            "status": record.status,
            "latest_index": len(record.events),
            "events": events_slice,
        })

    # SSE streaming mode
    async def event_generator():
        cursor = since
        while True:
            current_events = record.events[cursor:]
            for evt in current_events:
                yield f"data: {json.dumps(evt)}\n\n"
                cursor += 1

            if record.status in ("completed", "failed", "cancelled"):
                # Final notification event
                yield f"data: {json.dumps({'type': 'stream_end', 'status': record.status})}\n\n"
                break

            await asyncio.sleep(0.5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@api_router.get(
    "/runs/{run_id}/results",
    summary="Retrieve completed UX analysis report in machine-readable JSON format",
)
def get_run_results(run_id: str):
    """Retrieve full structured report JSON."""
    if not RUN_ID_REGEX.match(run_id):
        raise HTTPException(status_code=400, detail="Malformed run ID format.")

    safe_file = job_manager.resolve_safe_file_path(run_id, "report.json")
    if not safe_file:
        raise HTTPException(
            status_code=404,
            detail=f"Report results for '{run_id}' not ready or not found.",
        )

    try:
        with open(safe_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return JSONResponse(content=data)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to read report: {exc}")


@api_router.get(
    "/runs/{run_id}/reports/{filename:path}",
    summary="Safely view or download run artifacts (HTML reports, screenshots, JSON)",
)
def serve_report_file(run_id: str, filename: str):
    """Serve run artifacts while strictly defending against path traversal."""
    if not RUN_ID_REGEX.match(run_id):
        raise HTTPException(status_code=400, detail="Malformed run ID format.")

    decoded_filename = unquote(filename)
    if ".." in decoded_filename or decoded_filename.startswith(("/", "\\")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Path traversal characters detected.",
        )

    safe_file = job_manager.resolve_safe_file_path(run_id, decoded_filename)
    if not safe_file:
        raise HTTPException(
            status_code=404,
            detail=f"File '{filename}' not found for run '{run_id}'.",
        )

    media_type = "application/octet-stream"
    suffix = safe_file.suffix.lower()
    if suffix == ".html":
        media_type = "text/html; charset=utf-8"
    elif suffix == ".json":
        media_type = "application/json"
    elif suffix in (".png", ".jpg", ".jpeg"):
        media_type = "image/png" if suffix == ".png" else "image/jpeg"
    elif suffix == ".txt":
        media_type = "text/plain; charset=utf-8"

    return FileResponse(
        path=safe_file,
        media_type=media_type,
        headers={"X-Content-Type-Options": "nosniff"},
    )


@api_router.post(
    "/runs/{run_id}/cancel",
    response_model=CancelResponse,
    summary="Cancel an active test run",
)
def cancel_active_run(run_id: str) -> CancelResponse:
    """Abort an in-progress test run gracefully."""
    if not RUN_ID_REGEX.match(run_id):
        raise HTTPException(status_code=400, detail="Malformed run ID format.")

    ok = job_manager.cancel_run(run_id)
    if not ok:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found to cancel.")

    return CancelResponse(
        run_id=run_id,
        status="cancelling",
        message="Cancellation signal sent to test runner.",
    )
