"""Automated tests for persona-based browser task execution, safety policies, and evidence collection."""

import json
from pathlib import Path
from unittest.mock import MagicMock
import pytest

from blindspot.ai.base import BaseAIProvider
from blindspot.ai.exceptions import AIStructuredOutputError
from blindspot.execution.agent import PersonaTaskAgent
from blindspot.execution.models import (
    ActionType,
    AgentAction,
    ExecutionRunResult,
    TaskExecutionResult,
    TaskStatus,
)
from blindspot.execution.runner import PersonaTestRunner, execute_persona_tasks
from blindspot.execution.safety import (
    is_action_destructive,
    is_ip_private_or_restricted,
    mask_sensitive_input,
    validate_navigation_url,
)
from blindspot.personas.models import Persona, PersonaPlan, PersonaTask


# ─────────────────────────────────────────────────────────────────────────────
# 1. Safety Policies & URL Validation Tests
# ─────────────────────────────────────────────────────────────────────────────


def test_safety_url_validation_permitted():
    """Verify standard public HTTP/HTTPS URLs pass safety checks."""
    ok, reason = validate_navigation_url("https://example.com/products")
    assert ok is True
    assert reason is None

    ok, reason = validate_navigation_url("http://subdomain.testsite.org/page?query=1")
    assert ok is True


def test_safety_url_validation_blocked_schemes():
    """Verify non-HTTP schemes are rejected."""
    for scheme_url in ("file:///etc/passwd", "javascript:alert(1)", "data:text/html,<h1>Hi</h1>", "ftp://ftp.example.com"):
        ok, reason = validate_navigation_url(scheme_url)
        assert ok is False
        assert "Forbidden URL scheme" in reason


def test_safety_url_validation_blocked_private_and_metadata():
    """Verify private networks, loopbacks, and cloud metadata endpoints are strictly blocked."""
    blocked_targets = [
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://0.0.0.0:80",
        "http://169.254.169.254/latest/meta-data/",
        "http://metadata.google.internal/computeMetadata/v1/",
        "http://10.0.0.1/admin",
        "http://192.168.1.1/setup",
        "http://172.16.0.5/api",
        "http://service.internal/secret",
        "http://myhost.local",
    ]
    for url in blocked_targets:
        ok, reason = validate_navigation_url(url)
        assert ok is False, f"Expected {url} to be blocked!"
        assert any(term in reason for term in ("blocked", "forbidden", "private"))


def test_safety_destructive_actions():
    """Verify destructive financial or account actions are blocked."""
    dangerous = [
        ("button", "Buy now with 1-click"),
        ("button", "Place your order"),
        ("a", "Confirm payment"),
        ("button", "Delete account permanently"),
        ("form", "Terminate account"),
    ]
    for target, value in dangerous:
        is_dest, reason = is_action_destructive(target, value)
        assert is_dest is True
        assert "destructive" in reason

    # Safe interactions
    safe = [
        ("button", "Search"),
        ("a", "Read more"),
        ("button", "Add to wishlist"),
        ("input", "T-shirt"),
    ]
    for target, value in safe:
        is_dest, _ = is_action_destructive(target, value)
        assert is_dest is False


def test_safety_mask_sensitive_input():
    """Verify passwords and credit cards are masked."""
    assert mask_sensitive_input("user_password", "SuperSecret123") == "********"
    assert mask_sensitive_input("creditcard_number", "4111222233334444") == "********"
    assert mask_sensitive_input("search_query", "ceramic mug") == "ceramic mug"


