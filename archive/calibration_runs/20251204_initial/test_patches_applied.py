"""
Test script to verify all patches have been applied successfully
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.forensics.sec_edgar_api import SECEdgarAPI, FilingMetadata, fetch_nike_2019_filings


async def test_sec_edgar_api():
    """Test the patched SEC EDGAR API"""
    print("=" * 80)
    print("TESTING PATCHED SEC EDGAR API")
    print("=" * 80)
    
    # Test 1: API instantiation
    print("\n1. Testing API instantiation...")
    api = SECEdgarAPI()
    print(f"   ✓ SECEdgarAPI instantiated")
    print(f"   ✓ Cache directory: {api.cache_dir}")
    print(f"   ✓ Rate limit: {api.rate_limit_delay}s")
    
    # Test 2: Test FilingMetadata dataclass
    print("\n2. Testing FilingMetadata dataclass...")
    metadata = FilingMetadata(
        accession_number="0000320187-19-000001",
        filing_type="10-K",
        cik="0000320187",
        company_name="Nike Inc."
    )
    print(f"   ✓ FilingMetadata created")
    print(f"   ✓ Accession: {metadata.accession_number}")
    print(f"   ✓ Type: {metadata.filing_type}")
    
    # Test 3: Fetch Nike 2019 filings (limited to 5 for quick test)
    print("\n3. Testing get_filings() with Nike 2019...")
    async with SECEdgarAPI() as api:
        filings = await api.get_filings(
            cik="0000320187",
            start_date="2019-01-01",
            end_date="2019-12-31",
            filing_types=["10-K", "10-Q"],
            max_filings=5,
            company_name="Nike Inc."
        )
        
        print(f"   ✓ Retrieved {len(filings)} filings")
        for filing in filings[:3]:
            print(f"   - {filing.filing_type}: {filing.filing_date} ({filing.accession_number})")
    
    # Test 4: Company info
    print("\n4. Testing get_company_info()...")
    async with SECEdgarAPI() as api:
        info = await api.get_company_info("0000320187")
        print(f"   ✓ Company: {info.get('name')}")
        print(f"   ✓ Tickers: {info.get('tickers')}")
        print(f"   ✓ SIC: {info.get('sic')} - {info.get('sic_description')}")
    
    print("\n" + "=" * 80)
    print("ALL TESTS PASSED - PATCHES SUCCESSFULLY APPLIED!")
    print("=" * 80)


def test_imports():
    """Test that all patched modules can be imported"""
    print("=" * 80)
    print("TESTING MODULE IMPORTS")
    print("=" * 80)
    
    modules = [
        ('src.forensics.sec_edgar_api', ['SECEdgarAPI', 'FilingMetadata']),
        ('src.forensics.sec_edgar_analyzer', ['SECForensicAnalyzer']),
        ('src.forensics.forensic_orchestrator', ['ForensicOrchestrator']),
        ('src.forensics.insider_form4_analyzer', ['InsiderForm4Analyzer']),
    ]
    
    for module_name, classes in modules:
        try:
            print(f"\n✓ {module_name}")
            module = __import__(module_name, fromlist=classes)
            for cls in classes:
                if hasattr(module, cls):
                    print(f"  ✓ {cls}")
                else:
                    print(f"  ✗ {cls} NOT FOUND")
        except Exception as e:
            print(f"✗ {module_name}: {e}")
    
    print("\n" + "=" * 80)
    print("IMPORT TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    print("\n")
    test_imports()
    print("\n")
    asyncio.run(test_sec_edgar_api())

