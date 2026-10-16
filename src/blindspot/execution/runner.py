"""Orchestrator for executing persona tasks in isolated browser contexts."""

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Union

from playwright.sync_api import Error as PlaywrightError, sync_playwright

from blindspot.ai.base import BaseAIProvider
from blindspot.execution.agent import PersonaTaskAgent
from blindspot.execution.models import (
    ExecutionRunResult,
    PersonaExecutionResult,
)
from blindspot.personas.models import PersonaPlan


class PersonaTestRunner:
    """Manages browser execution lifecycle, context isolation, and evidence persistence."""

    def __init__(
        self,
        provider: BaseAIProvider,
        browser_type: str = "chromium",
        headless: bool = True,
        viewport_width: int = 1280,
        viewport_height: int = 800,
        max_actions_per_task: int = 8,
        action_timeout_ms: int = 8000,
    ) -> None:
        self.provider = provider
        self.browser_type = browser_type.lower().strip()
        self.headless = headless
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.max_actions_per_task = max_actions_per_task
        self.action_timeout_ms = action_timeout_ms

    def run_plan(
        self,
        plan: PersonaPlan,
        output_dir: Union[str, Path],
        on_event: Optional[Callable[[Dict[str, Any]], None]] = None,
        cancel_check: Optional[Callable[[], bool]] = None,
    ) -> ExecutionRunResult:
        """Execute tasks for all personas in the plan across isolated browser contexts.

        Args:
            plan: Synthesized PersonaPlan containing personas and assigned tasks.
            output_dir: Directory where execution artifacts, screenshots, and results are stored.
            on_event: Optional callback for progress and action events.
            cancel_check: Optional callable that returns True when task should be cancelled.

        Returns:
            ExecutionRunResult summarizing all persona task outcomes.
        """
        run_dir = Path(output_dir)
        run_dir.mkdir(parents=True, exist_ok=True)
        evidence_base = run_dir / "evidence"
        evidence_base.mkdir(parents=True, exist_ok=True)

        persona_results = []
        agent = PersonaTaskAgent(
            provider=self.provider,
            max_actions=self.max_actions_per_task,
            action_timeout_ms=self.action_timeout_ms,
        )

        with sync_playwright() as p:
            launcher = getattr(p, self.browser_type, None)
            if launcher is None:
                raise ValueError(f"Browser engine '{self.browser_type}' is not supported.")

            try:
                browser = launcher.launch(headless=self.headless)
            except PlaywrightError as exc:
                err_msg = str(exc)
                if "Executable doesn't exist" in err_msg or "Please run" in err_msg:
                    raise RuntimeError(
                        f"Playwright browser '{self.browser_type}' is not installed.\n"
                        f"Run 'playwright install {self.browser_type}' to install it."
                    ) from exc
                raise

            try:
                for persona in plan.personas:
                    if cancel_check and cancel_check():
                        break

                    # 1. Create an independent browser context for session isolation
                    context_obj = browser.new_context(
                        viewport={"width": self.viewport_width, "height": self.viewport_height},
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) BlindSpot-UX-Tester/0.1.0",
                    )
                    page = context_obj.new_page()

                    task_results = []
                    try:
                        for task in persona.tasks:
                            if cancel_check and cancel_check():
                                break

                            if on_event:
                                try:
                                    on_event({
                                        "type": "task_start",
                                        "persona_id": persona.id,
                                        "persona_name": persona.name,
                                        "task_id": task.id,
                                        "task_objective": task.objective,
                                        "timestamp": datetime.now(timezone.utc).isoformat(),
                                    })
                                except Exception:
                                    pass

                            task_evidence_dir = evidence_base / persona.id / task.id
                            result = agent.execute_task(
                                page=page,
                                persona=persona,
                                task=task,
                                evidence_dir=task_evidence_dir,
                                initial_url=plan.website_url,
                                on_step=on_event,
                                cancel_check=cancel_check,
                            )
                            task_results.append(result)

                            if on_event:
                                try:
                                    on_event({
                                        "type": "task_finish",
                                        "persona_id": persona.id,
                                        "persona_name": persona.name,
                                        "task_id": task.id,
                                        "status": result.status.value,
                                        "evidence": result.collected_evidence,
                                        "error": result.error_message,
                                        "timestamp": datetime.now(timezone.utc).isoformat(),
                                    })
                                except Exception:
                                    pass
                    finally:
                        # Close context after persona completes: clears cookies, storage, sessions
                        context_obj.close()

                    persona_results.append(
                        PersonaExecutionResult(
                            persona_id=persona.id,
                            persona_name=persona.name,
                            task_results=task_results,
                        )
                    )

            finally:
                browser.close()

        # Build run result
        run_result = ExecutionRunResult(
            target_url=plan.website_url,
            browser=self.browser_type,
            headless=self.headless,
            personas=persona_results,
        )

        # Save to disk
        results_file = run_dir / "execution_results.json"
        run_result.results_file_path = str(results_file)
        with open(results_file, "w", encoding="utf-8") as f:
            f.write(run_result.model_dump_json(indent=2))

        return run_result


def execute_persona_tasks(
    plan: PersonaPlan,
    provider: BaseAIProvider,
    output_dir: Union[str, Path],
    browser_type: str = "chromium",
    headless: bool = True,
    max_actions_per_task: int = 8,
    on_event: Optional[Callable[[Dict[str, Any]], None]] = None,
    cancel_check: Optional[Callable[[], bool]] = None,
) -> ExecutionRunResult:
    """Convenience functional helper to run persona tasks."""
    runner = PersonaTestRunner(
        provider=provider,
        browser_type=browser_type,
        headless=headless,
        max_actions_per_task=max_actions_per_task,
    )
    return runner.run_plan(
        plan=plan,
        output_dir=output_dir,
        on_event=on_event,
        cancel_check=cancel_check,
    )
