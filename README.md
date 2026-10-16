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
│       ├── cli.py               # Typer CLI application (setup, inspect, provider, model)
│       ├── cli_setup.py         # Interactive multi-provider setup wizard
│       ├── ai/                  # Universal AI provider integration layer
│       │   ├── __init__.py      # Exports providers, models, and factory
│       │   ├── adapter.py       # UnifiedAIAdapter wrapping LiteLLM engine
│       │   ├── base.py          # BaseAIProvider interface & structured JSON parser
│       │   ├── exceptions.py    # AI provider exception hierarchy
│       │   ├── factory.py       # Universal provider registry & creation factory
│       │   ├── models.py        # AIResponse and ProviderStatus models
│       │   └── providers/       # Lightweight provider implementations
│       ├── browser/             # Playwright browser inspection engine
│       │   ├── __init__.py      # Exports BrowserInspector, inspect_website, models
│       │   ├── models.py        # Pydantic models for elements, viewport, results
│       │   └── inspector.py     # Browser automation, navigation, and DOM harvesting
│       ├── config/              # Configuration loader & validation
│       │   ├── __init__.py      # Config exports
│       │   ├── loader.py        # TOML loader with file discovery & persistence
│       │   └── models.py        # Pydantic schema for AIConfig, TaskModelsConfig, etc.
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

## 🤖 Universal AI Model Configuration System

BlindSpot features a universal AI model layer powered by **LiteLLM** under a dedicated adapter (`UnifiedAIAdapter`). You are never locked into a single provider or model.

Supported deployment categories:
1. **Local AI** – Run models on your own machine without sending data to the cloud (e.g. **Ollama** running **Gemma 4**, Llama 3, Mistral, Qwen).
2. **Cloud APIs** – Hosted foundation models with direct API access (e.g. **Google Gemini**, **OpenAI**, **Anthropic Claude**, **OpenRouter**).
3. **Custom Endpoints** – Self-hosted or third-party OpenAI-compatible endpoints (e.g. vLLM, LM Studio, LocalAI, Together AI, Groq).
4. **Hybrid / Task-Specific Models** – Direct different models to specific pipeline tasks (e.g. fast model for persona generation, reasoning model for UX analysis).

---

### 🧙‍♂️ Interactive Setup Wizard (`blindspot setup`)

The easiest way to get started is the interactive setup wizard:

```powershell
blindspot setup
```

The wizard guides you through:
1. Choosing your deployment category (`local`, `cloud`, `custom`, or `hybrid`).
2. Selecting your provider (`ollama`, `gemini`, `openai`, `anthropic`, `openrouter`, or `custom`).
3. Selecting or entering your model (e.g., `gemma4`, `gemini-2.5-flash`, `gpt-4o-mini`, `claude-3-5-sonnet-20241022`).
4. Entering credentials safely (hidden entry, never displayed or printed in plaintext).
5. Testing the connection in real time.
6. Saving your configuration to `~/.blindspot/config.toml` (user-level) or `blindspot.toml` (project-level).

---

### 📋 CLI Provider & Model Commands

| Command | Description |
|---|---|
| `blindspot setup` | Launch the interactive configuration wizard |
| `blindspot provider list` | Display all supported providers, active provider, model, and endpoint |
| `blindspot provider test` | Probe health and run a 1-token verification test on the active model |
| `blindspot model list` | Discover locally installed Ollama models or show curated cloud models |
| `blindspot provider prompt "<text>"` | Send a test prompt directly to verify model output |

#### Discover Models
```powershell
# List models installed locally in Ollama
blindspot model list --provider ollama

# List popular models for Google Gemini
blindspot model list --provider gemini

# List popular models for OpenAI
blindspot model list --provider openai
```

#### Test Connection & Send Verification Prompts
```powershell
# Test the currently active configuration
blindspot provider test

# Test a specific provider/model combination on the fly
blindspot provider test --provider gemini --model gemini-2.5-flash

# Send a test prompt to verify model generation
blindspot provider prompt "Give a 1-sentence tip for testing website accessibility."
```

---

### 🔧 Configuration Guides

#### 1. How to Configure a Local Gemma 4 Model (via Ollama)

**Why choose this?** 100% private, runs entirely on your local GPU/CPU, zero cloud API costs.

