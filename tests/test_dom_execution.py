"""Unit and integration tests for DOM HTML, CSS styling, element refs, and zero screenshot tokens."""

from pathlib import Path
from unittest.mock import MagicMock
import pytest
from playwright.sync_api import sync_playwright

from blindspot.ai.base import BaseAIProvider
from blindspot.execution.agent import (
    EXTRACT_DOM_SNAPSHOT_JS,
    PersonaTaskAgent,
    build_agent_step_prompt,
    build_agent_system_prompt,
)
from blindspot.execution.models import (
    ActionType,
    AgentAction,
    TaskStatus,
)
from blindspot.personas.models import Persona, PersonaTask


@pytest.fixture
def interactive_html_page(tmp_path: Path) -> str:
    """Create a local test HTML page with distinct interactive elements."""
    html_content = """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>DOM Test Portal</title>
  <style>
    body { font-family: sans-serif; padding: 40px; }
    .btn { padding: 10px 20px; font-size: 14px; cursor: pointer; }
    #target-btn { background: #3b82f6; color: white; border: none; }
    #text-box { padding: 8px; font-size: 14px; width: 250px; }
    #status { margin-top: 20px; font-weight: bold; color: #10b981; }
  </style>
</head>
<body>
  <h1>Interactive Portal</h1>
  <div>
    <input type="text" id="text-box" placeholder="Enter keywords..." />
  </div>
  <div style="margin-top: 20px;">
    <button id="target-btn" class="btn" onclick="document.getElementById('status').innerText='Button Clicked Successfully!'">
      Submit Action
    </button>
  </div>
  <div id="status">Ready</div>
</body>
</html>"""
    file_path = tmp_path / "dom_portal.html"
    file_path.write_text(html_content, encoding="utf-8")
    return file_path.as_uri()


def test_dom_prompt_contains_dom_html_and_css():
    """Verify prompt incorporates DOM HTML structure, CSS styling, and interactive element refs."""
    task = PersonaTask(
        id="t_dom",
        objective="Locate and activate Submit Action",
        starting_conditions="On portal page",
        success_criteria=["Button Clicked Successfully!"],
        evidence_to_collect=["Confirmation message"],
    )
    persona = Persona(
        id="p_dom",
        name="DOM Tester",
        description="Testing DOM & CSS interaction",
        experience_level="Expert",
        goals=["Test click precision"],
        likely_difficulties=[],
        tasks=[task],
    )

    elements = [
        {
            "ref": "@e1",
            "index": 1,
            "element_type": "input",
            "tag": "input",
            "id": "text-box",
            "placeholder": "Enter keywords...",
            "css": "font: 14px; color: rgb(0, 0, 0)",
        },
        {
            "ref": "@e2",
            "index": 2,
            "element_type": "button",
            "tag": "button",
            "id": "target-btn",
            "text": "Submit Action",
            "css": "bg: rgb(59, 130, 246); color: rgb(255, 255, 255); cursor: pointer",
        },
    ]

    dom_html = "<main><div><input id='text-box'><button id='target-btn'>Submit Action</button></div></main>"

    prompt = build_agent_step_prompt(
        persona=persona,
        task=task,
        page_url="https://example.com",
        page_title="DOM Test Portal",
        elements=elements,
        dom_html=dom_html,
        page_text="Ready",
        history=[],
    )

    # Must contain Persona and Task context
    assert "DOM Tester" in prompt
    assert "Button Clicked Successfully!" in prompt
    # Must contain DOM HTML & CSS styles
    assert "DOM HTML Structure:" in prompt
    assert "Submit Action" in prompt
    assert "@e1 <input>" in prompt
    assert "@e2 <button>" in prompt
    assert "[css: bg: rgb(59, 130, 246)" in prompt


