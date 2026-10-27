<p align="center">
  <a href="https://github.com/harshit-dev-on/BlindSpot">
    <img src="logo.svg" alt="BlindSpot Logo" width="160">
  </a>
</p>

<div align="center">

# BlindSpot

### The open-source AI UX & accessibility testing tool. Autonomous AI personas that explore, audit, and fix your app’s user experience.

<br/>

<a href="docs/TECHNICAL_SPECIFICATION.md"><img src="https://img.shields.io/badge/Docs-Technical%20Spec-2b9246?style=for-the-badge&logo=gitbook&logoColor=white" alt="Docs"></a>
<a href="https://github.com/harshit-dev-on/BlindSpot"><img src="https://img.shields.io/badge/Website-blindspot.ai-f0f0f0?style=for-the-badge&logoColor=000000" alt="Website"></a>
<a href="https://github.com/harshit-dev-on/BlindSpot/discussions"><img src="https://img.shields.io/badge/Community-Discussions-blue?style=for-the-badge&logo=github&logoColor=white" alt="Community"></a>

<a href="#-local-web-studio--report-viewer"><img src="https://img.shields.io/badge/Web%20Studio-Local%20UI-2b9246?style=for-the-badge&logoColor=white" alt="Web Studio"></a>
<a href="#-zero-docker-requirement"><img src="https://img.shields.io/badge/Zero%20Docker-Native%20Playwright-3b82f6?style=for-the-badge&logoColor=white" alt="Zero Docker"></a>

<a href="https://github.com/harshit-dev-on/BlindSpot"><img src="https://img.shields.io/github/stars/harshit-dev-on/BlindSpot?style=flat-square" alt="GitHub Stars"></a>
<a href="LICENSE"><img src="https://img.shields.io/badge/License-Apache%202.0-3b82f6?style=flat-square" alt="License"></a>
<a href="https://pypi.org/project/blindspot/"><img src="https://img.shields.io/badge/PyPI-v0.1.0-orange?style=flat-square" alt="PyPI Version"></a>
<a href="https://github.com/harshit-dev-on/BlindSpot/actions"><img src="https://img.shields.io/badge/Tests-175%20Passing-brightgreen?style=flat-square" alt="Tests"></a>

</div>

<br/>

> [!TIP]
> **Token-Efficient & Grounded!** BlindSpot analyzes web pages directly through semantic DOM HTML, computed CSS styles, and compact element refs (`@e1`, `@e2`) — eliminating token exhaustion from heavy images while capturing complete layout and styling context.

---

## BlindSpot Overview

BlindSpot are autonomous AI UX and accessibility testing agents that act just like real diverse human users — they navigate your application dynamically, experience cognitive friction, uncover usability barriers, and validate accessibility standards through actual interactive exploration. Built for product teams, frontend developers, and QA engineers who need fast, qualitative usability insights without the overhead of manual human testing panels or the false positives and blind spots of static analysis linters.

**Key Capabilities:**

- **Token-Efficient DOM HTML & CSS Analysis** — Personas inspect semantic DOM structure, computed CSS styles, and compact element references (`@e1`, `@e2`) with zero image token overhead
- **Live Browser Execution** — Watch personas navigate in real time with interactive element highlighting and a floating Heads-Up Display (HUD)
- **Full UX & Accessibility Toolkit** — DOM structure extraction, cognitive load evaluation, WCAG 2.2 Level AA checks, and interactive journey auditing out of the box
- **Synthetic User Personas** — Diverse AI personas modeling real-world technical literacy, motor impairments, visual needs, and specific user goals
- **Zero Docker Requirement** — Native host Playwright browser automation running cleanly in user space (`~/.blindspot`), with no heavy containers or background daemons
- **Developer-First CLI** — Streamlined ergonomics (`-t`, `-u`, `-i`, `-c`, `-m`, `-n`, `--config`), instant preflight checks, and animated terminal spinners
- **Compliance & Actionable Reporting** — Standalone interactive HTML reports with reproduction screenshots, JSON datasets, and native SARIF for GitHub Code Scanning

