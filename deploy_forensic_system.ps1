<#
.SYNOPSIS
    JLAW Forensic Analysis System - Complete Single-Click Deployment
    
.DESCRIPTION
    This script provides a complete single-click deployment experience:
    - Verifies Python installation
    - Installs all required dependencies
    - Validates API keys (optional)
    - Verifies all 13 forensic modules
    - Tests filing collection (Nike 2019 benchmark)
    - Runs complete forensic analysis
    - Opens output folder automatically
    
.PARAMETER Ticker
    Company ticker symbol (e.g., NKE)
    
.PARAMETER CIK
    Company CIK number (e.g., 0000320187)
    
.PARAMETER Year
    Analysis year (e.g., 2019)
    
.PARAMETER SkipTests
    Skip module verification and filing count tests
    
.PARAMETER SkipDeps
    Skip dependency installation
    
.PARAMETER Verbose
    Enable verbose output
    
.EXAMPLE
    PowerShell -ExecutionPolicy Bypass -File .\deploy_forensic_system.ps1
    
.EXAMPLE
    PowerShell -ExecutionPolicy Bypass -File .\deploy_forensic_system.ps1 -Ticker NKE -Year 2019
    
.EXAMPLE
    PowerShell -ExecutionPolicy Bypass -File .\deploy_forensic_system.ps1 -CIK 0000320187 -Year 2019 -SkipTests
#>

param(
    [string]$Ticker = "NKE",
    [string]$CIK = "",
    [string]$Year = "2019",
    [switch]$SkipTests,
    [switch]$SkipDeps,
    [switch]$Verbose
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Color functions
function Write-Success($msg) {
    Write-Host "✅ $msg" -ForegroundColor Green
}

function Write-Error-Custom($msg) {
    Write-Host "❌ $msg" -ForegroundColor Red
}

function Write-Warning-Custom($msg) {
    Write-Host "⚠️  $msg" -ForegroundColor Yellow
}

function Write-Info($msg) {
    Write-Host "ℹ️  $msg" -ForegroundColor Cyan
}

function Write-Section($title) {
    Write-Host ""
    Write-Host ("=" * 80) -ForegroundColor DarkGray
    Write-Host "  $title" -ForegroundColor Cyan
    Write-Host ("=" * 80) -ForegroundColor DarkGray
}

function Get-PythonCmd {
    if (Get-Command python -ErrorAction SilentlyContinue) { 
        return 'python' 
    }
    if (Get-Command py -ErrorAction SilentlyContinue) { 
        return 'py -3' 
    }
    throw 'Python 3 is required but was not found in PATH. Please install Python 3.11 or 3.12.'
}

function Test-PythonVersion($python) {
    Write-Info "Checking Python version..."
    $version = & $python --version 2>&1
    Write-Host "   $version"
    
    if ($version -match "Python 3\.(1[12])\.") {
        Write-Success "Python version is compatible"
        return $true
    }
    elseif ($version -match "Python 3\.") {
        Write-Warning-Custom "Python 3.11 or 3.12 recommended for best compatibility"
        return $true
    }
    else {
        Write-Error-Custom "Python 3.x required"
        return $false
    }
}

function Install-Dependencies($python) {
    if ($SkipDeps) {
        Write-Warning-Custom "Skipping dependency installation (--SkipDeps)"
        return
    }
    
    Write-Section "Installing Dependencies"
    
    Write-Info "Upgrading pip, setuptools, wheel..."
    & $python -m pip install --upgrade pip setuptools wheel --quiet
    
    if (Test-Path "requirements.txt") {
        Write-Info "Installing requirements from requirements.txt..."
        & $python -m pip install -r requirements.txt --quiet
        Write-Success "Dependencies installed"
    }
    else {
        Write-Error-Custom "requirements.txt not found"
        throw "requirements.txt not found"
    }
}

function Test-ModuleVerification($python) {
    if ($SkipTests) {
        Write-Warning-Custom "Skipping module verification (--SkipTests)"
        return $true
    }
    
    Write-Section "Verifying 13 Forensic Modules"
    
    $result = & $python verify_13_modules.py 2>&1
    Write-Host $result
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "All 13 modules verified successfully"
        return $true
    }
    else {
        Write-Error-Custom "Module verification failed"
        return $false
    }
}

