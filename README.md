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
├── .gitignore               # Excludes venvs, secrets, caches, and test artifacts
├── pyproject.toml           # PEP 621 package metadata, dependencies & CLI entry point
├── README.md                # Project documentation & Windows quickstart
├── src/
│   └── blindspot/
│       ├── __init__.py      # Package version & metadata
│       ├── __main__.py      # python -m blindspot entry point
│       ├── cli.py           # Typer CLI application (blindspot, inspect)
│       ├── core/
│       │   ├── __init__.py
│       │   ├── models.py    # Dataclasses & models (InspectConfig, ValidationResult)
│       │   └── validation.py# URL & context validation with friendly error hints
│       └── utils/
│           ├── __init__.py
│           └── console.py   # Rich terminal output formatting & panels
└── tests/
    ├── __init__.py
    ├── test_cli.py          # Typer CLI command tests
    └── test_validation.py   # Unit tests for URL and context validation
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

## 🚀 Usage

Once installed, the `blindspot` command is available in your activated environment.

### 1. View Root Help

```powershell
blindspot --help
```

Output:
```text
Usage: blindspot [OPTIONS] COMMAND [ARGS]...

  BlindSpot: Open-source AI-powered website UX testing tool.

  Simulates real user personas exploring websites to uncover UX flaws,
  accessibility barriers, and confusing user journeys.

Options:
  -v, --version  Show the version of BlindSpot and exit.
  --help         Show this message and exit.

Commands:
  inspect  Prepare and validate a website inspection session.
```

### 2. View Inspect Command Help

```powershell
blindspot inspect --help
```

Output:
```text
Usage: blindspot inspect [OPTIONS]

  Prepare and validate a website inspection session.

  Requires a target website URL and a context description of the website's
  purpose and target audience.

Options:
  -u, --url TEXT      Target website URL to test (e.g. https://example.com).
                      [required]
  -c, --context TEXT  Context describing website purpose & audience, or path
                      to text file.  [required]
  --help              Show this message and exit.
```

### 3. Run Inspect with Valid Inputs

Pass an inspection target URL and context directly:

```powershell
blindspot inspect --url https://example.com --context "An online bookstore for technical software developers looking for reference guides."
```

You can also pass a file reference using the `@` prefix or a direct path:

```powershell
blindspot inspect --url https://example.com --context @my-context.txt
```

### 4. Beginner-Friendly Error Messages

BlindSpot validates all inputs and provides actionable, clear tips if something is wrong:

**Missing Protocol Scheme:**
```powershell
blindspot inspect --url example.com --context "E-commerce store"
```
```text
╭─ Invalid URL Provided ───────────────────────────────────────────────────╮
│ ❌ URL is missing a protocol scheme (http:// or https://).               │
│                                                                          │
│ 💡 Tip: Did you mean 'https://example.com'? BlindSpot requires an        │
│ explicit 'https://' or 'http://' prefix.                                 │
╰──────────────────────────────────────────────────────────────────────────╯
```

**Context Too Brief:**
```powershell
blindspot inspect --url https://example.com --context "store"
```
```text
╭─ Invalid Context Provided ───────────────────────────────────────────────╮
│ ❌ Context description is too brief (5 characters).                      │
│                                                                          │
│ 💡 Tip: Provide more context (at least 10 characters) describing the     │
│ website's purpose and target audience.                                   │
╰──────────────────────────────────────────────────────────────────────────╯
```

---

## 🧪 Running Automated Tests

Run the test suite using `pytest`:

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
- [x] Automated test suite
- [ ] Browser automation core using **Playwright**
- [ ] Provider-agnostic AI persona generation (starting with **Gemma 4**)
- [ ] Action recording (DOM snapshots, user journeys, console logs, screenshots)
- [ ] Analysis engine and consolidate UX report generator
- [ ] **Model Context Protocol (MCP)** server integration for AI coding agents
- [ ] Web-based demonstration UI

---

## 📄 License

Apache-2.0
