#!/usr/bin/env python3
"""
Test script to verify that the filing count fix works correctly.
This should retrieve all 89 Nike 2019 filings.
"""

import asyncio
import sys
from pathlib import Path

# Setup paths
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from jlaw_production_forensic import UnifiedForensicAnalyzer


async def test_filing_count():
    """Test that we fetch all 89 Nike 2019 filings."""
    print("=" * 80)
    print("TESTING FILING COUNT FIX")
    print("=" * 80)
    print("\nTarget: Nike 2019")
    print("Expected: 89 filings")
    print()
    
    # Initialize analyzer
    analyzer = UnifiedForensicAnalyzer(
        cik="0000320187",
        company_name="NIKE, Inc."
    )
    
    try:
        # Fetch filings
        filings = await analyzer.fetch_all_filings(
            start_date="2019-01-01",
            end_date="2019-12-31"
        )
        
        filing_count = len(filings)
        
        print("\n" + "=" * 80)
        print("RESULTS")
        print("=" * 80)
        print(f"Filings Retrieved: {filing_count}")
        print(f"Expected:          89")
        
        if filing_count == 89:
            print("\n✅ SUCCESS: Correct number of filings retrieved!")
            return True
        else:
            print(f"\n❌ MISMATCH: Expected 89, got {filing_count}")
            print(f"   Difference: {89 - filing_count} filings missing")
            
            # Show filing types breakdown
            from collections import defaultdict
            type_counts = defaultdict(int)
            for f in filings:
                type_counts[f["filing_type"]] += 1
            
            print("\n   Filing Types Retrieved:")
            for ft, ct in sorted(type_counts.items()):
                print(f"      {ft}: {ct}")
            
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup
        if hasattr(analyzer, 'session') and analyzer.session:
            await analyzer.session.close()


if __name__ == "__main__":
    success = asyncio.run(test_filing_count())
    sys.exit(0 if success else 1)