def test_dom_snapshot_js_extraction(interactive_html_page: str):
    """Verify EXTRACT_DOM_SNAPSHOT_JS extracts elements with refs, computed CSS properties, and DOM HTML."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        page.goto(interactive_html_page)

        snapshot = page.evaluate(EXTRACT_DOM_SNAPSHOT_JS)
        assert isinstance(snapshot, dict)
        assert "elements" in snapshot
        assert "dom_html" in snapshot

        elements = snapshot["elements"]
        assert len(elements) >= 2

        # Check element refs and attributes
        first_el = elements[0]
        assert "ref" in first_el and first_el["ref"].startswith("@e")
        assert "tag" in first_el
        assert "css" in first_el
        assert "bounding_box" in first_el

        # Verify dom_html contains semantic content
        assert "Interactive Portal" in snapshot["dom_html"]
        assert "target-btn" in snapshot["dom_html"]

        browser.close()


def test_agent_click_via_element_ref(interactive_html_page: str, tmp_path: Path, monkeypatch):
    """Verify agent clicks an element using only its @eN ref resolved from the DOM snapshot."""
    monkeypatch.setattr(
        "blindspot.execution.agent.validate_navigation_url",
        lambda url, **kw: (True, None),
    )

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        page.goto(interactive_html_page)

        snapshot = page.evaluate(EXTRACT_DOM_SNAPSHOT_JS)
        elements = snapshot["elements"]

        # Identify which ref corresponds to the button
        btn_ref = None
        for el in elements:
            if el.get("tag") == "button":
                btn_ref = el["ref"]
                break

        assert btn_ref is not None, "Button ref not found in elements!"

        mock_provider = MagicMock(spec=BaseAIProvider)
        agent = PersonaTaskAgent(provider=mock_provider)

        # Dispatch click via @eN ref
        action = AgentAction(
            action=ActionType.CLICK,
            target=btn_ref,
            reasoning="Click button by element ref.",
        )
        ok, err = agent._dispatch_action(page, action, elements=elements)
        assert ok is True
        assert err is None

        # Verify button's onclick was executed
        status_text = page.inner_text("#status")
        assert "Button Clicked Successfully!" in status_text

        browser.close()


def test_agent_fill_via_element_ref(interactive_html_page: str, monkeypatch):
    """Verify agent fills an input using its @eN ref resolved from the DOM snapshot."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        page.goto(interactive_html_page)

        snapshot = page.evaluate(EXTRACT_DOM_SNAPSHOT_JS)
        elements = snapshot["elements"]

        input_ref = None
        for el in elements:
            if el.get("tag") == "input":
                input_ref = el["ref"]
                break

        assert input_ref is not None

        mock_provider = MagicMock(spec=BaseAIProvider)
        agent = PersonaTaskAgent(provider=mock_provider)

        action = AgentAction(
            action=ActionType.FILL,
            target=input_ref,
            value="Autonomous DOM Typing",
            reasoning="Fill field via element ref.",
        )
        ok, err = agent._dispatch_action(page, action, elements=elements)
        assert ok is True
        assert err is None

        current_val = page.input_value("#text-box")
        assert current_val == "Autonomous DOM Typing"

        browser.close()


def test_execution_loop_sends_zero_screenshot_tokens(interactive_html_page: str, tmp_path: Path, monkeypatch):
    """Verify that during task execution, generate_structured is called with image_b64=None."""
    monkeypatch.setattr(
        "blindspot.execution.agent.validate_navigation_url",
        lambda url, **kw: (True, None),
    )

    task = PersonaTask(
        id="t_tokens",
        objective="Verify button click",
        starting_conditions="On page",
        success_criteria=["Button Clicked Successfully!"],
        evidence_to_collect=["Confirmation"],
    )
    persona = Persona(
        id="p_tokens",
        name="Token Saver",
        description="Testing token consumption",
        experience_level="Intermediate",
        goals=["Save tokens"],
        likely_difficulties=[],
        tasks=[task],
    )

    mock_provider = MagicMock(spec=BaseAIProvider)
    mock_provider.generate_structured.side_effect = [
        AgentAction(
            action=ActionType.CLICK,
            target="#target-btn",
            reasoning="Click button using CSS selector.",
        )
    ]

    agent = PersonaTaskAgent(provider=mock_provider, max_actions=2)
    evidence_dir = tmp_path / "token_evidence"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})

        result = agent.execute_task(
            page=page,
            persona=persona,
            task=task,
            evidence_dir=evidence_dir,
            initial_url=interactive_html_page,
        )

        browser.close()

    assert result.status == TaskStatus.SUCCESS
    # Ensure provider was called with image_b64=None
    call_kwargs = mock_provider.generate_structured.call_args.kwargs
    assert call_kwargs.get("image_b64") is None, "Expected image_b64=None to prevent token exhaustion!"


