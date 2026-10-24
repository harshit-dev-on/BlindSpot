"""Unit tests for BlindSpot Agent Tools suite."""

import pytest
from blindspot.tools import (
    BrowserActionTool,
    JourneyTodoTool,
    RecordAccessibilityBarrierTool,
    RecordUXFrictionTool,
    SessionNotesTool,
    TodoStatus,
    UsabilityHeuristic,
    UserThoughtTool,
)


def test_user_thought_tool():
    tool = UserThoughtTool()
    schema = tool.get_parameters_schema()
    assert "persona_name" in schema["properties"]
    assert "frustration_level" in schema["properties"]

    res = tool.execute(
        persona_name="Sam Senior",
        observation="The button is very small and low contrast",
        expectation="I expected large clear text",
        frustration_level=7,
        confusion_points=["Tiny gray text on white"],
    )
    assert res.success is True
    assert "Sam Senior" in res.output
    assert "Frustration: 7/10" in res.output
    assert len(tool.thought_history) == 1
    assert tool.thought_history[0].frustration_level == 7


def test_record_ux_friction_tool():
    tool = RecordUXFrictionTool()
    res = tool.execute(
        title="No loading indicator on checkout",
        description="User clicked submit but screen did not update for 3 seconds",
        heuristic="1. Visibility of system status",
        severity="critical",
        element_selector="#btn-submit",
        page_url="https://example.com/checkout",
        remediation_suggestion="Add spinner animation on button click",
    )
    assert res.success is True
    assert "UX-001" in res.output
    assert len(tool.friction_records) == 1
    rec = tool.friction_records[0]
    assert rec.heuristic == UsabilityHeuristic.VISIBILITY_OF_STATUS
    assert rec.severity == "critical"


def test_record_accessibility_barrier_tool():
    tool = RecordAccessibilityBarrierTool()
    res = tool.execute(
        wcag_criterion="1.4.3",
        impact="serious",
        element_selector="button.cta-ghost",
        html_snippet="<button class='cta-ghost'>Learn More</button>",
        failure_summary="Text contrast ratio 2.8:1 is below the required 4.5:1 minimum",
        suggested_fix="Change text color to #1a202c",
        page_url="https://example.com",
    )
    assert res.success is True
    assert "A11Y-001" in res.output
    assert len(tool.barriers) == 1

    # Test SARIF conversion
    sarif_item = tool.barriers[0].to_sarif_result()
    assert sarif_item["ruleId"] == "WCAG-1.4.3"
    assert sarif_item["level"] == "error"
    assert sarif_item["properties"]["elementSelector"] == "button.cta-ghost"


def test_journey_todo_tool():
    tool = JourneyTodoTool()

    # Add items
    r1 = tool.execute(action="add", description="Locate pricing table")
    assert r1.success is True
    assert "TODO-1" in r1.output

    r2 = tool.execute(action="add", description="Select Enterprise plan")
    assert r2.success is True
    assert "TODO-2" in r2.output

    # Complete item
    r3 = tool.execute(action="complete", item_id="TODO-1", notes="Found at #pricing")
    assert r3.success is True
    assert tool.todos["TODO-1"].status == TodoStatus.COMPLETED

    # Block item
    r4 = tool.execute(action="block", item_id="TODO-2", notes="Enterprise button is disabled")
    assert r4.success is True
    assert tool.todos["TODO-2"].status == TodoStatus.BLOCKED

    # List items
    r5 = tool.execute(action="list")
    assert "[X] TODO-1" in r5.output
    assert "[!] TODO-2" in r5.output


def test_session_notes_tool():
    tool = SessionNotesTool()

    # Set note
    r1 = tool.execute(action="set", key="test_email", value="user123@test.com")
    assert r1.success is True
    assert tool.notes["test_email"] == "user123@test.com"

    # Get note
    r2 = tool.execute(action="get", key="test_email")
    assert r2.success is True
    assert r2.data["value"] == "user123@test.com"

    # List notes
    r3 = tool.execute(action="list")
    assert "test_email: user123@test.com" in r3.output

    # Delete note
    r4 = tool.execute(action="delete", key="test_email")
    assert r4.success is True
    assert "test_email" not in tool.notes


def test_browser_action_tool_simulated():
    tool = BrowserActionTool(page=None)
    res = tool.execute(action="click", selector="#btn-login")
    assert res.success is True
    assert res.data["simulated"] is True
    assert res.data["action"] == "click"

    # Test OpenAI function calling schema export
    schema = tool.to_openai_tool()
    assert schema["type"] == "function"
    assert schema["function"]["name"] == "browser_act"
