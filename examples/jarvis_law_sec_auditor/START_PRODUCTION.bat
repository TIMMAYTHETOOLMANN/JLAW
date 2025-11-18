@echo off
REM JARVIS:LAW Production Server Launcher
REM Starts production-ready Waitress WSGI server on port 9000

echo ============================================================================
echo JARVIS:LAW FORENSIC ANALYSIS SYSTEM - PRODUCTION DEPLOYMENT
echo ============================================================================
echo.

REM Change to script directory
cd /d "%~dp0"

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found in PATH
    echo Please install Python 3.11+ and add to PATH
    pause
    exit /b 1
)

echo [OK] Python detected
echo.

REM Check if requirements are installed
python -c "import waitress" >nul 2>&1
if errorlevel 1 (
    echo [WARN] Installing required packages...
    pip install -r requirements_unified.txt
)

echo [OK] Dependencies verified
echo.

REM Start production server
echo [LAUNCH] Starting production server on port 9000...
echo.
echo Browser will open automatically to: http://localhost:9000
echo.
echo To stop server: Press Ctrl+C or close this window
echo ============================================================================
echo.

REM Open browser after 2 seconds
timeout /t 2 /nobreak >nul
start http://localhost:9000

REM Launch production server
python production_waitress.py

pause

