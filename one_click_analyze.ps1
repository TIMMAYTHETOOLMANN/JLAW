<#
 JLAW Unified Forensic Analysis — One-Click Runner (Windows)

 This PowerShell script provides a guided, single‑click experience to:
  - Check Python availability
  - Install required dependencies
  - Optionally validate API keys
  - Prompt for analysis parameters (Ticker/CIK, Year or Date Range, Filing Types)
  - Run the full 13‑phase unified pipeline
  - Open the generated output folder automatically

 Interactive usage:
   PowerShell -ExecutionPolicy Bypass -File .\one_click_analyze.ps1

 Non‑interactive (CI‑friendly) usage:
   PowerShell -ExecutionPolicy Bypass -File .\one_click_analyze.ps1 `
     -Ticker NKE -Year 2019 -OutputDir output -Verbose `
     -SkipDeps:$false -SkipKeyCheck:$false

 Supported parameters (non‑interactive):
   -Ticker <string> | -CIK <string>
   -Year <int> OR -StartDate <YYYY-MM-DD> -EndDate <YYYY-MM-DD>
   -FilingTypes <"10-K,10-Q,8-K,4,DEF 14A"> (default: all)
   -OutputDir <path> (default: output)
   -Verbose (switch; default: ON if not supplied)
   -NoReport (switch; default: OFF)
#>

param(
  [switch]$SkipDeps,
  [switch]$SkipKeyCheck,
  # Non-interactive inputs (optional)
  [string]$Ticker,
  [string]$CIK,
  [string]$Year,
  [string]$StartDate,
  [string]$EndDate,
  [string]$FilingTypes = 'all',
  [string]$OutputDir = 'output',
  [switch]$Verbose,
  [switch]$NoReport
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Section($title) {
  Write-Host ('=' * 80) -ForegroundColor DarkGray
  Write-Host "  $title" -ForegroundColor Cyan
  Write-Host ('=' * 80) -ForegroundColor DarkGray
}

function Get-PythonCmd {
  if (Get-Command python -ErrorAction SilentlyContinue) { return 'python' }
  if (Get-Command py -ErrorAction SilentlyContinue) { return 'py -3' }
  throw 'Python 3 is required but was not found in PATH.'
}

function Ensure-DepInstall($python) {
  if ($SkipDeps) { Write-Host 'Skipping dependency installation (--SkipDeps)'; return }
  Write-Section 'Installing Dependencies'
  & $python -m pip install --upgrade pip setuptools wheel | Write-Host
  if (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'requirements.txt')) {
    & $python -m pip install -r (Join-Path $PSScriptRoot 'requirements.txt')
  } else {
    Write-Warning 'requirements.txt not found — continuing.'
  }
}

function Validate-Keys($python) {
  if ($SkipKeyCheck) { Write-Host 'Skipping API key validation (--SkipKeyCheck)'; return }
  if (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'verify_api_keys.py')) {
    Write-Section 'Validating API Keys (.env)'
    try {
      & $python (Join-Path $PSScriptRoot 'verify_api_keys.py')
    } catch {
      Write-Warning "Key validation encountered an issue: $($_.Exception.Message). Continuing."
    }
  }
}

function Prompt-Inputs {
  Write-Section 'JLAW Unified Forensic Analysis — Input Parameters'
  $ticker = Read-Host 'Ticker (e.g., NKE) [leave blank to use CIK]'
  $cik    = Read-Host 'CIK (10 digits, e.g., 0000320187) [leave blank to use Ticker]'
  if ([string]::IsNullOrWhiteSpace($ticker) -and [string]::IsNullOrWhiteSpace($cik)) {
    Write-Host 'You must provide either a Ticker or a CIK.' -ForegroundColor Yellow
    return Prompt-Inputs
  }

  $year = Read-Host 'Analysis Year (e.g., 2019) [leave blank for custom date range]'
  $startDate = ''
  $endDate = ''
  if ([string]::IsNullOrWhiteSpace($year)) {
    $startDate = Read-Host 'Start Date (YYYY-MM-DD)'
    $endDate   = Read-Host 'End Date (YYYY-MM-DD)'
  }

  $filingTypes = Read-Host 'Filing Types (comma-separated) or "all" for all [default: all]'
  if ([string]::IsNullOrWhiteSpace($filingTypes)) { $filingTypes = 'all' }

  $outDir = Read-Host 'Output directory [default: output]'
  if ([string]::IsNullOrWhiteSpace($outDir)) { $outDir = 'output' }

  $verboseAns = Read-Host 'Verbose mode? (Y/n) [default: Y]'
  $verbose = -not ($verboseAns -match '^[Nn]')

  $reportAns = Read-Host 'Generate full report stack? (Y/n) [default: Y]'
  $noReport = ($reportAns -match '^[Nn]')

  return [pscustomobject]@{
    Ticker = $ticker
    CIK = $cik
    Year = $year
    StartDate = $startDate
    EndDate = $endDate
    FilingTypes = $filingTypes
    OutputDir = $outDir
    Verbose = $verbose
    NoReport = $noReport
  }
}

