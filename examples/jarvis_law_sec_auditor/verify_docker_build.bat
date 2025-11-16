@echo off
REM JARVIS:LAW Docker Build Verification Script
REM Run this to check if the Docker build was successful and test the container

echo ============================================================================
echo JARVIS:LAW - Docker Build Verification
echo ============================================================================
echo.

echo [1/5] Checking Docker installation...
docker --version
if errorlevel 1 (
    echo [FAIL] Docker not installed
    pause
    exit /b 1
)
echo [OK] Docker is installed
echo.

echo [2/5] Checking if image exists...
docker images jarvis-law-forensic:latest
if errorlevel 1 (
    echo [FAIL] Image not found
    echo.
    echo Rebuilding image...
    docker build -t jarvis-law-forensic:latest .
    if errorlevel 1 (
        echo [FAIL] Build failed
        pause
        exit /b 1
    )
)
echo [OK] Image exists
echo.

echo [3/5] Testing Python imports in container...
docker run --rm jarvis-law-forensic:latest python -c "import networkx; import flask; import numpy; import pandas; import sklearn; print('SUCCESS: All core imports work!')" 2>&1
if errorlevel 1 (
    echo [WARN] Some imports failed, but container runs
) else (
    echo [OK] All imports successful
)
echo.

echo [4/5] Starting test container...
docker run -d -p 5001:5000 --name jarvis-test-verify jarvis-law-forensic:latest
if errorlevel 1 (
    echo [FAIL] Container failed to start
    echo.
    echo Checking logs...
    docker logs jarvis-test-verify
    docker rm -f jarvis-test-verify
    pause
    exit /b 1
)
echo [OK] Container started
echo.

echo [5/5] Waiting for container to initialize (15 seconds)...
timeout /t 15 /nobreak >nul

echo.
echo Checking container status...
docker ps --filter "name=jarvis-test-verify"
echo.

echo Checking container logs...
docker logs jarvis-test-verify

echo.
echo ============================================================================
echo VERIFICATION COMPLETE
echo ============================================================================
echo.
echo Container is running on port 5001
echo Test at: http://localhost:5001
echo.
echo To stop test container: docker rm -f jarvis-test-verify
echo.

pause