1. Install and launch [Ollama](https://ollama.ai/).
2. Pull the Gemma 4 model in your terminal:
   ```powershell
   ollama pull gemma4
   ```
3. Run the BlindSpot setup wizard:
   ```powershell
   blindspot setup
   ```
   - Select `local` -> `ollama` -> `gemma4`.
4. Alternatively, create or update `~/.blindspot/config.toml`:
   ```toml
   [ai]
   category = "local"
   provider = "ollama"
   model = "gemma4"
   base_url = "http://localhost:11434"
   timeout = 90.0
   ```
5. Test the connection:
   ```powershell
   blindspot provider test
   ```

---

#### 2. How to Configure Google Gemini API

**Why choose this?** High-speed, large context window, advanced multimodal capabilities, and generous free-tier limits.

1. Get a Gemini API key from [Google AI Studio](https://aistudio.google.com/).
2. Set your environment variable:
   ```powershell
   # PowerShell (Current Session)
   $env:GEMINI_API_KEY = "your-actual-gemini-api-key"

   # Or persist in Windows User Environment Variables:
   [System.Environment]::SetEnvironmentVariable('GEMINI_API_KEY', 'your-key', 'User')
   ```
3. Run `blindspot setup`:
   - Select `cloud` -> `gemini` -> `gemini-2.5-flash`.
   - Press Enter to use your existing `GEMINI_API_KEY` environment variable.
4. Or configure `~/.blindspot/config.toml`:
   ```toml
   [ai]
   category = "cloud"
   provider = "gemini"
   model = "gemini-2.5-flash"
   api_key_env = "GEMINI_API_KEY"
   timeout = 60.0
   ```
5. Test the connection:
   ```powershell
   blindspot provider test
   ```

---

#### 3. How to Switch Providers

BlindSpot resolves configuration using clear precedence:
**CLI Flags > Environment Variables > Local `blindspot.toml` > Global `~/.blindspot/config.toml` > Defaults**

You can switch providers in any of these ways:

- **Method A: Re-run the setup wizard:**
  ```powershell
  blindspot setup
  ```
- **Method B: Edit your configuration file (`~/.blindspot/config.toml`):**
  Change `provider = "gemini"` and `model = "gemini-2.5-flash"`.
- **Method C: Environment variables:**
  ```powershell
  $env:BLINDSPOT_PROVIDER = "openai"
  $env:BLINDSPOT_MODEL = "gpt-4o-mini"
  ```
- **Method D: Temporary CLI flags:**
  ```powershell
  blindspot provider test --provider anthropic --model claude-3-5-sonnet-20241022
  ```

---

#### 4. Future Task-Specific Model Routing

BlindSpot is designed so different models can handle different UX pipeline tasks in the future:

```toml
[ai]
category = "hybrid"
provider = "ollama"
model = "gemma4"  # Default fallback model

[ai.tasks]
persona_generation = "gemini-2.5-flash"   # Fast cloud model for personas
task_planning      = "gemma4"             # Local model for task steps
ux_analysis        = "gemini-2.5-pro"     # High-reasoning model for UX analysis
report_generation  = "gemini-2.5-flash"   # Consolidated report formatting
```

---

### 🔒 Security Principles

- **Never Hardcoded:** API keys are never stored inside codebase source files or committed to Git.
- **Environment First:** Recommended storage is via system environment variables (`GEMINI_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`).
- **No Secrets in Output:** Keys are masked (e.g. `sk-...abcd`) in terminal tables and omitted from logs.
- **Git Ignored:** `blindspot.toml` and `.blindspot/` are included in `.gitignore`.
- **No Unnecessary Network Traffic:** Model tests are only triggered when explicitly requested (`blindspot provider test` or during `blindspot setup`).

---

## 🚀 Usage Guide

### 1. Website Browser Inspection

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
- [x] Universal AI configuration with **LiteLLM** adapter (`UnifiedAIAdapter`)
- [x] Interactive setup wizard (`blindspot setup`) with secure hidden credentials
- [x] Multi-provider support (Ollama, Gemini, OpenAI, Anthropic, OpenRouter, Custom endpoints)
- [x] CLI provider tools (`blindspot provider list`, `test`, `prompt`, `blindspot model list`)
- [x] Structured JSON output extraction, schema validation & retry engine
- [x] Task-specific model routing configuration (`persona_generation`, `ux_analysis`, etc.)
- [ ] AI persona synthesis pipeline (interpreting website inspection + context)
- [ ] Task assignment & autonomous persona-based browser interaction
- [ ] Consolidated evidence-backed UX improvement report generator
- [ ] **Model Context Protocol (MCP)** server integration for AI coding agents
- [ ] Web-based demonstration UI

---

## 📄 License

Apache-2.0
