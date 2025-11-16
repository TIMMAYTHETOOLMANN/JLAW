@echo off
REM ============================================================================
REM JARVIS:LAW - COMPLETE RESTART WITH ALL FIXES
REM ============================================================================

echo.
echo ============================================================================
echo JARVIS:LAW FORENSIC ANALYSIS SYSTEM - COMPLETE RESTART
echo ============================================================================
echo.

cd /d "%~dp0"

echo [STEP 1] Stopping any existing server...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :9000 ^| findstr LISTENING') do (
    echo   Killing process %%a
    taskkill /F /PID %%a 2>nul
)
timeout /t 3 /nobreak >nul

echo.
echo [STEP 2] Verifying port 9000 is clear...
netstat -ano | findstr :9000 | findstr LISTENING >nul
if errorlevel 1 (
    echo   [OK] Port 9000 is available
) else (
    echo   [WARNING] Port still in use, waiting...
    timeout /t 3 /nobreak >nul
)

echo.
echo ============================================================================
echo ALL FIXES APPLIED TO THIS SERVER:
echo ============================================================================
echo   [OK] Fix 1: JSON Serialization (FraudIndicator.to_dict method)
echo   [OK] Fix 2: SEC Download URLs (Correct EDGAR format with CIK)
echo   [OK] Fix 3: Analysis Limit Parameter (Respects user input)
echo   [OK] Fix 4: NKE Ticker Symbol (Nike now recognized)
echo ============================================================================
echo.

echo [STEP 3] Starting production server...
echo.
echo Server will be available at: http://localhost:9000
echo.
echo IMPORTANT INSTRUCTIONS:
echo   1. Wait for "Serving on http://0.0.0.0:9000" message
echo   2. Open browser to: http://localhost:9000
echo   3. Press F5 to refresh and clear old results
echo   4. Run a NEW analysis (the old results shown are from BEFORE fixes)
echo.
echo To stop server: Press Ctrl+C in this window
echo ============================================================================
echo.

python production_waitress.py

pause