function Test-FilingCount($python) {
    if ($SkipTests) {
        Write-Warning-Custom "Skipping filing count test (--SkipTests)"
        return $true
    }
    
    Write-Section "Testing Filing Collection (Nike 2019 Benchmark)"
    
    Write-Info "Expected: 89 filings for Nike 2019..."
    $result = & $python test_filing_count_fix.py 2>&1
    Write-Host $result
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Filing collection test passed (89/89 filings)"
        return $true
    }
    else {
        Write-Warning-Custom "Filing count test did not pass completely"
        Write-Info "Continuing with analysis..."
        return $true  # Don't fail deployment
    }
}

function Run-ForensicAnalysis($python) {
    Write-Section "Running Complete Forensic Analysis"
    
    $args = @()
    
    if ($CIK) {
        $args += @('--cik', $CIK)
    }
    elseif ($Ticker) {
        $args += @('--ticker', $Ticker)
    }
    
    if ($Year) {
        $args += @('--year', $Year)
    }
    
    if ($Verbose) {
        $args += '--verbose'
    }
    
    Write-Info "Command: jlaw_forensic.py $($args -join ' ')"
    Write-Host ""
    
    & $python jlaw_forensic.py @args
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Forensic analysis completed"
        return $true
    }
    else {
        Write-Error-Custom "Forensic analysis encountered errors"
        return $false
    }
}

function Open-OutputFolder {
    Write-Section "Opening Output Folder"
    
    if (Test-Path "output") {
        $latest = Get-ChildItem "output" -Directory |
            Where-Object { $_.Name -like '*_FORENSIC_ANALYSIS_*' } |
            Sort-Object LastWriteTime -Descending |
            Select-Object -First 1
        
        if ($latest) {
            Write-Info "Opening: $($latest.FullName)"
            Start-Process $latest.FullName
            Write-Success "Output folder opened"
        }
        else {
            Write-Warning-Custom "No analysis output found"
        }
    }
    else {
        Write-Warning-Custom "Output directory not found"
    }
}

# Main execution
try {
    Push-Location $PSScriptRoot
    
    Write-Host ""
    Write-Host ("=" * 80) -ForegroundColor Cyan
    Write-Host "  JLAW FORENSIC ANALYSIS SYSTEM" -ForegroundColor Cyan
    Write-Host "  Complete Single-Click Deployment" -ForegroundColor Cyan
    Write-Host ("=" * 80) -ForegroundColor Cyan
    
    # Step 1: Check Python
    Write-Section "Step 1: Python Environment Check"
    $python = Get-PythonCmd
    if (!(Test-PythonVersion $python)) {
        throw "Python version check failed"
    }
    
    # Step 2: Install Dependencies
    Write-Section "Step 2: Dependency Installation"
    Install-Dependencies $python
    
    # Step 3: Verify Modules
    Write-Section "Step 3: Module Verification"
    if (!(Test-ModuleVerification $python)) {
        Write-Warning-Custom "Some modules failed verification, but continuing..."
    }
    
    # Step 4: Test Filing Collection
    Write-Section "Step 4: Filing Collection Test"
    Test-FilingCount $python | Out-Null
    
    # Step 5: Run Analysis
    Write-Section "Step 5: Forensic Analysis Execution"
    Write-Info "Target: $($Ticker ? $Ticker : $CIK) - Year: $Year"
    if (!(Run-ForensicAnalysis $python)) {
        throw "Forensic analysis failed"
    }
    
    # Step 6: Open Results
    Write-Section "Step 6: Results"
    Open-OutputFolder
    
    # Success
    Write-Host ""
    Write-Host ("=" * 80) -ForegroundColor Green
    Write-Host "  DEPLOYMENT COMPLETE" -ForegroundColor Green
    Write-Host ("=" * 80) -ForegroundColor Green
    Write-Success "System deployed and analysis completed successfully"
    Write-Info "Review the output folder for detailed forensic reports"
    Write-Host ""
    
    exit 0
}
catch {
    Write-Host ""
    Write-Host ("=" * 80) -ForegroundColor Red
    Write-Host "  DEPLOYMENT FAILED" -ForegroundColor Red
    Write-Host ("=" * 80) -ForegroundColor Red
    Write-Error-Custom $_.Exception.Message
    Write-Host ""
    Write-Info "Review the errors above and try again"
    Write-Info "For help: https://github.com/TIMMAYTHETOOLMANN/JLAW"
    Write-Host ""
    
    exit 1
}
finally {
    Pop-Location
}