function Build-Args($inputs) {
  $args = @()
  if (-not [string]::IsNullOrWhiteSpace($inputs.Ticker)) { $args += @('--ticker', $inputs.Ticker) }
  if (-not [string]::IsNullOrWhiteSpace($inputs.CIK))    { $args += @('--cik', $inputs.CIK) }
  if (-not [string]::IsNullOrWhiteSpace($inputs.Year))   { $args += @('--year', $inputs.Year) }
  else {
    if (-not [string]::IsNullOrWhiteSpace($inputs.StartDate)) { $args += @('--start-date', $inputs.StartDate) }
    if (-not [string]::IsNullOrWhiteSpace($inputs.EndDate))   { $args += @('--end-date', $inputs.EndDate) }
  }
  if (-not [string]::IsNullOrWhiteSpace($inputs.OutputDir)) { $args += @('--output-dir', $inputs.OutputDir) }
  if ($inputs.Verbose) { $args += '--verbose' }
  if ($inputs.NoReport) { $args += '--no-report' }
  if (-not [string]::IsNullOrWhiteSpace($inputs.FilingTypes) -and $inputs.FilingTypes.ToLower() -ne 'all') {
    $args += @('--filing-types', $inputs.FilingTypes)
  }
  return $args
}

function Open-LatestOutput($baseOut) {
  try {
    if (-not (Test-Path -LiteralPath $baseOut)) { return }
    $latest = Get-ChildItem -LiteralPath $baseOut -Directory |
      Where-Object { $_.Name -like '*_FORENSIC_ANALYSIS_*' } |
      Sort-Object LastWriteTime -Descending |
      Select-Object -First 1
    if ($latest) {
      Write-Host "Opening output: $($latest.FullName)" -ForegroundColor Green
      Start-Process $latest.FullName | Out-Null
    }
  } catch {
    Write-Warning "Could not open output folder: $($_.Exception.Message)"
  }
}

Push-Location $PSScriptRoot
try {
  Write-Section 'Environment Check'
  $python = Get-PythonCmd
  & $python --version

  Ensure-DepInstall -python $python
  Validate-Keys -python $python

  # Determine non-interactive mode if any of the data parameters were supplied
  $niKeys = @('Ticker','CIK','Year','StartDate','EndDate','FilingTypes','OutputDir','Verbose','NoReport') | Where-Object { $PSBoundParameters.ContainsKey($_) }
  $nonInteractive = $niKeys.Count -gt 0

  if ($nonInteractive) {
    # Build inputs object from provided parameters; apply sensible defaults
    $useVerbose = $true
    if ($PSBoundParameters.ContainsKey('Verbose')) {
      $useVerbose = $Verbose.IsPresent
    }
    $ft = $FilingTypes
    if ([string]::IsNullOrWhiteSpace($ft)) { $ft = 'all' }
    $out = $OutputDir
    if ([string]::IsNullOrWhiteSpace($out)) { $out = 'output' }

    $inputs = [pscustomobject]@{
      Ticker      = $Ticker
      CIK         = $CIK
      Year        = $Year
      StartDate   = $StartDate
      EndDate     = $EndDate
      FilingTypes = $ft
      OutputDir   = $out
      Verbose     = $useVerbose
      NoReport    = $NoReport.IsPresent
    }
  } else {
    $inputs = Prompt-Inputs
  }
  $args = Build-Args -inputs $inputs

  Write-Section 'Executing Unified Forensic Analysis'
  Write-Host "Command: jlaw_forensic.py $($args -join ' ')" -ForegroundColor DarkCyan
  & $python (Join-Path $PSScriptRoot 'jlaw_forensic.py') @args

  Open-LatestOutput -baseOut $inputs.OutputDir
  Write-Host 'Analysis complete.' -ForegroundColor Green
}
catch {
  Write-Error $_.Exception.Message
  exit 1
}
finally {
  Pop-Location
}
