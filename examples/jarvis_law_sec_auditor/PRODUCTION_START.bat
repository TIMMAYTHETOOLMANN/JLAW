@echo off
REM ========================================
REM JARVIS:LAW Production Server Launcher
REM ========================================

echo.
echo ================================================================================
echo JARVIS:LAW FORENSIC ANALYSIS SYSTEM - PRODUCTION DEPLOYMENT
echo ================================================================================
echo.

REM Check if requirements are installed
echo [1/3] Verifying dependencies...
pip show flask >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Flask not found. Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies.
        pause
        exit /b 1
    )
) else (
    echo [OK] Dependencies verified.
)

echo.
echo [2/3] Checking environment configuration...
if not exist .env (
    echo [WARNING] .env file not found. Creating from template...
    echo OPENAI_API_KEY=your_openai_key_here > .env
    echo ANTHROPIC_API_KEY=your_anthropic_key_here >> .env
    echo [ACTION REQUIRED] Please edit .env file with your API keys.
    pause
)

echo.
echo [3/3] Starting production server...
echo.
python production_server.py

if errorlevel 1 (
    echo.
    echo [ERROR] Server failed to start. Check logs above.
    pause
    exit /b 1
)

