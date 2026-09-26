@echo off
rem ============================================================
rem  System Configuration Comparison Tool - Windows launcher
rem  Double-click this file: it sets up everything automatically.
rem ============================================================
setlocal
title System Configuration Comparison Tool
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo.
    echo  Python 3 was not found on this computer.
    echo  Install it from https://www.python.org/downloads/
    echo  (tick "Add python.exe to PATH" during installation) and retry.
    echo.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo.
    echo  First run - setting up a virtual environment...
    echo.
    python -m venv .venv
    if errorlevel 1 (
        echo  Could not create the virtual environment.
        pause
        exit /b 1
    )
    ".venv\Scripts\python.exe" -m pip install --upgrade pip >nul
    echo  Installing dependencies (psutil, customtkinter)...
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo  Dependency installation failed. Check your internet
        echo  connection and run this file again.
        pause
        exit /b 1
    )
    echo.
    echo  Setup complete.
    echo.
)

".venv\Scripts\python.exe" main.py

echo.
pause