<br/>

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
│ • Technical literacy, accessibility needs, and intent modeling  │
│ • Observable tasks & verifiable success criteria synthesis       │
│ • Pydantic schema validation & deterministic fallbacks          │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ Stage 3: Token-Efficient DOM & CSS Browser Execution            │
│ • Semantic DOM HTML & computed CSS styling ingestion            │
│ • Compact element reference resolution (@e1, @e2, CSS/text)     │
│ • 100% isolated browser contexts per persona                    │
│ • Live headed mode with floating HUD and element highlighting   │
│ • Destructive action filtering & sensitive credential masking   │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ Stage 4: UX Findings Synthesis & Actionable Remediation         │
│ • Finding taxonomy: Verified Defects vs Usability Observations  │
│ • Self-contained, responsive HTML and structured JSON outputs   │
│ • Native SARIF export for GitHub Security Code Scanning tab     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Use Cases

- **Autonomous UX & Usability Audits** — Detect cognitive friction, confusing copy, dead-end navigation, and form abandonment points
- **WCAG 2.2 Level AA Accessibility Audits** — Validate color contrast, screen reader ARIA attributes, keyboard navigation traps, and focus visibility
- **User Journey & Funnel Verification** — Validate onboarding flows, multi-step checkouts, and critical conversion funnels across desktop and mobile viewports
- **Continuous CI/CD Regression Testing** — Run headless audits on pull requests to catch user-facing regressions before shipping to production

---

## 🚀 Quick Start

