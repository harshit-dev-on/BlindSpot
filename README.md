# BlindSpot Technical Documentation

### Autonomous AI-Powered Website UX and Accessibility Auditing Engine

| Specification | Details |
|---|---|
| **Document Version** | 1.0.0 |
| **Software Version** | 0.1.0 |
| **Supported Platforms** | Windows 10/11, macOS 12+, Linux (Ubuntu 22.04+, Debian 12+, Fedora 38+) |
| **Runtime Environment** | Python 3.10, 3.11, 3.12, 3.13, 3.14+ |
| **Browser Engine** | Chromium (Playwright automation layer) |
| **License** | Apache License 2.0 |

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Architecture and Pipeline](#2-system-architecture-and-pipeline)
3. [System Requirements and Platform Matrix](#3-system-requirements-and-platform-matrix)
4. [Installation and Environment Setup](#4-installation-and-environment-setup)
5. [Quickstart Guide](#5-quickstart-guide)
6. [Command-Line Interface (CLI) Manual](#6-command-line-interface-cli-manual)
7. [AI Provider and Model Configuration](#7-ai-provider-and-model-configuration)
8. [Security and Sandboxing Guardrails](#8-security-and-sandboxing-guardrails)
9. [Report and Evidence Data Model](#9-report-and-evidence-data-model)
10. [Web Demonstration Studio](#10-web-demonstration-studio)
11. [Model Context Protocol (MCP) Integration](#11-model-context-protocol-mcp-integration)
12. [Agent Skills Integration (Open Specification)](#12-agent-skills-integration-open-specification)
13. [Offline Testing and Local Sample Application](#13-offline-testing-and-local-sample-application)
14. [Automated Test Suite and Verification](#14-automated-test-suite-and-verification)
15. [Troubleshooting and Diagnostic Reference](#15-troubleshooting-and-diagnostic-reference)
16. [Repository Structure](#16-repository-structure)
17. [License and Compliance](#17-license-and-compliance)

---

## 1. Executive Summary

BlindSpot is an autonomous user experience (UX) and accessibility auditing framework designed to eliminate the diagnostic gap between synthetic technical tests (such as unit, integration, and standard end-to-end assertions) and qualitative human usability evaluations.

Traditional testing suites verify that code paths execute without raising exceptions; however, they cannot evaluate cognitive friction, navigation dead ends, confusing copy, inaccessible form workflows, or visual layout discrepancies. Human usability studies provide these qualitative insights but are resource-intensive, slow, and impossible to run on every continuous integration commit.

BlindSpot bridges this gap by combining large language models with browser automation:
- **Zero Instrument Requirement**: Operates strictly against the rendered browser surface without requiring source code modifications, analytics SDKs, or special test hooks.
- **Diverse Synthetic Personas**: Generates realistic simulated user profiles reflecting varying degrees of technical literacy, accessibility requirements, device constraints, and behavioral goals.
- **Autonomous Task Execution**: Deploys isolated browser contexts to execute user tasks, evaluate interactive controls, capture telemetry, and collect evidence.
- **Evidence-Backed Remediation**: Produces deterministic JSON datasets and standalone HTML dashboards classifying findings into verified functional defects, usability observations, and actionable potential improvements.

---

## 2. System Architecture and Pipeline

BlindSpot executes a multi-stage testing pipeline that isolates each phase of the evaluation process to guarantee deterministic outputs and prevent session contamination.

```
                    Target Website URL + Context
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ Stage 1: Website Inspection & Structural DOM Ingestion          │
│ • Viewport initialization (Chromium 1280x800 desktop default)   │
│ • Full-page rendered baseline screenshot capture                │
│ • Interactive element extraction (buttons, anchors, inputs)    │
│ • Bounding box computation & visible accessibility attributes   │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ Stage 2: Grounded Persona Synthesis & Task Planning             │
│ • Prompt-injection-fenced DOM content delivery                  │
│ • Technical literacy, accessibility, and intent modeling        │
│ • Synthesis of realistic, observable tasks & success criteria   │
│ • Pydantic schema validation & fallback synthesis               │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ Stage 3: Autonomous Sandboxed Browser Execution                 │
│ • 100% isolated browser contexts per persona                    │
│ • Zero state leakage (cookies, storage, cache isolated)         │
│ • Autonomous decision loop: click, fill, select, scroll, wait   │
│ • Destructive action filtering & sensitive credential masking   │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ Stage 4: Multi-Modal Evidence Acquisition                       │
│ • Checkpoint screenshots at key interactions & task conclusions │
│ • Complete chronological action telemetry & DOM text state      │
│ • Explicit verification against persona success criteria        │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ Stage 5: UX Report Synthesis and Classification                 │
│ • Finding taxonomy: Verified Defects vs Usability Observations  │
│ • Structured reproduction steps with associated screenshots     │
│ • High-priority remediation recommendations                     │
│ • Self-contained, responsive HTML and structured JSON outputs   │
└─────────────────────────────────────────────────────────────────┘
```

### Architectural Principles

1. **Strict Context Isolation**: Every persona executes within a freshly initialized `BrowserContext`. Cookies, session storage, and cache entries do not persist across persona boundaries.
2. **Defensive Model Consumption**: Untrusted website text is strictly fenced within structural XML boundaries before transmission to language models.
3. **Black-Box Operation**: Tests interact strictly with rendered DOM nodes through standard user input simulations (clicks, keyboard strokes, navigation requests).
4. **Resilient Failure Modes**: Network delays, missing elements, and navigation timeouts are captured as test observations rather than unhandled software exceptions.

---

## 3. System Requirements and Platform Matrix

### Operating System Support

| Operating System | Architecture | Support Level |
|---|---|---|
| **Windows 11** | x64, ARM64 | Fully Supported (Primary development target) |
| **Windows 10** (build 19041+) | x64 | Fully Supported |
| **macOS 12.0+ (Monterey, Ventura, Sonoma, Sequoia)** | Apple Silicon, x64 | Fully Supported |
| **Linux (Ubuntu 22.04 LTS, Debian 12, Fedora 38+)** | x64, ARM64 | Fully Supported |

### Software Prerequisites

- **Python Runtime**: Python 3.10, 3.11, 3.12, 3.13, or 3.14+.
- **Browser Runtime**: Playwright-managed Chromium engine.
- **Hardware Resources**:
  - Memory: 4 GB minimum (8 GB+ recommended when running local language models).
  - Storage: 1 GB available disk space for browser binaries, caches, and test run evidence.

### Supported AI Backends

BlindSpot features a universal AI abstraction layer powered by LiteLLM:
- **Local Language Models**: Ollama (e.g., Gemma 4, Llama 3, Mistral, Qwen 2.5).
- **Google Gemini**: Gemini 2.5 Flash, Gemini 1.5 Pro via Google AI Studio.
- **OpenAI**: GPT-4o, GPT-4o-mini via OpenAI API.
- **Anthropic**: Claude 3.5 Sonnet, Claude 3 Opus via Anthropic API.
- **OpenRouter & Custom Gateways**: Any OpenAI-compatible inference gateway.

---

## 4. Installation and Environment Setup

### 4.1 Quick Install (Single Command — Strix Standard)

BlindSpot installs natively with zero system-level dependencies and **no Docker requirement**. Headless Chromium binaries are auto-provisioned directly into user space (`~/.blindspot`), keeping your host clean and isolated.

**Windows (PowerShell):**
```powershell
irm https://raw.githubusercontent.com/harshit-dev-on/BlindSpot/master/scripts/install.ps1 | iex
```

**Linux / macOS (Bash / Zsh):**
```bash
curl -fsSL https://raw.githubusercontent.com/harshit-dev-on/BlindSpot/master/scripts/install.sh | bash
```

The installer automatically:
1. Clones and sets up a dedicated virtual environment in `~/.blindspot/venv`.
2. Provisions the native Playwright Chromium browser binary without requiring administrator or root rights.
3. Configures a direct CLI shim (`~/.blindspot/bin`) and adds it to your user `PATH`.
4. Leaves your existing Python installations completely unmodified.

---

### 4.2 Contributor & Local Development Installation

If you prefer to clone and contribute to the repository directly:

#### Step 1: Clone the Repository
```powershell
git clone https://github.com/harshit-dev-on/BlindSpot.git
cd BlindSpot
```

#### Step 2: Initialize Virtual Environment

**Windows PowerShell:**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

> [!NOTE]
> If Windows blocks script execution with an `Execution_Policies` restriction, permit local signed scripts:
> `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

**Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

#### Step 3: Install Package Dependencies
```powershell
# Recommended: Install core engine with development tools, web studio, and MCP server
pip install -e ".[dev,web,mcp]"
```

Alternatively, install specific components independently:
- **Core CLI Only**: `pip install -e .`
- **Development & Testing Suite**: `pip install -e ".[dev]"`
- **Web Demonstration Studio**: `pip install -e ".[web]"`
- **Model Context Protocol (MCP) Server**: `pip install -e ".[mcp]"`

### 4.4 Install Playwright Browser Binaries

Download the sandboxed Chromium browser runtime managed by Playwright:

```powershell
playwright install chromium
```

---

## 5. Quickstart Guide

### Step 1: Configure AI Credentials (Strix Standard)

You can configure BlindSpot using standard environment variables (zero configuration):

```bash
# Set your model route and API key (identical to Strix format)
export BLINDSPOT_LLM="google/gemini-2.5-flash"
export LLM_API_KEY="your-api-key"
```

Or launch the streamlined interactive setup wizard:

```powershell
blindspot setup
```

The wizard prompts for:
1. **Model Route**: In standard `<provider>/<model>` format (e.g., `gemini/gemini-2.5-flash`, `openai/gpt-4o-mini`, `anthropic/claude-3-7-sonnet`, `ollama/gemma4`).
2. **API Credentials**: Reads directly from your environment or securely saves to your local `~/.blindspot/config.toml`.
3. **Instant Preflight**: Automatically runs a live connection check.

### Step 2: Validate AI Provider Reachability

Verify that the configured provider responds properly:

```powershell
blindspot provider test
```

### Step 3: Execute an Autonomous Inspection Run

Run an end-to-end evaluation directly with `--target`:

```powershell
# Direct execution (Strix style)
blindspot --target "https://example.com"

# With custom focus instruction
blindspot -t "https://example.com" -i "Focus on navigation accessibility and checkout friction"
```

Or simply run bare `blindspot` to launch the interactive start screen / Web Studio:

```powershell
blindspot
```

### Step 4: Review Audit Artifacts

BlindSpot writes all run outputs to a dedicated folder under `reports/run_<sanitized_host>_<timestamp>/` containing both the interactive HTML report and the standardized `findings.sarif` report for GitHub / CI security scanning:

**Windows PowerShell:**
```powershell
Start-Process (Get-ChildItem reports/*/report.html | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName
```

---

## 6. Command-Line Interface (CLI) Manual

### 6.1 `blindspot inspect`

The primary execution command. Conducts DOM ingestion, persona synthesis, sandboxed task execution, evidence acquisition, and report generation.

```text
Usage: blindspot inspect [OPTIONS]
```

#### Options Reference

| Parameter | Short | Type | Default | Description |
|---|---|---|---|---|
| `--url` | `-u` | String | **Required** | Target website URL (HTTP or HTTPS scheme required). |
| `--context` | `-c` | String | **Required** | Plain-text purpose and target audience description, or path to a text file. |
| `--personas` | `-p` | Integer | `3` | Number of synthetic personas to simulate (clamped between 1 and 5). |
| `--max-actions` | | Integer | `8` | Maximum interactive action steps permitted per persona task. |
| `--browser` | `-b` | String | `chromium` | Browser engine: `chromium`, `firefox`, or `webkit`. |
| `--headless` / `--no-headless` | | Boolean | `True` | Run browser in headless mode. |
| `--headed` | | Flag | `False` | Launch browser in visible desktop window (alias for `--no-headless`). |
| `--output-dir` | `-o` | Path | Auto | Custom destination directory for test artifacts (defaults to `reports/run_*`). |
| `--allow-local` | | Flag | `False` | Explicitly permit navigation to loopback addresses (`localhost`, `127.0.0.1`). |
| `--skip-ai` | | Flag | `False` | Run DOM inspection and element extraction without calling AI models. |
| `--skip-execution` | | Flag | `False` | Synthesize personas and task plan without executing browser journeys. |
| `--skip-report` | | Flag | `False` | Skip final UX analysis and HTML/JSON report generation. |
| `--ai-provider` | | String | None | Runtime override for AI provider (e.g., `gemini`, `ollama`, `openai`). |
| `--ai-model` | | String | None | Runtime override for model identifier (e.g., `gemini-2.5-flash`). |

#### Examples

```powershell
# Standard run with 3 personas in headless mode
blindspot inspect -u "https://news.ycombinator.com" -c "Tech community link aggregator and discussion forum"

# Visible browser execution for live demonstration
blindspot inspect -u "https://example.com" -c "Reference site" --headed --personas 2

# Inspect local development server (explicit loopback opt-in required)
blindspot inspect -u "http://localhost:3000" -c "Next.js dashboard prototype" --allow-local

# Fast offline structural extraction without LLM generation
blindspot inspect -u "https://example.com" -c "Offline check" --skip-ai
```

### 6.2 `blindspot setup`

Launches the interactive terminal setup wizard. Collects deployment mode, provider, model name, and API credentials with masked terminal inputs.

```powershell
blindspot setup
```

### 6.3 `blindspot provider` Subcommands

Diagnostics and live queries against configured AI providers.

```powershell
# List supported providers, active provider, model identifier, and key source
blindspot provider list

# Test provider connectivity and verify text generation
blindspot provider test

# Test a specific provider and model without changing saved configuration
blindspot provider test --provider openai --model gpt-4o-mini

# Send an arbitrary prompt to the active provider
blindspot provider prompt "List 3 accessibility criteria for primary navigation menus."
```

### 6.4 `blindspot model` Subcommands

Discover models supported by or available on configured backends.

```powershell
# Query local Ollama instance for pulled models
blindspot model list --provider ollama

# List verified production models for Google Gemini
blindspot model list --provider gemini

# List verified production models for OpenAI
blindspot model list --provider openai
```

### 6.5 `blindspot web`

Launches the interactive Web Demonstration Studio.

```powershell
# Start web server on 127.0.0.1:8000 and open default browser
blindspot web

# Custom host and port configuration
blindspot web --host 0.0.0.0 --port 8080 --no-open

# Development mode with hot reloading
blindspot web --reload
```

### 6.6 `blindspot mcp`

Starts the Model Context Protocol (MCP) server over standard input/output (stdio) for integration with AI coding agents.

```powershell
blindspot mcp
```

### 6.7 `blindspot skill` Subcommands

Manage, inspect, validate, and install Agent Skills following the open specification (standardized under the Linux Foundation / Anthropic / OpenAI).

```powershell
# List all packaged skills and their token footprints
blindspot skill list

# Validate all packaged or local SKILL.md files against the specification checklist
blindspot skill validate

# Validate a specific skill or custom directory
blindspot skill validate ./my-custom-skill/SKILL.md

# Export and install skills into current workspace (.agents/skills and .github/skills)
blindspot skill install

# Export specifically to .agents/skills (for Cursor, Codex, Antigravity)
blindspot skill install --target agents

# Export specifically to .github/skills (for GitHub Copilot, VS Code)
blindspot skill install --target github
```

### 6.8 CLI Exit Codes

| Exit Code | Meaning |
|---|---|
| `0` | Success: Test execution and report generation completed successfully. |
| `1` | Fatal Error: Unhandled runtime error, critical environment failure, or skill validation failure. |
| `2` | Input Validation Error: Invalid URL, invalid context, or unsupported CLI flag. |

---

## 7. AI Provider and Model Configuration

### 7.1 Configuration Resolution Hierarchy

BlindSpot resolves configuration parameters using a strict precedence order:

```
1. Explicit CLI Flags (--ai-provider, --ai-model)
                      │
                      ▼
2. Environment Variables (BLINDSPOT_*, GEMINI_API_KEY, etc.)
                      │
                      ▼
3. Local Project File (./blindspot.toml)
                      │
                      ▼
4. User Global Config (~/.blindspot/config.toml)
                      │
                      ▼
5. Built-in Engine Defaults (Ollama / gemma4)
```

### 7.2 TOML Configuration Schema (`blindspot.toml` or `~/.blindspot/config.toml`)

```toml
[ai]
# Deployment category: "local", "cloud", or "custom"
category = "cloud"

# Active provider: "gemini", "ollama", "openai", "anthropic", "openrouter", "openai_compatible"
provider = "gemini"

# Model identifier
model = "gemini-2.5-flash"

# Custom endpoint URL (required for local Ollama or custom gateways)
# base_url = "http://localhost:11434"

# Environment variable containing the API credential (recommended)
api_key_env = "GEMINI_API_KEY"

# Direct API key (optional; environment variables preferred)
# api_key = ""

# Request timeout in seconds
timeout = 60.0

# Optional task-specific model routing
[ai.tasks]
persona_generation = "gemini-2.5-flash"
task_planning      = "gemini-2.5-flash"
ux_analysis        = "gemini-2.5-flash"
```

### 7.3 Environment Variables Reference (`.env.example`)

BlindSpot automatically loads credentials and overrides from the active environment:

```bash
# Provider API Credentials
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Runtime Engine Overrides
BLINDSPOT_PROVIDER=gemini
BLINDSPOT_MODEL=gemini-2.5-flash
BLINDSPOT_TIMEOUT=60.0
BLINDSPOT_BASE_URL=https://custom-gateway.internal/v1
```

---

## 8. Security and Sandboxing Guardrails

BlindSpot enforces zero-trust boundary controls across browser automation, network communications, prompt delivery, and report rendering.

### 8.1 Server-Side Request Forgery (SSRF) and Redirect Containment

- **Prohibited Subnets**: By default, browser automation is prohibited from navigating to private IPv4/IPv6 networks (RFC 1918: `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), loopback addresses (`127.0.0.1`, `localhost`, `::1`), and link-local ranges (`169.254.0.0/16`).
- **Cloud Metadata Defense**: Cloud instance metadata endpoints (`169.254.169.254`, `metadata.google.internal`, `instance-data`) are permanently blocked. This defense cannot be bypassed by any flag.
- **Post-Navigation Redirect Verification**: After every page load or client-side redirect, the browser agent evaluates `page.url`. If a public URL redirects to a prohibited internal IP address, execution is terminated immediately.
- **Controlled Loopback Opt-in**: Navigation to local development servers is only permitted when the operator explicitly passes `--allow-local`.

### 8.2 Prompt Injection Defense

Untrusted web content extracted from the target website (page titles, link text, button labels, meta descriptions) is strictly fenced within `<untrusted_website_content>` XML tags in all model prompts. System prompts instruct language models to treat enclosed content as passive observational data, ignoring embedded instructions, system role overrides, or jailbreak attempts.

### 8.3 Destructive Action Filtering

The browser execution agent evaluates interactive elements against destructive keyword heuristics. Actions targeting buttons or links containing irreversible phrases (such as "Delete Account", "Terminate Subscription", "Cancel Policy", "Purchase Now", "Submit Payment") are rejected, preventing destructive operations on live web applications.

### 8.4 Sensitive Input Masking

Target input fields associated with sensitive data (such as passwords, credit card numbers, CVVs, security questions, and API tokens) are masked with `********` before being recorded into action history objects, execution logs, or report files.

### 8.5 Cross-Site Scripting (XSS) Prevention

All dynamic data rendered into the standalone `report.html`—including page titles, persona biographies, element text snippets, reproduction steps, and suggested fixes—is escaped using `html.escape` to eliminate stored XSS vulnerabilities when viewing reports.

### 8.6 Path Traversal Neutralization

Report artifact endpoints in the web demo validate that requested file paths resolve strictly within the designated run directory using `Path.is_relative_to()`. Path traversal sequences (`..`, `/`, `\`) trigger an immediate HTTP 403 Forbidden response.

---

## 9. Report and Evidence Data Model

### 9.1 Artifacts Directory Layout

Every inspection run produces an isolated, self-contained directory under `reports/<run_id>/`:

```text
reports/run_example_com_20261016_120000/
├── screenshot.png               # Baseline full-page desktop screenshot
├── inspection_result.json       # Structural DOM inventory and metadata
├── personas.json                # Synthesized persona profiles and task assignments
├── execution_results.json       # Step-by-step action history and outcome statuses
├── report.json                  # Machine-readable report with prioritized findings
├── report.html                  # Responsive, self-contained HTML audit dashboard
└── evidence/                    # Per-persona, per-task checkpoint artifacts
    └── persona_1/
        └── task_p1_1/
            ├── step_1_click.png
            └── step_2_finish.png
```

### 9.2 Finding Classification Taxonomy

BlindSpot categorizes all audit findings into three distinct levels to prevent subjective UX opinions from being conflated with functional software bugs:

1. **Objectively Verified Defects (`verified_issue`)**:
   - Definite browser execution failures, unhandled JavaScript errors, broken HTTP navigation links (404/500), form submission rejections, crashed interactions, and missing accessibility attributes (`alt`, `aria-label`).
2. **Usability Observations (`usability_observation`)**:
   - Navigation friction, ambiguous button labels, confusing multi-step task progressions, visual clutter, or delayed user feedback observed during simulated journeys.
3. **Potential Improvements (`potential_improvement`)**:
   - Strategic enhancements to improve conversion rates, information hierarchy, layout legibility, or user guidance.

### 9.3 Machine-Readable Report Schema (`report.json`)

```json
{
  "run_id": "run_example_com_20261016_120000",
  "target_url": "https://example.com",
  "target_context": "Reference site",
  "timestamp": "2026-10-16T12:00:00.000000",
  "execution_metrics": {
    "total_personas": 2,
    "total_tasks": 4,
    "passed_tasks": 3,
    "failed_tasks": 1,
    "duration_seconds": 18.42
  },
  "summary": {
    "total_findings": 3,
    "verified_issues": 1,
    "usability_observations": 1,
    "potential_improvements": 1,
    "critical_count": 0,
    "high_count": 1,
    "medium_count": 1,
    "low_count": 1
  },
  "findings": [
    {
      "id": "finding_1",
      "category": "verified_issue",
      "severity": "high",
      "title": "Primary Call-to-Action button unresponsive",
      "description": "Clicking the 'Get Started' button failed to trigger navigation or reveal modal content.",
      "persona_name": "Marcus Vance",
      "task_name": "Create a team trial account",
      "reproduction_steps": [
        "Navigate to target URL",
        "Click button with selector '#hero-cta'"
      ],
      "evidence_screenshot": "evidence/persona_1/task_1/step_1_click.png",
      "suggested_fix": "Verify that event listeners on '#hero-cta' are bound prior to user interaction."
    }
  ]
}
```

---

## 10. Web Demonstration Studio

The Web Demonstration Studio provides an interactive visual dashboard for configuring audits, watching real-time testing progress, and inspecting reports.

```powershell
# Launch the web studio
blindspot web
```

### Architectural Design

- **Backend**: Built with FastAPI. Provides REST endpoints for run creation, artifact downloading, and status inspection.
- **Real-Time Telemetry**: Uses Server-Sent Events (SSE) via `/api/runs/{run_id}/events` to stream action logs, active persona switches, and checkpoint screenshots to the client without page polling.
- **Frontend**: Pure HTML5, Vanilla CSS, and JavaScript. Zero external frontend framework dependencies, ensuring fast load times and clean maintenance.
- **Safety**: Fully inherits engine-level SSRF defenses and path traversal validation.

### Web REST API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/` | `GET` | Serves the single-page application dashboard. |
| `/api/runs` | `GET` | Returns list of historical test runs stored in `reports/`. |
| `/api/runs` | `POST` | Initiates a new autonomous audit run in the background. |
| `/api/runs/{run_id}` | `GET` | Retrieves full status, progress metrics, and findings for a run. |
| `/api/runs/{run_id}/events` | `GET` | Server-Sent Events (SSE) live progress stream. |
| `/api/runs/{run_id}/report.html` | `GET` | Serves the standalone interactive HTML report. |
| `/api/runs/{run_id}/report.json` | `GET` | Serves the machine-readable JSON dataset. |
| `/api/runs/{run_id}/artifacts/{file_path}` | `GET` | Serves screenshots and checkpoint evidence files safely. |

---

## 11. Model Context Protocol (MCP) Integration

BlindSpot includes an official Model Context Protocol (MCP) server, allowing AI coding assistants (such as Cursor, Claude Desktop, and Antigravity) to autonomously test websites and inspect findings.

### 11.1 Starting the MCP Server

```powershell
# Run the MCP server over standard I/O (stdio)
blindspot mcp
```

### 11.2 Exposed MCP Tools

| Tool Name | Parameters | Description |
|---|---|---|
| `inspect_website` | `url`, `context`, `personas`, `headed`, `wait_for_completion`, `timeout_seconds` | Triggers an autonomous inspection and testing run. |
| `get_test_status` | `run_id` | Returns current execution stage, active step, and task metrics. |
| `get_test_results` | `run_id` | Retrieves structured summary of test outcomes, defect counts, and artifact paths. |
| `get_findings` | `run_id`, `severity` (optional), `category` (optional) | Retrieves full findings list with reproduction steps and remediation suggestions. |
| `verify_fixes` | `run_id`, `reference_run_id`, `url`, `context` | Compares two runs to verify whether previously identified defects were resolved. |

### 11.3 Client Configuration Examples

#### Claude Desktop (`%APPDATA%\Claude\claude_desktop_config.json`)

```json
{
  "mcpServers": {
    "blindspot": {
      "command": "d:\\Projects\\BlindSpot\\.venv\\Scripts\\blindspot.exe",
      "args": ["mcp"]
    }
  }
}
```

#### Cursor (`.cursor/mcp.json`)

```json
{
  "mcpServers": {
    "blindspot": {
      "command": "d:\\Projects\\BlindSpot\\.venv\\Scripts\\python.exe",
      "args": ["-m", "blindspot.mcp.server"]
    }
  }
}
```

---

## 12. Agent Skills Integration (Open Specification)

BlindSpot implements the **Agent Skills open standard** (standardized under the Linux Foundation / Agentic AI Foundation and supported across OpenAI Codex, GitHub Copilot, Cursor, Antigravity, and VS Code).

### 12.1 MCP and Skills Synergy: The Runner and the Playbook

BlindSpot pairs Model Context Protocol (MCP) and Agent Skills as complementary architectural layers:
- **MCP provides the Runner**: Exposes deterministic tools (`inspect_website`, `get_findings`, `verify_fixes`) and handles external process execution, telemetry, and isolation.
- **Agent Skills provide the Playbook**: Injects procedural domain expertise, heuristic evaluation checklists, WCAG compliance rules, and structured developer output templates into the agent's context window on demand.

### 12.2 Three-Tier Progressive Disclosure

To prevent context window bloat and minimize inference latency—especially on local models (Ollama, Gemma, Llama)—BlindSpot skills adhere strictly to progressive disclosure:

1. **Discovery Tier (Startup)**: Only skill `name` and `description` are loaded (~50 tokens per skill).
2. **Activation Tier (Triggered)**: The full `SKILL.md` body (instructions, output template, explicit rules, examples) is injected into context on demand (~1,300 to 1,700 tokens).
3. **Execution Tier (On-Demand)**: Domain references and specialized assets are loaded lazily only if explicitly requested.

### 12.3 Packaged Production Skills

BlindSpot ships with four pre-validated, production-grade skills installed directly into `.agents/skills` and `.github/skills`:

| Skill Name | Invocation | Primary Use Case | Allowed Tools |
|---|---|---|---|
| `blindspot-ux-audit` | `/blindspot-ux-audit` | Autonomous end-to-end UX, heuristic, and user-journey audit with developer remediation plan. | `blindspot inspect` |
| `blindspot-verify-fix` | `/blindspot-verify-fix` | Automated regression verification confirming whether a code patch resolved a previously reported defect. | `blindspot inspect` |
| `blindspot-wcag-audit` | `/blindspot-wcag-audit` | Accessibility audit mapping browser DOM barriers to WCAG 2.2 Level AA Success Criteria with accessible code diffs. | `blindspot inspect` |
| `blindspot-persona-designer` | `/blindspot-persona-designer` | Synthetic persona and test journey modeling tailored to specific application audiences and constraints. | `blindspot inspect` |

### 12.4 Exporting and Validating Skills

To export skills into user projects or validate compliance against the Agent Skills specification:

```powershell
# Export skills to .agents/skills (for Cursor, Codex, Antigravity) and .github/skills (for Copilot)
blindspot skill install

# Validate skill integrity against the specification checklist
blindspot skill validate
```

---

## 13. Offline Testing and Local Sample Application

The repository includes a standalone mock web application (`examples/sample_site/`) representing an agile sprint tracking SaaS ("TaskFlow"). It contains realistic navigation links, product feature grids, pricing tiers, and an interactive lead capture form with client-side validation and dynamic confirmation banners.

### 13.1 Serve the Sample Application

In a dedicated terminal:

```powershell
# Serve sample site on port 8080
python -m http.server 8080 --directory examples/sample_site
```

The application is now accessible at `http://localhost:8080`.

### 13.2 Run BlindSpot Against the Sample Application

```powershell
# Full autonomous audit with 2 personas (requires configured AI provider)
blindspot inspect `
  --url "http://localhost:8080" `
  --context "TaskFlow sprint tracking and agile project management tool for software teams" `
  --personas 2 `
  --allow-local

# Fast offline structural extraction (No AI API key required)
blindspot inspect `
  --url "http://localhost:8080" `
  --context "TaskFlow agile app" `
  --skip-ai `
  --allow-local

# Visible browser window demonstration
blindspot inspect `
  --url "http://localhost:8080" `
  --context "TaskFlow agile app" `
  --headed `
  --allow-local
```

---

## 14. Automated Test Suite and Verification

BlindSpot maintains a comprehensive automated test suite. All tests use deterministic mocks and local HTML fixtures, requiring zero active internet connections or third-party API keys:

```powershell
# Run the complete test suite (165 tests across 20 modules)
pytest

# Run tests with verbose output
pytest -v

# Run the end-to-end pipeline smoke test
pytest tests/test_smoke_e2e.py -v
```

### Test Coverage Breakdown

| Test Module | Coverage Scope |
|---|---|
| `tests/test_architecture_parity.py` | Strix modular architecture parity (`interface`, `runtime`, `agents`, `report`). |
| `tests/test_validation.py` | URL syntax, context parameters, and flag boundary checks. |
| `tests/test_config.py` | Configuration hierarchy resolution, defaults, model route parsing, and TOML serialization. |
| `tests/test_ai_provider.py` | Universal adapter, retries, token tracking, and structured response parsing. |
| `tests/test_cli_provider.py` | CLI provider subcommands (`list`, `test`, `prompt`) and Strix setup wizard. |
| `tests/test_browser.py` | Playwright DOM extraction, bounding box calculations, and page inspection. |
| `tests/test_provisioning.py` | Automatic first-run browser engine provisioning and fallback verification. |
| `tests/test_session.py` | Browser inspection models, viewport serialization, and coordinate bounds. |
| `tests/test_personas.py` | Persona synthesis, prompt injection containment, and Pydantic validation. |
| `tests/test_execution.py` | Browser task execution, isolated contexts, action safety, and input masking. |
| `tests/test_reporting.py` | Evidence aggregation, finding ranking, and HTML XSS escaping verification. |
| `tests/test_sarif.py` | SARIF 2.1.0 log generation, GitHub Code Scanning schema compliance, and rules catalog. |
| `tests/test_web.py` | FastAPI application routes, SSE event streaming, and path traversal guards. |
| `tests/test_mcp.py` | Model Context Protocol tool execution, fix verification, and status schemas. |
| `tests/test_skills.py` | Agent Skills discovery, spec checklist validation, export, and CLI commands. |
| `tests/test_tools.py` | Tool registry, execution safety dispatch, and schema validation. |
| `tests/test_knowledge.py` | Heuristics knowledge base, WCAG criteria matching, and domain patterns. |
| `tests/test_cli.py` | Typer CLI commands, option parsing, `--target`/`-t` direct execution, and safety flags. |
| `tests/test_smoke_e2e.py` | End-to-end integration smoke test running against a local loopback HTTP server. |

---

## 15. Troubleshooting and Diagnostic Reference

### 15.1 Chromium Browser Missing

**Error:** `playwright._impl._errors.Error: Executable doesn't exist at ...`  
**Resolution:** Run `playwright install chromium` to download the sandboxed browser binaries.

### 15.2 Windows Script Execution Restriction

**Error:** `File ...\Activate.ps1 cannot be loaded because running scripts is disabled on this system.`  
**Resolution:** Open PowerShell and execute:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 15.3 Navigation Rejected on Localhost or Private Network

**Error:** `Navigation URL ... resolves to private/restricted IP and local testing is not enabled.`  
**Resolution:** BlindSpot blocks loopback and private subnets by default to prevent SSRF. Pass the `--allow-local` flag to permit testing local development servers:
```powershell
blindspot inspect -u "http://localhost:8080" -c "Local Test" --allow-local
```

### 15.4 Missing AI API Credentials

**Error:** `AuthenticationError: API key not found for provider ...`  
**Resolution:** Run `blindspot setup` to save your credentials to your user configuration, or define the corresponding environment variable (e.g., `$env:GEMINI_API_KEY="your-key"` in PowerShell).

### 15.5 Web Studio Port Conflict

**Error:** `[Errno 10048] error while attempting to bind on address ('127.0.0.1', 8000)`  
**Resolution:** Specify an alternate port using the `--port` argument:
```powershell
blindspot web --port 8085
```

---

## 16. Repository Structure

```text
BlindSpot/
├── .agents/
│   └── skills/                  # Agent Skills for Codex, Cursor, Antigravity, and Goose
├── .github/
│   └── skills/                  # Agent Skills for GitHub Copilot and VS Code
├── .env.example                 # Template for environment variables and API credentials
├── .gitignore                   # Excludes environments, caches, secrets, and reports
├── blindspot.example.toml       # Template configuration file for AI providers
├── LICENSE                      # Apache License 2.0
├── pyproject.toml               # PEP 621 packaging metadata, dependencies, and CLI entry point
├── README.md                    # Official documentation manual
├── scripts/
│   ├── install.ps1              # 1-command native installer for Windows (PowerShell)
│   └── install.sh               # 1-command native installer for Linux and macOS (Bash)
├── examples/
│   └── sample_site/             # Standalone sample application for testing and demos
│       ├── index.html           # TaskFlow sample application page
│       ├── styles.css           # Responsive stylesheet
│       └── README.md            # Sample application documentation
├── src/
│   └── blindspot/
│       ├── __init__.py          # Package version and metadata
│       ├── __main__.py          # python -m blindspot execution entry point
│       ├── cli.py               # Typer CLI application commands (backward compatibility shim)
│       ├── cli_setup.py         # Setup wizard backward compatibility shim
│       ├── interface/           # Strix parity CLI interface & interactive terminal
│       │   ├── main.py          # Primary application entrypoint
│       │   ├── cli_args.py      # Argument definitions and callbacks
│       │   ├── interactive.py   # Interactive start screen and prompts
│       │   └── scan_setup.py    # Setup wizard & model preflight checks
│       ├── runtime/             # Strix parity browser runtime execution engine
│       │   ├── browser.py       # Playwright browser inspector and session manager
│       │   ├── provisioning.py  # Zero-config automatic browser binary provisioning
│       │   └── session.py       # Viewport and inspection result data models
│       ├── agents/              # Strix parity autonomous agent layer
│       │   ├── factory.py       # Agent and test runner instantiation factories
│       │   ├── prompt.py        # System prompts and cognitive step decision builders
│       │   └── runner.py        # Persona test runner and execution loop
│       ├── report/              # Strix parity reporting and artifact generation
│       │   ├── analysis.py      # Heuristic analyzers and finding deduplication
│       │   ├── models.py        # UXFinding, severity, and report data models
│       │   ├── sarif.py         # SARIF 2.1.0 generator for GitHub Code Scanning
│       │   └── writer.py        # Multi-format report writing orchestrator
│       ├── ai/                  # Universal AI provider integration layer (LiteLLM)
│       │   ├── adapter.py       # UnifiedAIAdapter implementation
│       │   ├── base.py          # BaseAIProvider abstract interface
│       │   ├── exceptions.py    # Standardized AI exception hierarchy
│       │   ├── factory.py       # Universal provider factory and registry
│       │   ├── models.py        # Structured AI request/response models
│       │   └── providers/       # Specific provider adaptors (Ollama, Gemini, OpenAI)
│       ├── browser/             # Backward-compatible browser module exports
│       ├── config/              # Configuration loader, resolver, and schemas
│       ├── core/                # Core pipeline orchestration and validation
│       │   ├── runner.py        # Central pipeline coordinator (run_pipeline)
│       │   └── validation.py    # URL and context syntax validation
│       ├── execution/           # Backward-compatible execution module exports
│       ├── mcp/                 # Model Context Protocol (MCP) server integration
│       ├── personas/            # Persona synthesis and task planning
│       ├── reporting/           # Backward-compatible reporting module exports
│       ├── skills/              # Agent Skills (Open Standard) definitions & manager
│       ├── tools/               # Tool registry and execution dispatch
│       ├── utils/
│       │   └── console.py       # Rich terminal formatting, panels, and status displays
│       └── web/                 # Interactive web demonstration studio (FastAPI)
└── tests/                       # Automated test suite (165 tests across 20 modules)
    ├── test_architecture_parity.py # Parity checks for interface, runtime, agents, report
    ├── test_ai_provider.py      # Provider adapter, retry, and structured parsing tests
    ├── test_browser.py          # Browser automation and element extraction tests
    ├── test_cli.py              # CLI command tests (setup, inspect, flags)
    ├── test_cli_provider.py     # Provider and model CLI subcommand tests
    ├── test_config.py           # Configuration loading and resolution tests
    ├── test_execution.py        # Browser agent execution and safety policy tests
    ├── test_knowledge.py       # Knowledge base heuristic rules tests
    ├── test_mcp.py              # Model Context Protocol tool tests
    ├── test_personas.py         # Persona synthesis and prompt injection defense tests
    ├── test_provisioning.py     # Automatic browser engine installation tests
    ├── test_reporting.py        # Evidence aggregation, HTML escaping, and report tests
    ├── test_sarif.py            # SARIF 2.1.0 output formatting tests
    ├── test_session.py          # Session models and inspection data tests
    ├── test_skills.py           # Agent Skills discovery, spec validation, and installation tests
    ├── test_smoke_e2e.py        # End-to-end pipeline smoke test on loopback HTTP
    ├── test_tools.py            # Tool execution and dispatch tests
    ├── test_validation.py       # URL and context validation unit tests
    └── test_web.py              # Web demo FastAPI endpoints and SSE stream tests
```

---

## 17. License and Compliance

BlindSpot is distributed under the terms of the **Apache License, Version 2.0**. For complete legal terms and conditions, refer to the [LICENSE](LICENSE) file in the root directory of this repository.

