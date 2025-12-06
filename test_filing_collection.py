"""
Quick Nike 2019 Filing Count Test
"""
import asyncio
import sys
sys.path.insert(0, 'C:/Users/timot/IdeaProjects/JLAW')

from src.forensics.forensic_orchestrator import ForensicOrchestrator, ForensicCase
from src.forensics.config_manager import ConfigurationManager
from src.forensics.immutable_storage import StorageConfig
from datetime import datetime

async def test_filing_collection():
    print("Initializing system...")
    config_mgr = ConfigurationManager()
    config = config_mgr.config
    
    storage_config = StorageConfig(provider=config.storage_provider)
    
    orchestrator = ForensicOrchestrator(
        govinfo_api_key=config.govinfo.api_key,
        storage_config=storage_config,
        audit_signing_key=b"test-key",
        user_agent="NITS Recon Unit contact@nits-secops.org"
    )
    
    case = ForensicCase(
        case_id="TEST_2019",
        target_cik="0000320187",
        target_company="Nike Inc",
        investigation_start=datetime.now()
    )
    
    print("\nCollecting filings...")
    filings = await orchestrator._collect_filings(
        case=case,
        filing_types=["10-K", "10-Q", "4"],
        years=1
    )
    
    print(f"\n✓ Collected {len(filings)} filings")
    
    # Count by type
    form_counts = {}
    for filing in filings:
        form_type = filing.get('form_type', 'UNKNOWN')
        form_counts[form_type] = form_counts.get(form_type, 0) + 1
    
    print("\nBreakdown:")
    for form_type, count in sorted(form_counts.items()):
        print(f"  {form_type}: {count}")
    
    print(f"\n✓ Test complete!")
    return len(filings)

if __name__ == "__main__":
    result = asyncio.run(test_filing_collection())
    print(f"\nTotal: {result} filings")