def test_top_status_navbar_and_page_offset(interactive_html_page: str):
    """Verify live status navbar renders at the top, page is shifted down 40px, and floating HUD is eliminated."""
    mock_provider = MagicMock(spec=BaseAIProvider)
    agent = PersonaTaskAgent(provider=mock_provider, headless=False)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        page.goto(interactive_html_page, wait_until="domcontentloaded")

        # Simulate legacy floating HUD element present
        page.evaluate("""() => {
            const legacyHud = document.createElement('div');
            legacyHud.id = '__blindspot_live_hud';
            legacyHud.innerText = 'Floating text telling blind spot is running';
            document.body.appendChild(legacyHud);
        }""")
        assert page.locator("#__blindspot_live_hud").count() == 1

        # Render top navbar
        agent._update_live_navbar(
            page=page,
            persona_name="Sarah Jenkins",
            experience_level="Novice",
            task_objective="Test navbar appearance",
            step_num=1,
            max_steps=5,
            action_text="Action: click @e1",
            thought="Looking for button",
        )

        # 1. Floating HUD removed
        assert page.locator("#__blindspot_live_hud").count() == 0, "Floating HUD was not removed!"

        # 2. Navbar present at top
        navbar = page.locator("#__blindspot_navbar")
        assert navbar.count() == 1
        navbar_text = navbar.inner_text()
        assert "BLINDSPOT" in navbar_text
        assert "Sarah Jenkins" in navbar_text
        assert "STEP 1/5" in navbar_text.upper()

        # 3. Document shifted down 40px
        margin_top = page.evaluate("() => document.documentElement.style.marginTop")
        assert margin_top == "40px"

        # 4. DOM snapshot ignores navbar and overlay
        snapshot = page.evaluate(EXTRACT_DOM_SNAPSHOT_JS)
        element_ids = [el.get("id") for el in snapshot.get("elements", [])]
        assert "__blindspot_navbar" not in element_ids
        assert "__blindspot_live_hud" not in element_ids
        assert "__blindspot_overlay" not in element_ids

        # 5. Click navbar toggles blurry info overlay open
        overlay = page.locator("#__blindspot_overlay")
        assert overlay.count() == 1
        assert not overlay.is_visible()

        # Click to open info mode
        navbar.click()
        assert overlay.is_visible()
        card_text = page.locator("#__blindspot_info_card").inner_text()
        assert "Sarah Jenkins" in card_text
        assert "Test navbar appearance" in card_text
        assert "Action: click @e1" in card_text
        assert "Looking for button" in card_text

        # Click navbar again to close info mode
        navbar.click()
        assert not overlay.is_visible()

        # Click to re-open and test close button
        navbar.click()
        assert overlay.is_visible()
        page.locator("#__blindspot_close_btn").click()
        assert not overlay.is_visible()

        browser.close()


