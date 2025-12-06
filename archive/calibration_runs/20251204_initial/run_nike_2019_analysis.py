"""
NIKE 2019 FORENSIC ANALYSIS - PRODUCTION RUN
=============================================
This script runs the complete Nike 2019 SEC forensic analysis.

Target: All 89 Nike SEC filings from 2019
Expected: 54+ violations detected
Runtime: 5-10 minutes (with SEC rate limiting)
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Import the production runner
from nike_2019_production_run import run_nike_2019_production

async def main():
    """Main execution"""
    print("\n" + "="*80)
    print("STARTING NIKE 2019 FORENSIC ANALYSIS")
    print("="*80)
    print("\nThis will:")
    print("  1. Collect all 89 Nike SEC filings from 2019")
    print("  2. Analyze Form 4s for violations (late filings, zero-dollar transactions)")
    print("  3. Generate comprehensive violation report")
    print("  4. Save results to JSON file")
    print("\nExpected runtime: 5-10 minutes with SEC rate limiting")
    print("="*80)
    print("\nStarting analysis...\n")
    
    try:
        result = await run_nike_2019_production()
        
        print("\n" + "="*80)
        if result:
            print("✅ ANALYSIS COMPLETED SUCCESSFULLY")
            print("="*80)
            print("\nResults have been saved. Check the output files for details.")
            return 0
        else:
            print("⚠️ ANALYSIS COMPLETED BUT DID NOT MEET BENCHMARK")
            print("="*80)
            return 1
            
    except Exception as e:
        print("\n" + "="*80)
        print(f"❌ ERROR DURING ANALYSIS: {e}")
        print("="*80)
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    import logging
    
    # Set logging to WARNING to reduce noise
    logging.basicConfig(
        level=logging.WARNING,
        format='%(levelname)s: %(message)s'
    )
    
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

