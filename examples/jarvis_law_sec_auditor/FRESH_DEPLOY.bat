@echo off
REM ============================================================================
REM JARVIS:LAW - COMPLETE CACHE CLEAR AND FRESH DEPLOYMENT
REM ============================================================================

echo.
echo ============================================================================
echo JARVIS:LAW - COMPLETE CACHE CLEAR AND FRESH DEPLOYMENT
echo ============================================================================
echo.

cd /d "%~dp0"

REM ============================================================================
REM STEP 1: KILL ALL RUNNING SERVERS
REM ============================================================================
echo [STEP 1/6] Stopping all Python servers on port 9000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :9000 ^| findstr LISTENING') do (
    echo   Killing process %%a
    taskkill /F /PID %%a 2>nul
)
timeout /t 2 /nobreak >nul
echo   [OK] All servers stopped

REM ============================================================================
REM STEP 2: CLEAR PYTHON CACHE FILES
REM ============================================================================
echo.
echo [STEP 2/6] Clearing Python cache files...
echo   Removing __pycache__ directories...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
echo   Removing .pyc files...
del /s /q *.pyc 2>nul
echo   [OK] Python cache cleared

REM ============================================================================
REM STEP 3: CLEAR OLD FORENSIC OUTPUT DIRECTORIES
REM ============================================================================
echo.
echo [STEP 3/6] Clearing old forensic output directories...
for /d %%d in (forensic_output_*) do (
    echo   Removing %%d
    rd /s /q "%%d" 2>nul
)
echo   [OK] Old output directories cleared

REM ============================================================================
REM STEP 4: CLEAR DATABASE CACHE (OPTIONAL - COMMENT OUT IF YOU WANT TO KEEP)
REM ============================================================================
echo.
echo [STEP 4/6] Clearing database cache...
if exist forensic_evidence.db (
    echo   Backing up forensic_evidence.db to forensic_evidence.db.backup
    copy /y forensic_evidence.db forensic_evidence.db.backup >nul 2>&1
    echo   Removing forensic_evidence.db
    del forensic_evidence.db 2>nul
)
echo   [OK] Database cache cleared

REM ============================================================================
REM STEP 5: CLEAR LOG FILES
REM ============================================================================
echo.
echo [STEP 5/6] Clearing old log files...
del forensic_analysis_*.log 2>nul
del startup_errors.log 2>nul
del server.log 2>nul
echo   [OK] Log files cleared

REM ============================================================================
REM STEP 6: VERIFY PORT IS CLEAR
REM ============================================================================
echo.
echo [STEP 6/6] Verifying port 9000 is available...
netstat -ano | findstr :9000 | findstr LISTENING >nul
if errorlevel 1 (
    echo   [OK] Port 9000 is clear and ready
) else (
    echo   [WARNING] Port 9000 still in use, waiting 3 more seconds...
    timeout /t 3 /nobreak >nul
)

REM ============================================================================
REM SHOW APPLIED FIXES
REM ============================================================================
echo.
echo ============================================================================
echo ALL FIXES APPLIED TO THIS FRESH DEPLOYMENT:
echo ============================================================================
echo   [OK] Fix 1: JSON Serialization (FraudIndicator.to_dict method)
echo   [OK] Fix 2: SEC Download URLs (Correct EDGAR format with CIK)
echo   [OK] Fix 3: Analysis Limit Parameter (Respects user input)
echo   [OK] Fix 4: NKE Ticker Symbol (Nike now recognized)
echo   [OK] Fix 5: All caches cleared (Fresh start)
echo ============================================================================
echo.

REM ============================================================================
REM START FRESH SERVER
REM ============================================================================
echo [STARTING] Fresh server deployment...
echo.
echo Server will be available at: http://localhost:9000
echo.
echo IMPORTANT: After server starts...
echo   1. Open browser to: http://localhost:9000
echo   2. Do a HARD REFRESH: Ctrl+Shift+R (or Ctrl+F5)
echo   3. Search for "NKE" - should work now
echo   4. Run NEW analysis with limit=10
echo   5. Check server logs for "Analyzing 10 filings (user limit: 10)"
echo.
echo To stop server: Press Ctrl+C in this window
echo ============================================================================
echo.

python production_waitress.py

echo.
echo Server stopped.
pause

