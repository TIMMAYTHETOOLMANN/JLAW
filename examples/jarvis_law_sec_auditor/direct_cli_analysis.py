#!/usr/bin/env python3
"""
JARVIS:LAW Direct CLI Analysis
Raw forensic analysis bypassing GUI - immediate execution
"""

import sys
import os
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

def analyze_company(ticker_or_cik, form_type="4", years=3):
    """
    Direct forensic analysis of a company
    
    Args:
        ticker_or_cik: Stock ticker (e.g., 'NKE', 'TSLA') or CIK number
        form_type: SEC form type (default: '4' for insider trading)
        years: Number of years to analyze (default: 3)
    """
    print("=" * 80)
    print("JARVIS:LAW DIRECT FORENSIC ANALYSIS")
    print("=" * 80)
    print()
    print(f"Target: {ticker_or_cik}")
    print(f"Form Type: {form_type}")
    print(f"Analysis Period: Last {years} years")
    print()
    print("=" * 80)
    print()
    
    try:
        from tools.sec_crawler import search_company_by_ticker, fetch_sec_filings_by_cik
        from datetime import datetime
        
        # Step 1: Resolve ticker to CIK
        print("[1/4] Resolving company identifier...")
        
        if ticker_or_cik.isdigit():
            cik = ticker_or_cik.zfill(10)
            company_name = f"CIK-{cik}"
            print(f"      Using CIK: {cik}")
        else:
            print(f"      Looking up ticker: {ticker_or_cik}")
            company_info = search_company_by_ticker(ticker_or_cik.upper())
            if not company_info:
                print(f"      ❌ ERROR: Ticker '{ticker_or_cik}' not found")
                return None
            cik = company_info.get('cik')
            company_name = company_info.get('name', ticker_or_cik)
            print(f"      ✓ Found: {company_name}")
            print(f"      ✓ CIK: {cik}")
        
        print()
        
        # Step 2: Fetch recent filings
        print(f"[2/4] Fetching Form {form_type} filings from SEC.gov...")
        
        current_year = datetime.now().year
        year_start = current_year - years
        year_end = current_year
        
        filings = fetch_sec_filings_by_cik(
            cik=cik,
            form_type=form_type,
            year_start=year_start,
            year_end=year_end,
            limit=50
        )
        
        if not filings:
            print(f"      ❌ No Form {form_type} filings found")
            return None
        
        print(f"      ✓ Found {len(filings)} filings")
        print()
        
        # Step 3: Display recent filings
        print(f"[3/4] Recent Form {form_type} filings:")
        print()
        print(f"{'Date':<12} {'Accession':<22} {'URL'}")
        print("-" * 80)
        
        for i, filing in enumerate(filings[:10], 1):
            date = filing.get('filingDate', 'N/A')
            accession = filing.get('accessionNumber', 'N/A')
            url = filing.get('primaryDocument', 'N/A')
            print(f"{date:<12} {accession:<22} {url}")
        
        if len(filings) > 10:
            print(f"\n... and {len(filings) - 10} more filings")
        
        print()
        
        # Step 4: Basic analysis summary
        print("[4/4] Analysis Summary:")
        print()
        print(f"Company:          {company_name}")
        print(f"CIK:              {cik}")
        print(f"Form Type:        {form_type}")
        print(f"Total Filings:    {len(filings)}")
        print(f"Date Range:       {filings[-1].get('filingDate', 'N/A')} to {filings[0].get('filingDate', 'N/A')}")
        print()
        
        # Return data for further processing
        return {
            'company': company_name,
            'cik': cik,
            'form_type': form_type,
            'filings': filings,
            'total_count': len(filings)
        }
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("   Missing dependencies. Install with: pip install httpx beautifulsoup4 lxml")
        return None
    except Exception as e:
        print(f"❌ Analysis Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def quick_scan(ticker):
    """Quick scan shortcut"""
    return analyze_company(ticker)


if __name__ == "__main__":
    print()
    
    if len(sys.argv) < 2:
        print("Usage: python direct_cli_analysis.py <TICKER_OR_CIK> [FORM_TYPE] [YEARS]")
        print()
        print("Examples:")
        print("  python direct_cli_analysis.py NKE")
        print("  python direct_cli_analysis.py TSLA 4 5")
        print("  python direct_cli_analysis.py 0000320187 10-K")
        print()
        sys.exit(1)
    
    target = sys.argv[1]
    form_type = sys.argv[2] if len(sys.argv) > 2 else "4"
    years = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    
    result = analyze_company(target, form_type, years)
    
    if result:
        print("=" * 80)
        print("✓ ANALYSIS COMPLETE")
        print("=" * 80)
        print()
        print(f"Results saved to memory for company: {result['company']}")
        print()
    else:
        print("=" * 80)
        print("✗ ANALYSIS FAILED")
        print("=" * 80)
        sys.exit(1)

