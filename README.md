# BlindSpot 👁️

> **AI-Powered Website UX Testing Tool**
>
> Uncover hidden user experience flaws, confusing user journeys, and accessibility barriers using autonomous AI user personas and browser automation.

---

## 🎯 Project Vision

BlindSpot accepts two core inputs:
1. **Website URL** – The target web application or site to inspect.
2. **Context** – A description of the website's purpose, target audience, and primary user goals.

Its automated workflow:
1. **Understand & Model** – Analyzes the website context and structure.
2. **Synthesize Personas** – Generates diverse AI user personas (varying in technical proficiency, accessibility needs, and user goals).
3. **Execute Website Tasks** – Directs Playwright browser automation to realistically navigate and attempt tasks.
4. **Capture Evidence** – Records detailed user actions, DOM state, console errors, and screenshots.
5. **Analyze & Recommend** – Evaluates observations with AI (demonstrated with Gemma 4) to produce actionable, evidence-backed UX improvements.

---

## 📁 Project Structure

BlindSpot follows the modern Python `src/` layout:

```text
BlindSpot/
├── .gitignore                   # Excludes venvs, secrets, caches, and test artifacts
├── blindspot.example.toml       # Template configuration file for AI providers
├── pyproject.toml               # PEP 621 package metadata, dependencies & CLI entry point
├── README.md                    # Project documentation & Windows quickstart
├── src/
│   └── blindspot/
│       ├── __init__.py          # Package version & metadata
│       ├── __main__.py          # python -m blindspot entry point
│       ├── cli.py               # Typer CLI application (inspect, provider)
│       ├── ai/                  # Provider-agnostic AI integration layer
│       │   ├── __init__.py      # Exports providers, models, and factory
│       │   ├── base.py          # BaseAIProvider interface & structured JSON parser
│       │   ├── exceptions.py    # AI provider exception hierarchy
│       │   ├── factory.py       # Provider registry & creation factory
│       │   ├── models.py        # AIResponse and ProviderStatus models
│       │   └── providers/
│       │       ├── ollama.py    # Local inference with Ollama (e.g. Gemma 4)
│       │       └── openai_compatible.py # Hosted or self-hosted OpenAI-compatible APIs
│       ├── browser/             # Playwright browser inspection engine
│       │   ├── __init__.py      # Exports BrowserInspector, inspect_website, models
│       │   ├── models.py        # Pydantic models for elements, viewport, results
│       │   └── inspector.py     # Browser automation, navigation, and DOM harvesting
│       ├── config/              # Configuration loader & validation
│       │   ├── __init__.py      # Config exports
│       │   ├── loader.py        # TOML loader with file discovery & env overrides
│       │   └── models.py        # Pydantic schema for AIConfig & BlindSpotConfig
│       ├── core/
│       │   ├── __init__.py
│       │   ├── models.py        # Core dataclasses & models (InspectConfig, ValidationResult)
│       │   └── validation.py    # URL & context validation with friendly error hints
│       └── utils/
│           ├── __init__.py
│           └── console.py       # Rich terminal output formatting, panels & tables
└── tests/
    ├── __init__.py
    ├── test_ai_provider.py      # Unit tests for providers, mocking, structured output
    ├── test_browser.py          # Browser automation and element extraction tests
    ├── test_cli.py              # Typer CLI command tests (inspect, help)
    ├── test_cli_provider.py     # CLI tests for provider list, test, and prompt
    ├── test_config.py           # Configuration loading, validation, and overrides
    └── test_validation.py       # Unit tests for URL and context validation
```

---

## 💻 Windows Installation & Setup

### Prerequisites
- **Python 3.10 or higher** (Python 3.14+ supported)
- **Git for Windows**
- **PowerShell** or **Windows Terminal** (or Command Prompt)

---

### Step 1: Open Terminal in Project Directory

```powershell
cd D:\Projects\BlindSpot
```

---

### Step 2: Create a Virtual Environment

```powershell
python -m venv .venv
```

---

### Step 3: Activate the Virtual Environment

**In PowerShell:**
```powershell
.\.venv\Scripts\Activate.ps1
```