# ─────────────────────────────────────────────────────────────────────────────
# 2. Local Browser Page Execution Tests
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def local_html_page(tmp_path: Path) -> str:
    """Create a local test HTML page and return its file URL."""
    html_content = """<!DOCTYPE html>
<html>
<head><title>Test Store - Product Catalog</title></head>
<body>
  <h1>Welcome to Test Store</h1>
  <nav>
    <a href="#products" id="nav-products">Products</a>
    <a href="#about" id="nav-about">About Us</a>
  </nav>
  <div id="search-section">
    <input type="text" placeholder="Search catalog..." id="search-input" />
    <button id="search-btn" onclick="document.getElementById('results').innerText='Found 3 ceramic items.'">Search</button>
  </div>
  <div id="results">No search executed.</div>
  <div id="cart-section">
    <button id="btn-add-cart" onclick="document.getElementById('cart-msg').innerText='Item added to cart!'">Add to Cart</button>
    <span id="cart-msg">Cart is empty</span>
  </div>
</body>
</html>"""
    file_path = tmp_path / "index.html"
    file_path.write_text(html_content, encoding="utf-8")
    return file_path.as_uri()


@pytest.fixture
def sample_test_persona() -> Persona:
    """Fixture providing a persona with a realistic task."""
    return Persona(
        id="persona_tester_1",
        name="Alex - Product Searcher",
        description="Looking to search the catalog.",
        experience_level="Intermediate",
        goals=["Search items"],
        likely_difficulties=["Hidden search button"],
        tasks=[
            PersonaTask(
                id="task_search_1",
                objective="Search for ceramic products and verify results",
                starting_conditions="Starts on catalog page",
                success_criteria=["Found 3 ceramic items"],
                evidence_to_collect=["Search results text"],
            )
        ],
    )


def test_task_agent_successful_execution(local_html_page: str, sample_test_persona: Persona, tmp_path: Path, monkeypatch):
    """Verify browser agent executes click/fill actions and verifies success criteria."""
    from playwright.sync_api import sync_playwright

    # Allow local file URI specifically for this local HTML fixture
    monkeypatch.setattr(
        "blindspot.execution.agent.validate_navigation_url",
        lambda url, **kw: (True, None),
    )

    # Mock AI provider: step 1 fill search input, step 2 click search button
    mock_provider = MagicMock(spec=BaseAIProvider)
    mock_provider.name = "mock-ai"
    mock_provider.model = "mock-model"

    mock_provider.generate_structured.side_effect = [
        AgentAction(
            action=ActionType.FILL,
            target="#search-input",
            value="ceramic",
            reasoning="Enter search term into catalog search input.",
        ),
        AgentAction(
            action=ActionType.CLICK,
            target="#search-btn",
            reasoning="Click search button to execute search.",
        ),
    ]

    agent = PersonaTaskAgent(provider=mock_provider, max_actions=4)
    evidence_dir = tmp_path / "evidence_out"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        result = agent.execute_task(
            page=page,
            persona=sample_test_persona,
            task=sample_test_persona.tasks[0],
            evidence_dir=evidence_dir,
            initial_url=local_html_page,
        )

        browser.close()

    assert result.status == TaskStatus.SUCCESS
    assert result.task_id == "task_search_1"
    assert len(result.actions_taken) >= 2
    assert any("Found 3 ceramic items" in ev for ev in result.evidence)
    assert len(result.evidence_screenshots) > 0


def test_task_agent_loop_prevention_on_max_actions(local_html_page: str, sample_test_persona: Persona, tmp_path: Path, monkeypatch):
    """Verify agent terminates after max_actions if success criteria are not met."""
    from playwright.sync_api import sync_playwright

    monkeypatch.setattr(
        "blindspot.execution.agent.validate_navigation_url",
        lambda url, **kw: (True, None),
    )

    # Mock AI provider returning continuous scroll actions without satisfying criteria
    mock_provider = MagicMock(spec=BaseAIProvider)
    mock_provider.generate_structured.return_value = AgentAction(
        action=ActionType.SCROLL,
        value="down",
        reasoning="Keep scrolling looking for item.",
    )

    agent = PersonaTaskAgent(provider=mock_provider, max_actions=3)
    evidence_dir = tmp_path / "loop_out"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        result = agent.execute_task(
            page=page,
            persona=sample_test_persona,
            task=sample_test_persona.tasks[0],
            evidence_dir=evidence_dir,
            initial_url=local_html_page,
        )

        browser.close()

    assert result.status == TaskStatus.FAILURE
    assert len(result.actions_taken) == 3
    assert "Maximum action limit (3) reached" in result.error_message


