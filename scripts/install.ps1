# BlindSpot Universal 1-Line Installer for Windows PowerShell
# Usage: irm https://raw.githubusercontent.com/harshit-dev-on/BlindSpot/master/scripts/install.ps1 | iex

$ErrorActionPreference = "Stop"

# Verify Python is available
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    $pythonCmd = Get-Command py -ErrorAction SilentlyContinue
}

if (-not $pythonCmd) {
    Write-Host "Error: Python 3.10+ is required to install BlindSpot." -ForegroundColor Red
    Write-Host "Please install Python from https://python.org or the Microsoft Store." -ForegroundColor Yellow
    exit 1
}

$InstallDir = Join-Path $HOME ".blindspot\bin"
$VenvDir = Join-Path $HOME ".blindspot\venv"

New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null

Write-Host "-> Setting up isolated environment at $VenvDir..." -ForegroundColor Cyan

if (-not (Test-Path $VenvDir)) {
    & $pythonCmd.Source -m venv $VenvDir
}

$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
$VenvPip = Join-Path $VenvDir "Scripts\pip.exe"
$VenvBlindspot = Join-Path $VenvDir "Scripts\blindspot.exe"

& $VenvPip install --quiet --upgrade pip
Write-Host "-> Installing BlindSpot into isolated environment..." -ForegroundColor Cyan
if (Test-Path "$PSScriptRoot\..\pyproject.toml") {
    & $VenvPip install --quiet "$PSScriptRoot\.."
} elseif (Test-Path ".\pyproject.toml") {
    & $VenvPip install --quiet "."
} else {
    & $VenvPip install --quiet "git+https://github.com/harshit-dev-on/BlindSpot.git"
}

# Create runner batch file in ~/.blindspot/bin
$ShimFile = Join-Path $InstallDir "blindspot.cmd"
$ShimContent = "@echo off`r`n`"$VenvBlindspot`" %*"
[System.IO.File]::WriteAllText($ShimFile, $ShimContent, [System.Text.Encoding]::ASCII)

# Auto-provision Chromium browser binary
Write-Host "-> Provisioning headless browser engine..." -ForegroundColor Cyan
try {
    & $VenvPython -m playwright install chromium
} catch {
    # Non-blocking, will auto-provision on first run if failed here
}

# Add ~/.blindspot/bin to User PATH if not already present
$CurrentPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($CurrentPath -notlike "*$InstallDir*") {
    $NewPath = "$CurrentPath;$InstallDir"
    [Environment]::SetEnvironmentVariable("Path", $NewPath, "User")
    $env:Path += ";$InstallDir"
    Write-Host "+ Added $InstallDir to user PATH" -ForegroundColor Green
}

Write-Host "+ BlindSpot ready" -ForegroundColor Green
Write-Host ""
Write-Host '  ____  _     ___ _   _ ____  ____  ____   ___ _____ ' -ForegroundColor Cyan
Write-Host ' | __ )| |   |_ _| \ | |  _ \/ ___||  _ \ / _ \_   _|' -ForegroundColor Cyan
Write-Host ' |  _ \| |    | ||  \| | | | \___ \| |_) | | | || |  ' -ForegroundColor Cyan
Write-Host ' | |_) | |___ | || |\  | |_| |___) |  __/| |_| || |  ' -ForegroundColor Cyan
Write-Host ' |____/|_____|___|_| \_|____/|____/|_|    \___/ |_|  ' -ForegroundColor Cyan
Write-Host '   Autonomous AI UX & Usability Testing Agent' -ForegroundColor DarkGray
Write-Host ""
Write-Host 'To get started:' -ForegroundColor White
Write-Host ''
Write-Host '  1. Set your environment:' -ForegroundColor Cyan
Write-Host '     $env:LLM_API_KEY = "your-api-key"' -ForegroundColor DarkGray
Write-Host '     $env:BLINDSPOT_LLM = "google/gemini-2.5-flash"' -ForegroundColor DarkGray
Write-Host '     (or run "blindspot setup" for interactive configuration)' -ForegroundColor DarkGray
Write-Host ''
Write-Host '  2. Run a UX & accessibility audit:' -ForegroundColor Cyan
Write-Host '     blindspot --target https://example.com' -ForegroundColor DarkGray
Write-Host ''
Write-Host 'For more information visit https://github.com/harshit-dev-on/BlindSpot' -ForegroundColor DarkGray
Write-Host 'Supported models: Gemini, OpenAI, Claude, OpenRouter, Ollama' -ForegroundColor DarkGray
Write-Host ''