**Prerequisites:**
- Python 3.10+ (Windows, macOS, Linux)
- An LLM API key from any [supported provider](#configuration) (Google Gemini, OpenAI, Anthropic, OpenRouter) or local [Ollama](https://ollama.com)

### Installation & First Audit

```bash
# Windows (PowerShell) - 1-Line Universal Installer:
irm https://raw.githubusercontent.com/harshit-dev-on/BlindSpot/master/scripts/install.ps1 | iex

# macOS / Linux (Bash) - 1-Line Universal Installer:
curl -fsSL https://raw.githubusercontent.com/harshit-dev-on/BlindSpot/master/scripts/install.sh | bash

# Or via pipx:
pipx install git+https://github.com/harshit-dev-on/BlindSpot.git
# (or from local clone: pipx install .)
```

```bash
# Configure your AI provider (Gemini, Claude, OpenAI, OpenRouter, or Ollama)
export BLINDSPOT_LLM="gemini/gemini-2.5-flash"
export LLM_API_KEY="your-api-key"

# Run your first UX & accessibility audit
blindspot --target https://example.com
```

> [!NOTE]
> First run automatically provisions the sandboxed Playwright Chromium engine without requiring Docker or root privileges. Results are saved to `reports/run_<target>_<timestamp>/`.

### Updating

```bash
# Upgrade with pipx
pipx upgrade blindspot

# ...or re-run the 1-line installer
irm https://raw.githubusercontent.com/harshit-dev-on/BlindSpot/master/scripts/install.ps1 | iex
```

---

## Ways to Run BlindSpot

- **Open Source CLI** — Free, fast, runs natively with local Playwright and your own LLM key. [Quick Start](#-quick-start)
- **Interactive Terminal Start Screen** — Guided launcher with target suggestions and instant setup: `blindspot`
- **Local Web Studio UI** — Visual test launcher, live inspection viewer, and persona generator: `blindspot web`
- **Local Report Viewer** — Instant browser report viewing for completed audits: `blindspot view`

---

## 🖥️ Local Web Studio & Report Viewer

Every audit writes its results, telemetry, and screenshots to disk as it runs. Review them with dedicated local commands:

```bash
# Open and view the most recent audit report in your browser
blindspot view

# ...or view a specific run by name
blindspot view run_example_com_20261024_214532

# Launch the visual BlindSpot Web Studio UI (FastAPI + Modern Web App)
blindspot web --port 8000
```

The report viewer displays interactive task timelines, reproduction steps, screenshots, and prioritized remediation actions.

---

## 🤖 Use BlindSpot from Your Coding Agent

BlindSpot is agent-ready. Give Claude Code, Cursor, Codex, Goose, or Antigravity the ability to run audits, verify UX fixes, and evaluate accessibility:

```bash
# Export bundled Agent Skills conforming to the open SKILL.md specification
blindspot skill export --target agents    # installs to .agents/skills/
blindspot skill export --target github    # installs to .github/skills/
```

### Model Context Protocol (MCP) Server

Launch the native Model Context Protocol server to allow AI coding agents to inspect websites and execute persona journeys via standard MCP tools:

```bash
blindspot mcp
```

Add to your `mcp_config.json`:
```json
{
  "mcpServers": {
    "blindspot": {
      "command": "blindspot",
      "args": ["mcp"]
    }
  }
}
```

See [`AGENTS.md`](AGENTS.md) and [`docs/TECHNICAL_SPECIFICATION.md`](docs/TECHNICAL_SPECIFICATION.md) for agent directives and reference patterns.

---

## ✨ Features

### Agentic Usability & Inspection Tools

BlindSpot agents come equipped with an end-to-end browser and DOM evaluation toolkit:

- **Structural DOM & Accessibility Extractor** — Deep extraction of interactive buttons, anchors, forms, accessible names, ARIA states, and visible text
- **Sandboxed Browser Sessions** — 100% isolated browser contexts per persona ensuring zero state leakage across tests
- **Autonomous Decision Loop** — Goal-directed agents that click, type, scroll, wait, and evaluate outcomes
- **Safety & Guardrails** — Automatic SSRF protection, private IP blocking, sensitive credential masking, and destructive action filtering
- **Multi-Modal Evidence Acquisition** — Checkpoint screenshots at key interactions, complete action logs, and DOM snapshots

### Comprehensive UX & WCAG 2.2 Coverage

BlindSpot evaluates critical usability and accessibility factors across industry standards:

- **Perceivable (WCAG 1.x)** — Color contrast analysis, alt text sufficiency, non-text content, media alternatives
- **Operable (WCAG 2.x)** — Keyboard navigation accessibility, focus indicator visibility, avoid keyboard traps, touch target sizing
- **Understandable (WCAG 3.x)** — Error identification and suggestion, input assistance, predictable navigation patterns
- **Robust (WCAG 4.x)** — Valid ARIA markup, status messages, name/role/value attributes
- **Nielsen Usability Heuristics** — Visibility of system status, match between system and real world, error prevention, aesthetic and minimalist design

### Synthetic Persona Synthesis Engine

Advanced persona generation grounded directly in the target website's content and audience:

- **Technical Literacy Spectrum** — Simulates tech-savvy power users, average consumers, and novice/elderly users
- **Accessibility Needs** — Screen reader users, motor-impaired keyboard-only navigators, and low-vision users
- **Real-World Goal Synthesis** — Devises observable tasks with verifiable success criteria tailored to the inspected site

---

## Usage Examples

### Basic Usage

```bash
# Test a public website
blindspot --target https://example.com

# Test with short alias
blindspot -t https://example.com
```

### Custom Focus & Instructions

Guide testing towards specific user flows or areas of concern:

```bash
# Focus on checkout and payment friction
blindspot -t https://shop.example.com -i "Focus on the checkout funnel and cart validation"

# Provide instructions from a file
blindspot -t https://shop.example.com --instruction-file ./audit-instructions.txt
```

### Local Development Server Testing

Safely test local servers (localhost / 127.0.0.1) using the `--allow-local` flag:

```bash
blindspot -t http://localhost:3000 --allow-local
```

### Live Visible Browser & Persona Concurrency Control

Watch personas operate on your website live on screen with element highlighting, human pacing, and a real-time HUD, and control how many personas to test or run simultaneously:

```bash
# Watch a single persona operate live for fast interactive testing
blindspot -t https://example.com --headed -p 1

# Run multiple personas simultaneously in parallel
blindspot -t https://example.com -p 3 --concurrency 3

# Launch the interactive terminal wizard (prompts for live view & persona count)
blindspot
```

### Headless CI Mode

Run BlindSpot programmatically without interactive prompts using `-n/--non-interactive` — perfect for automated pipelines, scripts, and CI runners:

```bash
blindspot -n -t https://example.com -m gemini/gemini-2.5-flash
```

### CI/CD (GitHub Actions)

Add BlindSpot to your GitHub Actions pipeline to audit every pull request and upload SARIF accessibility findings:

```yaml
name: blindspot-ux-audit

on:
  pull_request:

jobs:
  ux-audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install BlindSpot
        run: pip install git+https://github.com/harshit-dev-on/BlindSpot.git

      - name: Install Playwright Browsers
        run: playwright install chromium

      - name: Run BlindSpot Audit
        env:
          BLINDSPOT_LLM: ${{ secrets.BLINDSPOT_LLM }}
          LLM_API_KEY: ${{ secrets.LLM_API_KEY }}
        run: blindspot -n -t https://staging.example.com

      - name: Upload SARIF Results
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: reports/
        continue-on-error: true
```

---

## Configuration

BlindSpot supports universal environment variables:

```bash
# Model selection (format: <provider>/<model>)
export BLINDSPOT_LLM="gemini/gemini-2.5-flash"

# API Key
export LLM_API_KEY="your-api-key"

# Optional: custom API base for local models (e.g. Ollama, LMStudio)
export LLM_API_BASE="http://localhost:11434"
```

> [!NOTE]
> BlindSpot automatically persists your configuration to `~/.blindspot/cli-config.json` and `~/.blindspot/config.toml`, so you don't have to re-enter it on every run.
> You can also run `blindspot setup` anytime for interactive guided configuration.

### Recommended Models:

- [Google Gemini 2.5 Flash](https://aistudio.google.com/) — `gemini/gemini-2.5-flash` *(Default pick: fast, highly cost-effective, excellent vision & DOM reasoning)*
- [Anthropic Claude 3.7 Sonnet](https://console.anthropic.com/) — `anthropic/claude-3-7-sonnet` *(Top-tier UX reasoning and heuristic synthesis)*
- [OpenAI GPT-4o-mini](https://platform.openai.com/) — `openai/gpt-4o-mini` *(Reliable, high speed, structured JSON output)*
- [Ollama Gemma 4 / Llama 3](https://ollama.com/) — `ollama/gemma4` *(100% offline, zero API costs, runs on localhost)*
- [OpenRouter](https://openrouter.ai/) — `openrouter/deepseek/deepseek-chat` *(Universal gateway across 100+ open-source and proprietary models)*

---

## Documentation

Full architectural documentation, data models, Nielsen heuristic mappings, and WCAG evaluation criteria are preserved in **[`docs/TECHNICAL_SPECIFICATION.md`](docs/TECHNICAL_SPECIFICATION.md)**.

## Contributing

We welcome contributions of code, heuristics, test personas, and new agent skills! Check out our [Contributing Guidelines](CONTRIBUTING.md) or open an [Issue](https://github.com/harshit-dev-on/BlindSpot/issues) or [Pull Request](https://github.com/harshit-dev-on/BlindSpot/pulls).

## Join Our Community

Have questions? Found a usability bug? Want to discuss autonomous testing agents?
**[Join our GitHub Discussions!](https://github.com/harshit-dev-on/BlindSpot/discussions)**

## Support the Project

**Love BlindSpot?** Give us a ⭐ on GitHub!

## Acknowledgements

BlindSpot builds on the incredible work of open-source projects like [Playwright](https://github.com/microsoft/playwright), [LiteLLM](https://github.com/BerriAI/litellm), [Rich](https://github.com/Textualize/rich), and [Typer](https://github.com/tiangolo/typer). Huge thanks to their maintainers!

---

> [!WARNING]
> **Authorized use only.** BlindSpot actively navigates and interacts with the web targets you specify. Only run tests against applications you own or have explicit permission to test. Always use `--allow-local` cautiously on development servers.