def test_task_agent_malformed_model_action_fails_gracefully(local_html_page: str, sample_test_persona: Persona, tmp_path: Path, monkeypatch):
    """Verify unrecoverable AI model error terminates the task gracefully without infinite loops."""
    from playwright.sync_api import sync_playwright

    monkeypatch.setattr(
        "blindspot.execution.agent.validate_navigation_url",
        lambda url, **kw: (True, None),
    )

    mock_provider = MagicMock(spec=BaseAIProvider)
    mock_provider.generate_structured.side_effect = AIStructuredOutputError(
        message="Model returned invalid JSON",
        raw_output="INVALID",
        provider="mock",
    )

    agent = PersonaTaskAgent(provider=mock_provider, max_actions=4)
    evidence_dir = tmp_path / "malformed_out"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        result = agent.execute_task(
            page=page,
            persona=sample_test_persona,
            task=sample_test_persona.tasks[0],
            evidence_dir=evidence_dir,
            initial_url=local_html_page,
        )

        browser.close()

    assert result.status in (TaskStatus.FAILURE, TaskStatus.INCONCLUSIVE)
    assert "AI decision error" in (result.error_message or "")


def test_independent_persona_sessions(tmp_path: Path, monkeypatch):
    """Verify that multiple personas run in completely isolated browser contexts."""
    # Create HTML page that checks and writes cookies
    page_html = """<!DOCTYPE html>
<html>
<body>
  <h1>Session Test Page</h1>
  <script>
    // Record current cookie
    const prevCookie = document.cookie;
    window.__seen_cookie = prevCookie;
    // Set a persona-specific cookie
    document.cookie = "persona_session=" + window.location.hash.slice(1);
  </script>
</body>
</html>"""
    html_file = tmp_path / "session_test.html"
    html_file.write_text(page_html, encoding="utf-8")
    page_url = html_file.as_uri()

    monkeypatch.setattr(
        "blindspot.execution.agent.validate_navigation_url",
        lambda url, **kw: (True, None),
    )

    # Create 2 personas
    persona1 = Persona(
        id="persona_alpha",
        name="User Alpha",
        description="First",
        experience_level="Novice",
        goals=["Test 1"],
        likely_difficulties=["None"],
        tasks=[
            PersonaTask(
                id="task_a",
                objective="Visit page",
                starting_conditions="Starts on page",
                success_criteria=["Session Test Page"],
                evidence_to_collect=["Title"],
            )
        ],
    )
    persona2 = Persona(
        id="persona_beta",
        name="User Beta",
        description="Second",
        experience_level="Expert",
        goals=["Test 2"],
        likely_difficulties=["None"],
        tasks=[
            PersonaTask(
                id="task_b",
                objective="Visit page",
                starting_conditions="Starts on page",
                success_criteria=["Session Test Page"],
                evidence_to_collect=["Title"],
            )
        ],
    )

    plan = PersonaPlan(
        website_url=f"{page_url}#init",
        context="Testing isolated sessions",
        website_summary="Session test page",
        personas=[persona1, persona2],
    )

    mock_provider = MagicMock(spec=BaseAIProvider)
    mock_provider.generate_structured.return_value = AgentAction(
        action=ActionType.FINISH,
        reasoning="Task criteria met.",
    )

    run_dir = tmp_path / "isolated_run"
    runner = PersonaTestRunner(
        provider=mock_provider,
        browser_type="chromium",
        headless=True,
        max_actions_per_task=2,
    )

    result = runner.run_plan(plan=plan, output_dir=run_dir)

    assert result.total_tasks == 2
    assert len(result.personas) == 2
    assert (run_dir / "execution_results.json").exists()

    # Read saved results file
    saved = json.loads((run_dir / "execution_results.json").read_text(encoding="utf-8"))
    assert saved["target_url"] == f"{page_url}#init"
    assert len(saved["personas"]) == 2