def test_scroll_test_navbar_and_overlay_toggle(interactive_html_page: str):
    """Verify scroll test navbar renders correctly, page shifts down 40px, and clicking toggles info mode."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        page.goto(interactive_html_page, wait_until="domcontentloaded")

        # Inject scroll_test navbar script
        navbar_js = f"""
        (() => {{
            const oldHud1 = document.getElementById('__blindspot_test_hud');
            if (oldHud1) oldHud1.remove();
            const oldHud2 = document.getElementById('__blindspot_live_hud');
            if (oldHud2) oldHud2.remove();

            document.documentElement.style.setProperty('margin-top', '40px', 'important');

            let bar = document.getElementById('__blindspot_navbar');
            if (!bar) {{
                bar = document.createElement('div');
                bar.id = '__blindspot_navbar';
                bar.style.cssText = 'position: fixed; top: 0; left: 0; right: 0; width: 100%; height: 40px; z-index: 2147483647; background: #090d16; color: #f8fafc; cursor: pointer; display: flex; align-items: center; justify-content: space-between; padding: 0 16px;';
                document.documentElement.appendChild(bar);
            }}

            let overlay = document.getElementById('__blindspot_overlay');
            if (!overlay) {{
                overlay = document.createElement('div');
                overlay.id = '__blindspot_overlay';
                overlay.style.cssText = 'position: fixed; top: 40px; left: 0; right: 0; bottom: 0; width: 100%; height: calc(100vh - 40px); z-index: 2147483646; background: rgba(9, 13, 22, 0.76); backdrop-filter: blur(12px); display: none; justify-content: center; align-items: flex-start; padding: 30px 20px;';
                overlay.innerHTML = '<div id="__blindspot_info_card"><h3>BlindSpot Engine Telemetry</h3><button id="__blindspot_close_btn">✕ Close</button></div>';
                document.documentElement.appendChild(overlay);

                const closeBtn = document.getElementById('__blindspot_close_btn');
                if (closeBtn) {{
                    closeBtn.onclick = (e) => {{
                        e.stopPropagation();
                        overlay.style.display = 'none';
                    }};
                }}
            }}

            bar.onclick = () => {{
                const ov = document.getElementById('__blindspot_overlay');
                if (!ov) return;
                const isHidden = ov.style.display === 'none' || !ov.style.display;
                ov.style.display = isHidden ? 'flex' : 'none';
            }};

            bar.innerHTML = '<span>BLINDSPOT</span><span id="__blindspot_nav_msg">Live scroll active</span>';
        }})();
        """
        page.evaluate(navbar_js)

        # 1. Navbar present
        navbar = page.locator("#__blindspot_navbar")
        assert navbar.count() == 1
        assert "BLINDSPOT" in navbar.inner_text()

        # 2. Shift margin-top 40px
        margin_top = page.evaluate("() => document.documentElement.style.marginTop")
        assert margin_top == "40px"

        # 3. Overlay toggle on click
        overlay = page.locator("#__blindspot_overlay")
        assert not overlay.is_visible()

        navbar.click()
        assert overlay.is_visible()
        assert "BlindSpot Engine Telemetry" in page.locator("#__blindspot_info_card").inner_text()

        navbar.click()
        assert not overlay.is_visible()

        browser.close()


def test_overlay_renders_extracted_dom_elements_and_html(interactive_html_page: str):
    """Verify that _update_live_navbar correctly populates elements table and semantic DOM HTML tree."""
    mock_provider = MagicMock(spec=BaseAIProvider)
    agent = PersonaTaskAgent(provider=mock_provider, headless=False, max_actions=5)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        page.goto(interactive_html_page, wait_until="domcontentloaded")

        # Extract DOM snapshot from interactive page
        snapshot = page.evaluate(EXTRACT_DOM_SNAPSHOT_JS)
        elements = snapshot.get("elements", [])
        dom_html = snapshot.get("dom_html", "")

        assert len(elements) > 0, "No interactive elements extracted from test page"
        assert len(dom_html) > 0, "No DOM HTML extracted from test page"

        # Update navbar with extracted DOM
        agent._update_live_navbar(
            page=page,
            persona_name="Alex Chen",
            experience_level="Expert",
            task_objective="Find and click checkout button",
            step_num=2,
            max_steps=5,
            action_text="click @e1",
            thought="Found prime checkout target",
            elements=elements,
            dom_html=dom_html,
        )

        navbar = page.locator("#__blindspot_navbar")
        overlay = page.locator("#__blindspot_overlay")

        # Open overlay
        navbar.click()
        assert overlay.is_visible()

        # Verify elements panel is visible and displays extracted elements
        panel_elements = page.locator("#__blindspot_panel_elements")
        assert panel_elements.is_visible()
        rows = page.locator(".__blindspot_elem_row")
        assert rows.count() == len(elements)

        # First element row contains @e1
        first_row_text = rows.nth(0).inner_text()
        assert "@e1" in first_row_text

        # Verify Tab 2 (Semantic DOM HTML)
        tab_dom = page.locator("#__blindspot_tab_dom")
        tab_dom.click()
        panel_dom = page.locator("#__blindspot_panel_dom")
        assert panel_dom.is_visible()
        dom_code_text = page.locator("#__blindspot_dom_code").inner_text()
        assert len(dom_code_text) > 0

        # Verify Tab 3 (Telemetry & Architecture)
        tab_telem = page.locator("#__blindspot_tab_telemetry")
        tab_telem.click()
        panel_telem = page.locator("#__blindspot_panel_telemetry")
        assert panel_telem.is_visible()

        # Switch back to elements tab
        page.locator("#__blindspot_tab_elements").click()
        assert panel_elements.is_visible()

        # Verify search filtering works
        search_input = page.locator("#__blindspot_elem_search")
        search_input.fill("@e1")
        visible_rows = page.evaluate("""() => {
            const rows = Array.from(document.querySelectorAll('.__blindspot_elem_row'));
            return rows.filter(r => r.style.display !== 'none').length;
        }""")
        assert visible_rows >= 1

        browser.close()