> 💡 **Note for PowerShell Users:** If you see an error like `cannot be loaded because running scripts is disabled on this system`, run this once in PowerShell:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```
> Then re-run `.\.venv\Scripts\Activate.ps1`.

**In Command Prompt (cmd.exe):**
```cmd
.\.venv\Scripts\activate.bat
```

---

### Step 4: Install BlindSpot in Editable Mode

Install the package along with development dependencies (`pytest`):

```powershell
python -m pip install -e ".[dev]"
```

*(Alternatively, if you use [uv](https://github.com/astral-sh/uv), you can run: `uv pip install -e ".[dev]"`)*

---

### Step 5: Install Playwright Browsers

Download Chromium for automated browser testing:

```powershell
playwright install chromium
```

---

## 🤖 AI Provider Configuration

BlindSpot features a provider-agnostic AI layer supporting both **local inference** (via Ollama) and **cloud / self-hosted endpoints** (via any OpenAI-compatible API).

### 1. Configuration File (`blindspot.toml`)

Copy the included template:

```powershell
copy blindspot.example.toml blindspot.toml
```

BlindSpot searches for configuration in:
1. Explicit path passed via `--config <path>`
2. Working directory: `./blindspot.toml` or `./.blindspot.toml`
3. User home directory: `~/.blindspot/config.toml`
4. Built-in defaults

#### Option A: Local Ollama (Default)

Use a local Ollama instance (ideal for **Gemma 4** or other local models):

```toml
[ai]
provider = "ollama"
model = "gemma4"
base_url = "http://localhost:11434"
timeout = 90.0
```

To pull the model in Ollama:
```powershell
ollama pull gemma4
```

#### Option B: OpenAI-Compatible API

Works with OpenAI, OpenRouter, Groq, Together, vLLM, LM Studio, or LocalAI:

```toml
[ai]
provider = "openai_compatible"
model = "gpt-4o-mini"
base_url = "https://api.openai.com/v1"
api_key_env = "OPENAI_API_KEY"
timeout = 60.0
```

### 2. Secure API Key Management

BlindSpot **never logs or saves API keys to disk**. Keys are read dynamically from environment variables:

**In PowerShell:**
```powershell
$env:OPENAI_API_KEY = "your-actual-api-key"
```

**In Command Prompt:**
```cmd
set OPENAI_API_KEY=your-actual-api-key
```

### 3. Environment Variable Overrides

Any setting can be overridden at runtime via environment variables:

| Variable | Description |
|---|---|
| `BLINDSPOT_PROVIDER` | `ollama` or `openai_compatible` |
| `BLINDSPOT_MODEL` | Model identifier (e.g., `gemma4`, `gpt-4o-mini`) |
| `BLINDSPOT_BASE_URL` | Custom endpoint URL |
| `BLINDSPOT_API_KEY_ENV` | Environment variable name storing the API key |
| `BLINDSPOT_TIMEOUT` | Request timeout in seconds |

---

## 🚀 Usage

### 1. Manage and Test AI Providers

#### List Supported Providers & Active Config
```powershell
blindspot provider list
```

Output:
```text
                            BlindSpot AI Providers                             
  Provider             Type                   Default Endpoint      Status     
  ollama (active)      Local inference        http://localhost:…    Supported  
  openai_compatible    Hosted or              https://api.opena…    Supported  
                       self-hosted API                                         

┌─────────────────────────── Active Configuration ────────────────────────────┐
│   Active Provider     ollama                                                │
│   Active Model        gemma4                                                │
│   Base URL            (default)                                             │
│   API Key Source      (not required)                                        │
│   Config Source       Built-in Defaults / Environment                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Test Provider Connectivity
Verify that the model server is running and the model is loaded:

```powershell
blindspot provider test
```

Override parameters on the fly:
```powershell
# Test a custom model or provider
blindspot provider test --provider openai_compatible --model gpt-4o-mini
```

#### Run a Basic AI Prompt
Send a quick prompt directly to the configured AI model to confirm generation:

```powershell
blindspot provider prompt "Give a 1-sentence tip for testing website accessibility."
```

---

### 2. Run Website Browser Inspection

Inspect a website using Playwright browser automation:

```powershell
blindspot inspect --url "https://example.com" --context "A demo website"
```

Output:
```text
┌───────────────────── BlindSpot Website Inspection Plan ─────────────────────┐
│                                                                             │
│   Website URL       https://example.com                                     │
│   Context           A demo website                                          │
│   Context Length    14 characters                                           │
│                                                                             │
└────────────────────── Status: Input validation passed ──────────────────────┘
→ Launching chromium to inspect https://example.com...
┌─────────────────── BlindSpot Browser Inspection Complete ───────────────────┐
│                                                                             │
│   Page Title              Example Domain                                    │
│   Final URL               https://example.com/                              │
│   Browser / Viewport      chromium (1280x800)                               │
│   Interactive Elements    1 total (1 links, 0 buttons, 0 form fields)       │
│   Page Text Length        917 characters                                    │
│   Screenshot Saved        reports\run_example_com_20261016_113645\screen…   │
│   Structured Data Saved   reports\run_example_com_20261016_113645\inspec…   │
│                                                                             │
└──────────────────────── Status: Artifacts captured ─────────────────────────┘
[OK] Inspection successful. Artifacts saved to directory.
```

#### Visible (Headed) Browser Mode
Watch the browser launch in a desktop window:
```powershell
blindspot inspect --url "https://example.com" --context "A demo website" --headed
```

#### Custom Output Directory
```powershell
blindspot inspect --url "https://example.com" --context "A demo website" --output-dir "./my_run"
```

---

## 🧪 Running Automated Tests

Run all unit, integration, and CLI tests (no live API keys or large model downloads required):

```powershell
pytest
```

Run with verbose test reporting:
```powershell
pytest -v
```

---

## 🗺️ Roadmap & Next Steps

- [x] Clean `src/` layout and PEP 621 packaging (`pyproject.toml`)
- [x] Typer CLI foundation (`blindspot` and `blindspot inspect`)
- [x] Input validation for URL and context with beginner-friendly errors
- [x] Browser automation inspection engine using **Playwright**
- [x] Full-page screenshot capture & interactive element discovery
- [x] Dedicated artifact run directories & structured JSON export
- [x] Provider-agnostic AI integration (**Ollama** & **OpenAI-compatible**)
- [x] Secure API key resolution and configuration loader (`blindspot.toml`)
- [x] AI CLI management (`blindspot provider list`, `test`, `prompt`)
- [x] Structured JSON output extraction, schema validation & retry engine
- [ ] AI persona synthesis pipeline (interpreting website inspection + context)
- [ ] Task assignment & autonomous persona-based browser interaction
- [ ] Consolidated evidence-backed UX improvement report generator
- [ ] **Model Context Protocol (MCP)** server integration for AI coding agents
- [ ] Web-based demonstration UI

---

## 📄 License

Apache-2.0
