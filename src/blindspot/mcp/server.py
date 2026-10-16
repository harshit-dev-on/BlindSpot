"""Model Context Protocol (MCP) server for BlindSpot AI coding agent integration."""

from typing import Any, Dict, Optional
from mcp.server.mcpserver import MCPServer

from blindspot.mcp.tools import (
    tool_get_findings,
    tool_get_test_results,
    tool_get_test_status,
    tool_inspect_website,
    tool_verify_fixes,
)


def create_mcp_server() -> MCPServer:
    """Build and configure the BlindSpot MCP server with registered inspection tools."""
    server = MCPServer(
        name="blindspot",
        instructions=(
            "BlindSpot is an autonomous website UX and usability testing tool. "
            "It simulates realistic user personas, navigates pages with Playwright, "
            "records interactions and screenshots, and generates evidence-backed UX defect reports. "
            "Use inspect_website to initiate a test run, get_test_status to poll progress, "
            "get_test_results and get_findings to inspect defects, and verify_fixes to verify resolved issues."
        ),
    )

    @server.tool(
        name="inspect_website",
        description=(
            "Start an automated BlindSpot UX testing run on a target website. "
            "Validates URL and SSRF safety, then runs browser inspection, persona generation, "
            "and Playwright task execution. Returns a run_id for status polling."
        ),
    )
    def inspect_website(
        url: str,
        context: str,
        personas: int = 3,
        headed: bool = False,
        wait_for_completion: bool = False,
    ) -> Dict[str, Any]:
        """Start a website inspection and testing run."""
        return tool_inspect_website(
            url=url,
            context=context,
            personas=personas,
            headed=headed,
            wait_for_completion=wait_for_completion,
        )

    @server.tool(
        name="get_test_status",
        description=(
            "Poll the real-time execution status, current stage, and task progress of a BlindSpot test run."
        ),
    )
    def get_test_status(run_id: str) -> Dict[str, Any]:
        """Check status of a running or completed test."""
        return tool_get_test_status(run_id=run_id)

    @server.tool(
        name="get_test_results",
        description=(
            "Retrieve a concise summary of a completed test run, including task pass/fail metrics, "
            "counts of verified defects vs usability observations, top findings, and report file paths."
        ),
    )
    def get_test_results(run_id: str) -> Dict[str, Any]:
        """Retrieve high-level results and report locations for a completed run."""
        return tool_get_test_results(run_id=run_id)

    @server.tool(
        name="get_findings",
        description=(
            "Retrieve detailed, validated UX findings for a run. Supports filtering by severity "
            "('Critical', 'High', 'Medium', 'Low') or category ('verified_issue', 'usability_observation', 'potential_improvement'). "
            "Includes observable evidence, reproduction steps, and suggested fixes."
        ),
    )
    def get_findings(
        run_id: str,
        severity: Optional[str] = None,
        category: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Retrieve detailed findings and suggested improvements."""
        return tool_get_findings(run_id=run_id, severity=severity, category=category)

    @server.tool(
        name="verify_fixes",
        description=(
            "Verify bug fixes by comparing a re-test against a reference run. "
            "Pass run_id (the new run) and reference_run_id (the baseline run) to produce an objective diff "
            "(Resolved, Recurring, New, Inconclusive), or pass url, context, and reference_run_id to start a new verification run."
        ),
    )
    def verify_fixes(
        url: Optional[str] = None,
        context: Optional[str] = None,
        run_id: Optional[str] = None,
        reference_run_id: Optional[str] = None,
        personas: int = 3,
    ) -> Dict[str, Any]:
        """Verify resolved defects between baseline and re-test runs."""
        return tool_verify_fixes(
            url=url,
            context=context,
            run_id=run_id,
            reference_run_id=reference_run_id,
            personas=personas,
        )

    return server


# Default server instance
mcp_server = create_mcp_server()


def run_mcp_server(transport: str = "stdio") -> None:
    """Launch the BlindSpot MCP server using the specified transport (default stdio)."""
    mcp_server.run(transport=transport)


if __name__ == "__main__":
    run_mcp_server()