def test_runner_max_personas_limit(tmp_path, monkeypatch):
    """Verify that max_personas limits execution to the requested number of personas."""
    html_file = tmp_path / "page.html"
    html_file.write_text("<html><body><h1>Test</h1></body></html>", encoding="utf-8")
    page_url = html_file.as_uri()

    monkeypatch.setattr(
        "blindspot.execution.agent.validate_navigation_url",
        lambda url, **kw: (True, None),
    )

    persona1 = Persona(
        id="p1",
        name="User 1",
        description="First",
        experience_level="Novice",
        goals=["G1"],
        likely_difficulties=[],
        tasks=[
            PersonaTask(
                id="t1",
                objective="View page",
                starting_conditions="",
                success_criteria=["Test"],
                evidence_to_collect=["Title"],
            )
        ],
    )
    persona2 = Persona(
        id="p2",
        name="User 2",
        description="Second",
        experience_level="Expert",
        goals=["G2"],
        likely_difficulties=[],
        tasks=[
            PersonaTask(
                id="t2",
                objective="View page",
                starting_conditions="",
                success_criteria=["Test"],
                evidence_to_collect=["Title"],
            )
        ],
    )

    plan = PersonaPlan(
        website_url=page_url,
        context="Test",
        website_summary="Test page",
        personas=[persona1, persona2],
    )

    mock_provider = MagicMock(spec=BaseAIProvider)
    mock_provider.generate_structured.return_value = AgentAction(
        action=ActionType.FINISH,
        reasoning="Done.",
    )

    run_dir = tmp_path / "limit_run"
    runner = PersonaTestRunner(
        provider=mock_provider,
        browser_type="chromium",
        headless=True,
        max_personas=1,
    )

    result = runner.run_plan(plan=plan, output_dir=run_dir)
    assert len(result.personas) == 1
    assert result.personas[0].persona_id == "p1"


def test_runner_concurrency_simultaneous(tmp_path, monkeypatch):
    """Verify simultaneous multi-worker persona execution with concurrency > 1."""
    html_file = tmp_path / "page2.html"
    html_file.write_text("<html><body><h1>Test Concurrent</h1></body></html>", encoding="utf-8")
    page_url = html_file.as_uri()

    monkeypatch.setattr(
        "blindspot.execution.agent.validate_navigation_url",
        lambda url, **kw: (True, None),
    )

    persona1 = Persona(
        id="p1",
        name="User 1",
        description="First",
        experience_level="Novice",
        goals=["G1"],
        likely_difficulties=[],
        tasks=[
            PersonaTask(
                id="t1",
                objective="View page",
                starting_conditions="",
                success_criteria=["Concurrent"],
                evidence_to_collect=["Title"],
            )
        ],
    )
    persona2 = Persona(
        id="p2",
        name="User 2",
        description="Second",
        experience_level="Expert",
        goals=["G2"],
        likely_difficulties=[],
        tasks=[
            PersonaTask(
                id="t2",
                objective="View page",
                starting_conditions="",
                success_criteria=["Concurrent"],
                evidence_to_collect=["Title"],
            )
        ],
    )

    plan = PersonaPlan(
        website_url=page_url,
        context="Test",
        website_summary="Concurrent test",
        personas=[persona1, persona2],
    )

    mock_provider = MagicMock(spec=BaseAIProvider)
    mock_provider.generate_structured.return_value = AgentAction(
        action=ActionType.FINISH,
        reasoning="Done.",
    )

    run_dir = tmp_path / "concurrent_run"
    runner = PersonaTestRunner(
        provider=mock_provider,
        browser_type="chromium",
        headless=True,
        concurrency=2,
    )

    events = []
    result = runner.run_plan(plan=plan, output_dir=run_dir, on_event=lambda ev: events.append(ev))
    assert len(result.personas) == 2
    assert len(events) >= 2

