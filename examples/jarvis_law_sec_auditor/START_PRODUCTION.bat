@echo off
REM JARVIS:LAW Production Server Launcher
REM Complete cold-start deployment including Docker services and Python server

echo ============================================================================
echo JARVIS:LAW FORENSIC ANALYSIS SYSTEM - PRODUCTION DEPLOYMENT
echo ============================================================================
echo.

REM Change to script directory
cd /d "%~dp0"

REM Check Docker installation
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker not found. Please install Docker Desktop.
    pause
    exit /b 1
)

echo [OK] Docker detected
echo.

REM Check if Docker daemon is running
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker daemon is not running. Please start Docker Desktop.
    pause
    exit /b 1
)

echo [OK] Docker daemon is running
echo.

REM Start Docker services
echo [DOCKER] Starting Docker services...
docker-compose up -d
if errorlevel 1 (
    echo [ERROR] Failed to start Docker services
    pause
    exit /b 1
)

echo [OK] Docker services started
echo.

REM Wait for services to be healthy
echo [WAIT] Waiting for services to be healthy...
timeout /t 10 /nobreak >nul

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
    echo [INSTALL] Installing required packages...
    pip install -r requirements_unified.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install requirements
        pause
        exit /b 1
    )
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

REM Open browser after 5 seconds
timeout /t 5 /nobreak >nul
start http://localhost:9000

REM Launch production server
python production_waitress.py

pause
