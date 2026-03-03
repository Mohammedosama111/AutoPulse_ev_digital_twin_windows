@echo off
title Electric Vehicle Digital Twin - Parameter Configuration Interface
color 0A

echo.
echo ================================================================
echo    Electric Vehicle Digital Twin - Web Interface Launcher
echo ================================================================
echo.
echo Starting the EV Digital Twin with Parameter Configuration...
echo.

cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7+ and try again
    echo.
    pause
    exit /b 1
)

REM Launch the web interface
echo Launching web interface...
python launch_with_parameters.py

echo.
echo Web interface stopped.
pause 