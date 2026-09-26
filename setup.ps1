<#
.SYNOPSIS
    Self-setup installer for Adaptive Resume AI Studio
    Installs Python dependencies, verifies LaTeX engine, registers custom icon,
    creates desktop shortcut, and launches the application.
#>

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   Adaptive Resume AI Studio - 1-Click Environment Setup  " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# 1. Check Python
Write-Host "[1/5] Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVer = & python --version 2>&1
    Write-Host "      Found: $pythonVer" -ForegroundColor Green
} catch {
    Write-Host "      ERROR: Python is not installed or not in PATH." -ForegroundColor Red
    Write-Host "      Please install Python 3.9+ from python.org and add it to PATH." -ForegroundColor Red
    Exit 1
}

# 2. Install Python Dependencies
Write-Host "[2/5] Installing Python dependencies (requirements.txt)..." -ForegroundColor Yellow
try {
    & python -m pip install -q -r requirements.txt
    Write-Host "      Dependencies installed successfully." -ForegroundColor Green
} catch {
    Write-Host "      Warning: Could not install all packages automatically. Retrying with --user..." -ForegroundColor Yellow
    & python -m pip install -q --user -r requirements.txt
}

# 3. Check LaTeX Compiler
Write-Host "[3/5] Checking LaTeX compilation engine..." -ForegroundColor Yellow
$hasCompiler = $false

try {
    $tectonicVer = & tectonic --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "      Found native Tectonic engine: $tectonicVer" -ForegroundColor Green
        $hasCompiler = $true
    }
} catch {}

if (-not $hasCompiler) {
    try {
        $wslTectonic = & wsl which tectonic 2>&1
        if ($LASTEXITCODE -eq 0 -and $wslTectonic) {
            Write-Host "      Found Tectonic via WSL: $wslTectonic" -ForegroundColor Green
            $hasCompiler = $true
        }
    } catch {}
}

if (-not $hasCompiler) {
    try {
        $pdflatexVer = & pdflatex --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "      Found pdfLaTeX engine." -ForegroundColor Green
            $hasCompiler = $true
        }
    } catch {}
}

if (-not $hasCompiler) {
    Write-Host "      Note: Neither Tectonic nor pdfLaTeX was detected in PATH." -ForegroundColor Yellow
    Write-Host "      (For automatic PDF compilation, install Tectonic via 'cargo install tectonic' or WSL)" -ForegroundColor Gray
}

# 4. Configure Icon and Desktop Shortcut
Write-Host "[4/5] Installing icon and creating Desktop shortcut..." -ForegroundColor Yellow
$iconsDir = Join-Path $env:USERPROFILE ".icons"
if (-not (Test-Path $iconsDir)) {
    New-Item -ItemType Directory -Path $iconsDir -Force | Out-Null
}

$sourceIco = Join-Path $ScriptDir "assets\adaptive_resume.ico"
$targetIco = Join-Path $iconsDir "adaptive_resume.ico"
if (Test-Path $sourceIco) {
    Copy-Item -Path $sourceIco -Destination $targetIco -Force
    Write-Host "      Copied dark-minimalist icon to: $targetIco" -ForegroundColor Green
} else {
    $targetIco = "$ScriptDir\assets\adaptive_resume.ico"
}

$desktopPath = [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::Desktop)
$shortcutPath = Join-Path $desktopPath "Adaptive Resume AI.lnk"
$vbsPath = Join-Path $ScriptDir "scripts\launch_studio.vbs"

try {
    $WshShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut($shortcutPath)
    $Shortcut.TargetPath = "wscript.exe"
    $Shortcut.Arguments = "`"$vbsPath`""
    $Shortcut.WorkingDirectory = "$ScriptDir"
    $Shortcut.IconLocation = "$targetIco, 0"
    $Shortcut.Description = "Adaptive Resume AI Studio - Local Executive Resume Tailoring"
    $Shortcut.Save()
    Write-Host "      Created Desktop shortcut: $shortcutPath" -ForegroundColor Green
} catch {
    Write-Host "      Warning: Could not create desktop shortcut automatically: $_" -ForegroundColor Yellow
}

# 5. Launch Application
Write-Host "[5/5] Launching Adaptive Resume AI Studio..." -ForegroundColor Yellow
try {
    Start-Process "wscript.exe" -ArgumentList "`"$vbsPath`""
    Write-Host ""
    Write-Host "Setup complete! Studio launched at: http://localhost:8765" -ForegroundColor Cyan
    Write-Host "A shortcut has also been placed on your Desktop." -ForegroundColor Cyan
} catch {
    Write-Host "      Starting directly via Python..." -ForegroundColor Yellow
    Start-Process "python" -ArgumentList "scripts\web_ui.py" -WorkingDirectory $ScriptDir
}
