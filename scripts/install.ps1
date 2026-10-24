# BlindSpot Universal 1-Line Installer for Windows PowerShell
# Usage: irm https://raw.githubusercontent.com/harshit-dev-on/BlindSpot/master/scripts/install.ps1 | iex

$ErrorActionPreference = "Stop"
chcp 65001 > $null 2>&1
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

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

function Invoke-ActionWithSpinner {
    param (
        [string]$Message,
        [string]$FilePath,
        [string[]]$ArgumentList
    )
    $frames = @([char]0x280B, [char]0x2819, [char]0x2839, [char]0x2838, [char]0x283C, [char]0x2834, [char]0x2826, [char]0x2827, [char]0x2807, [char]0x280F)
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $FilePath
    $psi.Arguments = ($ArgumentList -join " ")
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true

    $proc = [System.Diagnostics.Process]::Start($psi)
    $i = 0
    while (-not $proc.HasExited) {
        $frame = $frames[$i % $frames.Length]
        Write-Host -NoNewline "`r$frame $Message"
        Start-Sleep -Milliseconds 80
        $i++
    }
    $proc.WaitForExit()
    Write-Host -NoNewline ("`r" + (" " * ($Message.Length + 6)) + "`r")
    if ($proc.ExitCode -ne 0) {
        $err = $proc.StandardError.ReadToEnd()
        Write-Host "Error executing $FilePath : $err" -ForegroundColor Red
        throw "Command failed with exit code $($proc.ExitCode)"
    }
}

# 1. Setup isolated venv environment
if (-not (Test-Path $VenvDir)) {
    Invoke-ActionWithSpinner "setting up isolated environment" $pythonCmd.Source @("-m", "venv", $VenvDir)
}

$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
$VenvPip = Join-Path $VenvDir "Scripts\pip.exe"

# 2. Install / upgrade BlindSpot
$repoRoot = $null
if (Test-Path "$PSScriptRoot\..\pyproject.toml") {
    $repoRoot = (Resolve-Path "$PSScriptRoot\..").Path
} elseif (Test-Path ".\pyproject.toml") {
    $repoRoot = (Resolve-Path ".").Path
}

if ($repoRoot) {
    Invoke-ActionWithSpinner "installing blindspot" $VenvPip @("install", "--quiet", "--upgrade", "-e", "`"$repoRoot`"")
} else {
    Invoke-ActionWithSpinner "installing blindspot" $VenvPip @("install", "--quiet", "--upgrade", "git+https://github.com/harshit-dev-on/BlindSpot.git")
}

# 3. Create runner shim in ~/.blindspot/bin
$ShimFile = Join-Path $InstallDir "blindspot.cmd"
$ShimContent = "@echo off`r`n`"$VenvPython`" -m blindspot %*"
[System.IO.File]::WriteAllText($ShimFile, $ShimContent, [System.Text.Encoding]::ASCII)

# 4. Provision browser engine
try {
    Invoke-ActionWithSpinner "provisioning headless browser engine" $VenvPython @("-m", "playwright", "install", "chromium")
} catch {
    # Non-blocking, will auto-provision on first run if failed here
}

# 5. Add ~/.blindspot/bin to User PATH if not present
$CurrentPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($CurrentPath -notlike "*$InstallDir*") {
    $NewPath = "$CurrentPath;$InstallDir"
    [Environment]::SetEnvironmentVariable("Path", $NewPath, "User")
    $env:Path += ";$InstallDir"
}

# 6. Terminal completion output (matching Strix look)
$pyVer = & $VenvPython -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')"
Write-Host "  installed package blindspot 0.1.0, installed using Python $pyVer"
Write-Host "  These apps are now available"
Write-Host "    - blindspot.cmd"
$sparkles = "$([char]::ConvertFromUtf32(0x2728)) $([char]::ConvertFromUtf32(0x1F31F)) $([char]::ConvertFromUtf32(0x2728))"
Write-Host "done! $sparkles"

Write-Host ""
Write-Host "   ██████╗ ██╗     ██╗███╗   ██╗██████╗ ███████╗██████╗  ██████╗ ████████╗" -ForegroundColor Cyan
Write-Host "   ██╔══██╗██║     ██║████╗  ██║██╔══██╗██╔════╝██╔══██╗██╔═══██╗╚══██╔══╝" -ForegroundColor Cyan
Write-Host "   ██████╔╝██║     ██║██╔██╗ ██║██║  ██║███████╗██████╔╝██║   ██║   ██║   " -ForegroundColor Cyan
Write-Host "   ██╔══██╗██║     ██║██║╚██╗██║██║  ██║╚════██║██╔═══╝ ██║   ██║   ██║   " -ForegroundColor Cyan
Write-Host "   ██████╔╝███████╗██║██║ ╚████║██████╔╝███████║██║     ╚██████╔╝   ██║   " -ForegroundColor Cyan
Write-Host "   ╚═════╝ ╚══════╝╚═╝╚═╝  ╚═══╝╚═════╝ ╚══════╝╚═╝      ╚═════╝    ╚═╝   " -ForegroundColor Cyan
Write-Host ""
Write-Host "  Autonomous AI UX & Usability Testing Agent" -ForegroundColor DarkGray
Write-Host ""
Write-Host "To get started:" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  1. Set your environment (identical to Strix):" -ForegroundColor Cyan
Write-Host "     `$env:BLINDSPOT_LLM = 'gemini/gemini-2.5-flash'  # or `$env:STRIX_LLM" -ForegroundColor DarkGray
Write-Host "     `$env:LLM_API_KEY = 'your-api-key'" -ForegroundColor DarkGray
Write-Host "     (or run 'blindspot setup' for interactive configuration)" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  2. Run a UX & accessibility audit:" -ForegroundColor Cyan
Write-Host "     blindspot --target https://example.com" -ForegroundColor DarkGray
Write-Host ""
Write-Host "For more information visit https://github.com/harshit-dev-on/BlindSpot" -ForegroundColor DarkGray
Write-Host "Supported models: Gemini, OpenAI, Claude, OpenRouter, Ollama" -ForegroundColor DarkGray
Write-Host "Join our community https://github.com/harshit-dev-on/BlindSpot" -ForegroundColor DarkGray
Write-Host ""
Write-Host "→ Run refreshenv or open a new terminal" -ForegroundColor Yellow
Write-Host ""
