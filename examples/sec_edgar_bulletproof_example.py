#!/usr/bin/env python3
"""
SEC EDGAR Bulletproof Configuration - Usage Examples
===================================================

Run with mock mode: SEC_MOCK_MODE=true python examples/sec_edgar_bulletproof_example.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.integrations.sec_edgar_bulletproof_config import (
    BulletproofSECEdgarClient,
    BulletproofConfig
)

async def main():
    """Demonstrate bulletproof client usage."""
    print("SEC EDGAR Bulletproof Client - Examples")
    print("="*60)
    
    # Example 1: Basic usage
    async with BulletproofSECEdgarClient() as client:
        print("\n1. Fetching Apple submissions...")
        submissions = await client.get_company_submissions("320193")
        if submissions:
            print(f"   ✓ Company: {submissions['name']}")
        
        # Example 2: Specialized methods
        print("\n2. Using specialized methods...")
        filings = await client.get_10k_filings("AAPL", years=3)
        print(f"   ✓ Found {len(filings)} 10-K filings")
        
        # Example 3: Statistics
        print("\n3. Performance statistics:")
        stats = client.get_statistics()
        print(f"   Total requests: {stats['total_requests']}")
        print(f"   Success rate:   {stats['success_rate']:.1%}")
        print(f"   Cache hit rate: {stats['cache_hit_rate']:.1%}")
    
    print("\n" + "="*60)
    print("Examples completed! See SEC_EDGAR_BULLETPROOF_GUIDE.md for more.")

if __name__ == "__main__":
    asyncio.run(main())
