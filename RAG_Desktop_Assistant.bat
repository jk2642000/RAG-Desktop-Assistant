@echo off
title RAG Desktop Assistant Launcher
echo.
echo ========================================
echo   RAG Desktop Assistant Launcher
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" (
    echo [INFO] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if requirements are installed
if not exist "installed.flag" (
    echo [INFO] Installing requirements...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install requirements
        pause
        exit /b 1
    )
    echo. > installed.flag
)

REM Check for .env file
if not exist ".env" (
    echo [WARNING] .env file not found
    echo Please copy .env.example to .env and add your Gemini API key
    pause
)

REM Launch application
echo [INFO] Starting RAG Desktop Assistant...
python main.py

REM Deactivate virtual environment
deactivate

echo.
echo Application closed. Press any key to exit...
pause >nul