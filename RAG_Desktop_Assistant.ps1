# RAG Desktop Assistant PowerShell Launcher
param(
    [switch]$SkipChecks
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   RAG Desktop Assistant Launcher" -ForegroundColor Cyan  
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python installation
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[OK] Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.8+ from https://python.org" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Create virtual environment if it doesn't exist
if (-not (Test-Path "venv")) {
    Write-Host "[INFO] Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to create virtual environment" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# Activate virtual environment
Write-Host "[INFO] Activating virtual environment..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"

# Install requirements if not already installed
if (-not (Test-Path "installed.flag")) {
    Write-Host "[INFO] Installing requirements..." -ForegroundColor Yellow
    pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to install requirements" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
    New-Item -Path "installed.flag" -ItemType File | Out-Null
}

# Check for .env file
if (-not (Test-Path ".env")) {
    Write-Host "[WARNING] .env file not found" -ForegroundColor Yellow
    Write-Host "Please copy .env.example to .env and add your Gemini API key" -ForegroundColor Yellow
    if (-not $SkipChecks) {
        Read-Host "Press Enter to continue anyway"
    }
}

# Launch application
Write-Host "[INFO] Starting RAG Desktop Assistant..." -ForegroundColor Green
python main.py

Write-Host ""
Write-Host "Application closed." -ForegroundColor Cyan
if (-not $SkipChecks) {
    Read-Host "Press Enter to exit"
}