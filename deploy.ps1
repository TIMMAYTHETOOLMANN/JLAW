# JARVIS:LAW Production Deployment Script
# Deploys the complete forensic analysis system using Docker Compose

param(
    [switch]$Build,
    [switch]$Clean,
    [switch]$Stop
)

$ErrorActionPreference = "Stop"

# Colors for output
$Green = "Green"
$Yellow = "Yellow"
$Red = "Red"
$Cyan = "Cyan"

function Write-ColoredOutput {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

function Show-Header {
    Clear-Host
    Write-ColoredOutput "==================================================================================" $Cyan
    Write-ColoredOutput "JARVIS:LAW FORENSIC ANALYSIS SYSTEM - PRODUCTION DEPLOYMENT" $Cyan
    Write-ColoredOutput "==================================================================================" $Cyan
    Write-ColoredOutput ""
}

function Check-Prerequisites {
    Write-ColoredOutput "[CHECK] Verifying prerequisites..." $Yellow

    # Check if Docker is installed
    try {
        $dockerVersion = docker --version 2>$null
        Write-ColoredOutput "[OK] Docker detected: $dockerVersion" $Green
    } catch {
        Write-ColoredOutput "[ERROR] Docker not found. Please install Docker Desktop." $Red
        exit 1
    }

    # Check if Docker Compose is available
    try {
        $composeVersion = docker-compose --version 2>$null
        if ($composeVersion) {
            Write-ColoredOutput "[OK] Docker Compose detected: $composeVersion" $Green
        } else {
            $composeVersion = docker compose version 2>$null
            Write-ColoredOutput "[OK] Docker Compose V2 detected: $composeVersion" $Green
        }
    } catch {
        Write-ColoredOutput "[ERROR] Docker Compose not found." $Red
        exit 1
    }

    # Check if .env file exists
    if (!(Test-Path ".env")) {
        Write-ColoredOutput "[ERROR] .env file not found. Please create it with required environment variables." $Red
        exit 1
    }

    # Check if Docker daemon is running
    try {
        $null = docker info 2>$null
        Write-ColoredOutput "[OK] Docker daemon is running" $Green
    } catch {
        Write-ColoredOutput "[ERROR] Docker daemon is not running. Please start Docker Desktop." $Red
        exit 1
    }

    Write-ColoredOutput "[OK] Prerequisites verified" $Green
    Write-ColoredOutput ""
}

function Clean-System {
    Write-ColoredOutput "[CLEAN] Stopping and removing existing containers..." $Yellow

    try {
        docker-compose down --volumes --remove-orphans 2>$null
        Write-ColoredOutput "[OK] Clean shutdown completed" $Green
    } catch {
        Write-ColoredOutput "[WARN] No existing containers to clean" $Yellow
    }

    # Remove orphaned containers and images
    try {
        docker system prune -f 2>$null
        Write-ColoredOutput "[OK] System cleanup completed" $Green
    } catch {
        Write-ColoredOutput "[WARN] System cleanup skipped" $Yellow
    }

    Write-ColoredOutput ""
}

function Build-Images {
    Write-ColoredOutput "[BUILD] Building Docker images..." $Yellow

    try {
        docker-compose build --no-cache
        Write-ColoredOutput "[OK] Images built successfully" $Green
    } catch {
        Write-ColoredOutput "[ERROR] Failed to build images: $($_.Exception.Message)" $Red
        exit 1
    }

    Write-ColoredOutput ""
}

function Deploy-System {
    Write-ColoredOutput "[DEPLOY] Starting forensic analysis system..." $Yellow

    try {
        docker-compose up -d
        Write-ColoredOutput "[OK] System deployment initiated" $Green
    } catch {
        Write-ColoredOutput "[ERROR] Failed to deploy system: $($_.Exception.Message)" $Red
        exit 1
    }

    Write-ColoredOutput ""
}

function Wait-ForServices {
    Write-ColoredOutput "[WAIT] Waiting for services to be healthy..." $Yellow

    $services = @("postgres", "redis", "kafka", "minio", "forensic_app", "web_server")
    $maxWait = 300  # 5 minutes
    $waited = 0

    foreach ($service in $services) {
        Write-ColoredOutput "  Waiting for $service..." $Yellow

        while ($waited -lt $maxWait) {
            try {
                $status = docker-compose ps $service --format "table {{.Status}}"
                if ($status -match "healthy|running") {
                    Write-ColoredOutput "  [OK] $service is ready" $Green
                    break
                }
            } catch {
                # Service might not be up yet
            }

            Start-Sleep -Seconds 5
            $waited += 5
        }

        if ($waited -ge $maxWait) {
            Write-ColoredOutput "  [WARN] $service may not be fully ready yet" $Yellow
        }
    }

    Write-ColoredOutput ""
}

function Show-Status {
    Write-ColoredOutput "[STATUS] Service Status:" $Cyan
    docker-compose ps

    Write-ColoredOutput ""
    Write-ColoredOutput "[ACCESS] System Endpoints:" $Cyan
    Write-ColoredOutput "  Web Interface: http://localhost:3000" $Green
    Write-ColoredOutput "  API Health:    http://localhost:3000/health" $Green
    Write-ColoredOutput "  Forensic API:  http://localhost:8000" $Green
    Write-ColoredOutput "  MinIO Console: http://localhost:9001" $Green
    Write-ColoredOutput "  PostgreSQL:    localhost:5432" $Green
    Write-ColoredOutput "  Redis:         localhost:6379" $Green
    Write-ColoredOutput "  Kafka:         localhost:9092" $Green
    Write-ColoredOutput ""
}

function Stop-System {
    Write-ColoredOutput "[STOP] Stopping forensic analysis system..." $Yellow

    try {
        docker-compose down
        Write-ColoredOutput "[OK] System stopped successfully" $Green
    } catch {
        Write-ColoredOutput "[ERROR] Failed to stop system: $($_.Exception.Message)" $Red
        exit 1
    }

    Write-ColoredOutput ""
}

# Main execution
Show-Header

if ($Stop) {
    Stop-System
    exit 0
}

if ($Clean) {
    Clean-System
}

Check-Prerequisites

if ($Build) {
    Build-Images
}

Deploy-System
Wait-ForServices
Show-Status

Write-ColoredOutput "==================================================================================" $Cyan
Write-ColoredOutput "DEPLOYMENT COMPLETE - JARVIS:LAW FORENSIC SYSTEM OPERATIONAL" $Green
Write-ColoredOutput "==================================================================================" $Cyan
Write-ColoredOutput ""
Write-ColoredOutput "Next steps:" $Yellow
Write-ColoredOutput "  1. Open http://localhost:3000 in your browser" $White
Write-ColoredOutput "  2. Check API health at http://localhost:3000/health" $White
Write-ColoredOutput "  3. Access backend API at http://localhost:8000" $White
Write-ColoredOutput "  4. MinIO console at http://localhost:9001" $White
Write-ColoredOutput ""
Write-ColoredOutput "To stop the system: .\deploy.ps1 -Stop" $Yellow
Write-ColoredOutput "To rebuild: .\deploy.ps1 -Build" $Yellow
Write-ColoredOutput "To clean restart: .\deploy.ps1 -Clean" $Yellow
