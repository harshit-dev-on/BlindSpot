# TaskFlow — BlindSpot Sample Test Application

This directory contains a complete, self-contained mock web application specifically designed for testing and demonstrating the BlindSpot AI-powered UX testing tool without requiring third-party websites or external dependencies.

---

## Features for UX Simulation Testing

1. **Navigation Bar**: Accessible anchor links (`#features`, `#pricing`, `#contact`) and interactive buttons.
2. **Hero Call-to-Action**: Primary buttons triggering in-page transitions.
3. **Interactive Beta Signup Form**:
   - Inputs: Full Name (`#full-name`), Work Email (`#work-email`), Role Selector (`#user-role`), Team Size (`#team-size`), and Notes textarea.
   - Client-side validation: Highlights missing inputs or invalid email formats.
   - Dynamic Success Confirmation: Upon submission, hides the form and renders a clear confirmation banner (`#confirmation-banner`).
4. **Transparent Pricing Cards**: Multiple pricing tiers with clear feature checkmarks.

---

## 1. How to Serve the Sample Site Locally

From the repository root in PowerShell:

```powershell
# Start local HTTP server on port 8080
python -m http.server 8080 --directory examples/sample_site
```

The site will now be reachable at `http://localhost:8080`.

---

## 2. Running BlindSpot Against the Sample Site

BlindSpot's built-in SSRF defense prevents automated agents from navigating to private networks by default. To test local development servers, pass the explicit `--allow-local` flag.

### Option A: Standard Full Test (Using Your Configured AI Provider)

```powershell
blindspot inspect `
  --url "http://localhost:8080" `
  --context "TaskFlow project management and sprint tracking web app for engineering teams" `
  --personas 2 `
  --allow-local
```

### Option B: Fast Offline Inspection (No AI API Key Required)

To inspect page structure, interactive elements, and capture screenshots without invoking any AI models:

```powershell
blindspot inspect `
  --url "http://localhost:8080" `
  --context "TaskFlow agile software" `
  --skip-ai `
  --allow-local
```

### Option C: Visible Browser Demonstration (Headed Mode)

Watch the browser inspect and explore the sample site on your screen:

```powershell
blindspot inspect `
  --url "http://localhost:8080" `
  --context "TaskFlow project management SaaS" `
  --headed `
  --allow-local
```

---

## 3. Viewing the Generated UX Report

Once the run completes, BlindSpot automatically creates a unique directory under `reports/` containing:
- `report.html`: Interactive, responsive HTML report.
- `report.json`: Full structured JSON dataset.
- `screenshot.png`: High-resolution viewport screenshot.
- `evidence/`: Action logs and checkpoint screenshots.

To view the HTML report in your browser on Windows:

```powershell
# Open the latest generated report in your default browser
Start-Process (Get-ChildItem reports/*/report.html | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName
```
