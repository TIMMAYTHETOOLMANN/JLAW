@echo off
echo ====================================================================
echo JARVIS:LAW - Starting Test Server
echo ====================================================================
echo.

cd /d "%~dp0"

echo [1] Checking Python...
python --version
if errorlevel 1 (
    echo [ERROR] Python not found
    pause
    exit /b 1
)
echo.

echo [2] Starting test server on port 9000...
echo.
echo Server will be available at: http://localhost:9000
echo Press Ctrl+C to stop the server
echo.
echo ====================================================================
echo.

python test_server.py

echo.
echo Server stopped.
pause

