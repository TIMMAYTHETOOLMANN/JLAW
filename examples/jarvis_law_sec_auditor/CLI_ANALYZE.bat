@echo off
REM ========================================
REM JARVIS:LAW Direct CLI Analysis Launcher
REM GUI Bypass - Raw Forensic Analysis
REM ========================================

echo.
echo ================================================================================
echo JARVIS:LAW - DIRECT CLI FORENSIC ANALYSIS (GUI BYPASS)
echo ================================================================================
echo.
echo This script executes raw forensic analysis directly from CLI
echo No GUI configuration required
echo.

if "%1"=="" (
    echo Usage: CLI_ANALYZE.bat [TICKER or CIK] [FORM_TYPE] [YEARS]
    echo.
    echo Examples:
    echo   CLI_ANALYZE.bat NKE
    echo   CLI_ANALYZE.bat TSLA 4 5
    echo   CLI_ANALYZE.bat AAPL 10-K 3
    echo   CLI_ANALYZE.bat 0000320187
    echo.
    echo Common Tickers:
    echo   NKE    - Nike
    echo   TSLA   - Tesla
    echo   AAPL   - Apple
    echo   MSFT   - Microsoft
    echo   GOOGL  - Google
    echo   AMZN   - Amazon
    echo   META   - Meta/Facebook
    echo.
    pause
    exit /b 1
)

echo Target: %1
if not "%2"=="" echo Form: %2
if not "%3"=="" echo Years: %3
echo.
echo Starting analysis...
echo.

python direct_cli_analysis.py %1 %2 %3

echo.
pause

