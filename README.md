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
├── pyproject.toml               # PEP 621 package metadata, dependencies & CLI entry point
├── README.md                    # Project documentation & Windows quickstart
├── src/
│   └── blindspot/
│       ├── __init__.py          # Package version & metadata
│       ├── __main__.py          # python -m blindspot entry point
│       ├── cli.py               # Typer CLI application (blindspot, inspect)
│       ├── browser/             # Playwright browser inspection engine
│       │   ├── __init__.py      # Exports BrowserInspector, inspect_website, models
│       │   ├── models.py        # Pydantic models for elements, viewport, results
│       │   └── inspector.py     # Browser automation, navigation, and DOM harvesting
│       ├── core/
│       │   ├── __init__.py
│       │   ├── models.py        # Core dataclasses & models (InspectConfig, ValidationResult)
│       │   └── validation.py    # URL & context validation with friendly error hints
│       └── utils/
│           ├── __init__.py
│           └── console.py       # Rich terminal output formatting & panels
└── tests/
    ├── __init__.py
    ├── test_browser.py          # Browser automation and element extraction tests
    ├── test_cli.py              # Typer CLI command tests
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

Open PowerShell or Command Prompt in the `BlindSpot` root directory:

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
pip install -e ".[dev]"
```

*(Alternatively, if you use [uv](https://github.com/astral-sh/uv), you can run: `uv pip install -e ".[dev]"`)*

---

### Step 5: Install Playwright Browsers

Download Chromium (or all browsers) for automated browser testing:

```powershell
playwright install chromium
```

---

## 🚀 Usage

Once installed, the `blindspot` command is available in your activated environment.

### 1. View Root Help

```powershell
blindspot --help
```

### 2. View Inspect Command Help

```powershell
blindspot inspect --help
```

Output:
```text
Usage: blindspot inspect [OPTIONS]

  Inspect a target website using browser automation.

  Navigates to the website with Playwright, captures interactive elements, page
  content, full-page screenshot, and structured inspection data.

Options:
  -u, --url TEXT                  Target website URL to test (e.g.
                                  https://example.com).  [required]
  -c, --context TEXT              Context describing website purpose & audience,
                                  or path to text file.  [required]
  -o, --output-dir PATH           Custom directory to store artifacts (default:
                                  unique folder in reports/).
  -b, --browser TEXT              Browser engine to use: chromium, firefox,
                                  webkit.  [default: chromium]
  --headless / --no-headless      Run browser in headless mode or visible
                                  window.  [default: headless]
  --help                          Show this message and exit.
```

### 3. Run Browser Inspection

Execute an inspection on a live website:

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

### 4. Custom Output Directory and Browser Options

Store inspection artifacts in a designated directory:

```powershell
blindspot inspect --url "https://example.com" --context "A demo website" --output-dir "./my_test_run"
```

Or watch the browser live using `--no-headless`:

```powershell
blindspot inspect --url "https://example.com" --context "A demo website" --no-headless
```

### 5. Generated Artifacts

Each inspection run generates:
- **`screenshot.png`**: High-resolution full-page screenshot of the rendered website.
- **`inspection_result.json`**: Structured metadata containing:
  - Page title and final landing URL (accounting for redirects)
  - Viewport dimensions and browser engine
  - Extracted body text content
  - Discovered visible interactive elements (links, buttons, form inputs, textareas, selects) with their tags, labels, attributes, and bounding box coordinates
  - Aggregate statistics (total elements, link counts, button counts, field counts)

### 6. Beginner-Friendly Error Handling

BlindSpot validates all inputs and provides actionable, clear tips if something is wrong:

**Missing Protocol Scheme:**
```powershell
blindspot inspect --url example.com --context "E-commerce store"
```
```text
┌─ Invalid URL Provided ──────────────────────────────────────────────────────┐
│                                                                             │
│  [ERROR] URL is missing a protocol scheme (http:// or https://).            │
│                                                                             │
│  [TIP] Did you mean 'https://example.com'? BlindSpot requires an explicit   │
│  'https://' or 'http://' prefix.                                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Context Too Brief:**
```powershell
blindspot inspect --url https://example.com --context "store"
```
```text
┌─ Invalid Context Provided ──────────────────────────────────────────────────┐
│                                                                             │
│  [ERROR] Context description is too brief (5 characters).                   │
│                                                                             │
│  [TIP] Provide more context (at least 10 characters) describing the         │
│  website's purpose and target audience.                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🧪 Running Automated Tests

Run the full test suite using `pytest`:

```powershell
pytest
```

Or run with verbose output:

```powershell
pytest -v
```

---

## 🗺️ Roadmap & Next Steps

- [x] Clean `src/` layout and PEP 621 packaging (`pyproject.toml`)
- [x] Typer CLI foundation (`blindspot` and `blindspot inspect`)
- [x] Input validation for URL and context with beginner-friendly errors
- [x] Automated test suite (unit and CLI tests)
- [x] Browser automation inspection engine using **Playwright**
- [x] Full-page screenshot capture & interactive element discovery
- [x] Dedicated artifact run directories & structured JSON export
- [ ] Provider-agnostic AI persona generation (starting with **Gemma 4**)
- [ ] Action recording (DOM snapshots, user journeys, console logs, error states)
- [ ] Analysis engine and consolidated UX report generator
- [ ] **Model Context Protocol (MCP)** server integration for AI coding agents
- [ ] Web-based demonstration UI

---

## 📄 License

Apache-2.0
