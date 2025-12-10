#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
    EXECUTE NIKE UNIFIED ANALYSIS - ONE-CLICK PRODUCTION RUNNER
═══════════════════════════════════════════════════════════════════════════════

This is the main entry point for running comprehensive Nike 2019 forensic analysis.
It ensures all components work together properly and generates complete reports.

WHAT THIS SCRIPT DOES:
1. Validates environment and dependencies
2. Runs complete 13-phase unified forensic analysis
3. Generates comprehensive markdown AND JSON reports
4. Creates both structured output directory AND flat root files
5. Provides detailed progress feedback

EXPECTED OUTPUT:
- Structured directory: output/NIKE_Inc_2019_FORENSIC_ANALYSIS_YYYYMMDD_HHMMSS/
  - FORENSIC_REPORT.md (comprehensive markdown report)
  - executive_summary.md
  - machine_readable/violations.json
  - machine_readable/summary.json
  - evidence/chain_of_custody.json
  - appendices/methodology.md

- Root directory flat files (backwards compatibility):
  - NIKE_Inc_2019_FORENSIC_ANALYSIS_YYYYMMDD_HHMMSS.md
  - NIKE_Inc_2019_FORENSIC_ANALYSIS_YYYYMMDD_HHMMSS.json

═══════════════════════════════════════════════════════════════════════════════
"""

import asyncio
import sys
import logging
from pathlib import Path
from datetime import datetime

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

def print_banner():
    """Print startup banner."""
    print("\n" + "="*80)
    print("   EXECUTE NIKE UNIFIED ANALYSIS")
    print("   Complete Forensic Analysis System")
    print("="*80)
    print(f"\n   Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

def check_dependencies():
    """Check and report on critical dependencies."""
    print("  Checking dependencies...")
    
    missing = []
    available = []
    
    # Check critical imports
    try:
        import dotenv
        available.append("python-dotenv")
    except ImportError:
        missing.append("python-dotenv")
    
    try:
        import aiohttp
        available.append("aiohttp")
    except ImportError:
        missing.append("aiohttp")
    
    try:
        import aiofiles
        available.append("aiofiles")
    except ImportError:
        missing.append("aiofiles")
    
    try:
        import numpy
        available.append("numpy")
    except ImportError:
        missing.append("numpy")
    
    try:
        import pandas
        available.append("pandas")
    except ImportError:
        missing.append("pandas")
    
    # Report status
    if missing:
        print(f"  ⚠ Missing dependencies (advanced features unavailable): {', '.join(missing)}")
        print(f"  ✓ Available dependencies: {', '.join(available)}")
        print(f"\n  NOTE: Analysis will run in baseline mode (still comprehensive!)")
        print(f"  To enable all features, install: pip install {' '.join(missing)}")
    else:
        print(f"  ✓ All dependencies available - full unified mode enabled")
    
    print()
    return len(missing) == 0

def check_api_keys():
    """Check if API keys are configured."""
    print("  Checking API configuration...")
    
    try:
        from dotenv import load_dotenv
        import os
        
        load_dotenv()
        
        # Check for SEC API key (optional but recommended)
        sec_key = os.getenv('SEC_API_KEY')
        if sec_key:
            print(f"  ✓ SEC API key configured")
        else:
            print(f"  ℹ SEC API key not found (rate limits may apply)")
        
        # Check for AI API keys (optional for enhanced analysis)
        openai_key = os.getenv('OPENAI_API_KEY')
        anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        
        if openai_key or anthropic_key:
            print(f"  ✓ AI API keys available (enhanced analysis enabled)")
        else:
            print(f"  ℹ AI API keys not configured (basic analysis only)")
        
    except Exception as e:
        print(f"  ⚠ Could not check API keys: {e}")
    
    print()

async def run_nike_analysis():
    """Run the complete Nike 2019 analysis."""
    print("  Initializing analysis system...")
    print()
    
    # Import the main forensic system
    try:
        from jlaw_forensic import CompleteUnifiedForensicSystem
        
        # Initialize system
        system = CompleteUnifiedForensicSystem(output_dir="output")
        
        # Run analysis with Nike 2019 parameters
        print("  Starting Nike 2019 comprehensive analysis...")
        print("  This may take 5-15 minutes depending on your connection speed.")
        print()
        
        results, output_path = await system.execute_complete_analysis(
            ticker="NKE",
            cik="0000320187",
            year=2019,
            company_name="NIKE, Inc.",
            verbose=False,  # Set to True for detailed logging
            filing_types=None,  # Analyze all filing types
            no_report=False
        )
        
        print("\n" + "="*80)
        print("  ✅ ANALYSIS COMPLETE!")
        print("="*80)
        print(f"\n  RESULTS SUMMARY:")
        print(f"    Filings Analyzed:      {results['filings_analyzed']}")
        print(f"    Violations Identified: {results['total_violations']}")
        print(f"    Criminal Referrals:    {results['criminal_referrals']}")
        print(f"    Estimated Damages:     ${results['total_damages']:,.2f}")
        
        print(f"\n  REPORTS GENERATED:")
        print(f"    Main Directory:  {output_path}")
        print(f"    Main Report:     {output_path / 'FORENSIC_REPORT.md'}")
        
        # Check for root-level files
        import glob
        root_md_files = glob.glob(str(PROJECT_ROOT / "NIKE_Inc_2019_FORENSIC_ANALYSIS_*.md"))
        root_json_files = glob.glob(str(PROJECT_ROOT / "NIKE_Inc_2019_FORENSIC_ANALYSIS_*.json"))
        
        if root_md_files:
            latest_md = sorted(root_md_files)[-1]
            print(f"    Root MD File:    {Path(latest_md).name}")
        
        if root_json_files:
            latest_json = sorted(root_json_files)[-1]
            print(f"    Root JSON File:  {Path(latest_json).name}")
        
        print(f"\n  All reports contain comprehensive analysis including:")
        print(f"    • Executive summary with key findings")
        print(f"    • Detailed violation analysis for each filing")
        print(f"    • Statutory framework and legal citations")
        print(f"    • Evidence chain and source documents")
        print(f"    • Machine-readable data for further processing")
        
        print("\n" + "="*80)
        
        return 0
        
    except Exception as e:
        print("\n" + "="*80)
        print(f"  ❌ ERROR: Analysis failed")
        print("="*80)
        print(f"\n  {str(e)}")
        
        import traceback
        print(f"\n  FULL ERROR DETAILS:")
        traceback.print_exc()
        
        print(f"\n  TROUBLESHOOTING:")
        print(f"    1. Check that all dependencies are installed: pip install -r requirements.txt")
        print(f"    2. Verify your internet connection (needed for SEC EDGAR access)")
        print(f"    3. Check the log files for more details")
        print(f"    4. Try running with --verbose for detailed logging")
        
        return 1

def main():
    """Main entry point."""
    print_banner()
    
    # Pre-flight checks
    all_deps = check_dependencies()
    check_api_keys()
    
    if not all_deps:
        print("  ℹ Some dependencies are missing, but analysis will continue in baseline mode.")
        print("  Baseline mode still produces comprehensive, production-quality reports.")
        print()
    
    # Run analysis
    try:
        exit_code = asyncio.run(run_nike_analysis())
        
        print(f"\n  Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\n\n  ⚠ Analysis interrupted by user")
        print()
        sys.exit(130)
        
    except Exception as e:
        print(f"\n\n  ❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
