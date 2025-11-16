Thank you. @echo off
REM Quick server restart script after applying fixes

echo ====================================================================
echo JARVIS:LAW - SERVER RESTART (After Critical Fixes)
echo ====================================================================
echo.

echo [1] Stopping existing server...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :9000 ^| findstr LISTENING') do (
    echo Killing process %%a
    taskkill /F /PID %%a 2>nul
)
timeout /t 2 /nobreak >nul

echo.
echo [2] Verifying port is free...
netstat -ano | findstr :9000 | findstr LISTENING
if errorlevel 1 (
    echo ✅ Port 9000 is free
) else (
    echo ❌ Port still in use, trying again...
    timeout /t 3 /nobreak >nul
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :9000 ^| findstr LISTENING') do taskkill /F /PID %%a 2>nul
)

echo.
echo [3] Starting server with fixes applied...
echo.
echo ====================================================================
echo FIXES APPLIED:
echo ✅ JSON serialization error - FIXED
echo ✅ SEC filing download URLs - FIXED
echo ====================================================================
echo.

REM Start the test server
python test_server.py

pause

