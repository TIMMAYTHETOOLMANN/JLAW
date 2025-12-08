"""
Single Filing Test - Nike 10-K 2019
Verify core functionality before batch analysis

Notes:
- This test requires a valid GOVINFO_API_KEY (api.data.gov). If the key is not
  present in the environment, the test will be skipped to avoid false failures.
  Set GOVINFO_API_KEY in your environment or .env before running.
"""

import asyncio
import os
import pytest
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, 'C:/Users/timot/IdeaProjects/JLAW')

from src.forensics.forensic_orchestrator import ForensicOrchestrator
from src.forensics.immutable_storage import StorageConfig

async def test_single_filing():
    """Test analysis of single Nike 10-K filing from 2019."""
    
    print("="*80)
    print("SINGLE FILING TEST: Nike 10-K 2019")
    print("="*80)
    
    # Initialize orchestrator
    storage_config = StorageConfig(
        provider="LOCAL",
        retention_days=90,
        compliance_mode=True,
        redundancy_level=3,
        compression=True
    )
    
    # Resolve GovInfo API key from environment (fallback to .env if available)
    gov_key = os.getenv("GOVINFO_API_KEY", "").strip()
    if not gov_key:
        try:
            from dotenv import load_dotenv  # type: ignore
            load_dotenv()
            gov_key = os.getenv("GOVINFO_API_KEY", "").strip()
        except Exception:
            pass

    if not gov_key:
        pytest.skip("GOVINFO_API_KEY not set; skipping single filing test that requires GovInfo")

    orchestrator = ForensicOrchestrator(
        govinfo_api_key=gov_key,
        storage_config=storage_config,
        audit_signing_key=b"test_audit_key"
    )
    
    print("\n[1] Fetching Nike 2019 filings metadata...")
    
    # We know from our test: Nike 10-K filed 2019-07-23
    # Accession: 0000320187-19-000051
    
    test_filing = {
        'accession': '0000320187-19-000051',
        'filing_date': '2019-07-23',
        'form_type': '10-K',
        'primary_document': 'nke-531201910k.htm',
        'document_url': 'https://www.sec.gov/Archives/edgar/data/320187/000032018719000051/nke-531201910k.htm',
        'viewer_url': 'https://www.sec.gov/cgi-bin/viewer?action=view&cik=320187&accession_number=0000320187-19-000051&xbrl_type=v',
        'text_url': 'https://www.sec.gov/Archives/edgar/data/320187/000032018719000051.txt'
    }
    
    print(f"    Form: {test_filing['form_type']}")
    print(f"    Date: {test_filing['filing_date']}")
    print(f"    Accession: {test_filing['accession']}")
    print(f"    URL: {test_filing['document_url']}")
    
    print("\n[2] Initiating investigation...")
    
    case_id = await orchestrator.initiate_investigation(
        cik="0000320187",
        company_name="Nike Inc",
        investigator="TEST_SYSTEM",
        case_notes="Single filing test - 10-K 2019"
    )
    
    print(f"    Case ID: {case_id}")
    
    print("\n[3] Analyzing filing (this will take ~30-60 seconds with rate limiting)...")
    
    # Get the case
    case = orchestrator.active_cases[case_id]
    
    # Analyze the single filing
    analysis = await orchestrator._analyze_filing(case, test_filing)
    
    print(f"    [OK] Analysis complete")
    print(f"    Filing Type: {analysis.filing_type}")
    print(f"    Red Flags: {len(analysis.red_flags)}")
    print(f"    Revenue Anomalies: {len(analysis.revenue_anomalies)}")
    
    # Add to case
    case.filings_analyzed.append(analysis)
    
    print("\n[4] Mapping violations to statutes...")
    
    await orchestrator._map_all_violations(case)
    
    print(f"    [OK] Violations detected: {len(case.violations_detected)}")
    
    # Show violations
    if case.violations_detected:
        print("\n[5] Violations found:")
        for i, v in enumerate(case.violations_detected[:10], 1):  # Show first 10
            print(f"\n    {i}. {getattr(v, 'section', 'UNKNOWN')}")
            print(f"       Severity: {getattr(v, 'severity', 'UNKNOWN')}")
            print(f"       Description: {getattr(v, 'description', 'N/A')[:100]}...")
    else:
        print("\n[5] No violations detected")
    
    print("\n[6] Generating report...")
    
    # Calculate risk
    case.risk_score = orchestrator._calculate_risk_score(case)
    
    # Generate report
    case.status = orchestrator.active_cases[case_id].status  # Get current status
    report = await orchestrator._generate_case_report(case_id)
    
    print(f"    [OK] Report generated")
    print(f"    Risk Score: {report['summary']['risk_score']:.2%}")
    print(f"    Total Violations: {report['summary']['violations_detected']}")
    print(f"    Criminal Violations: {report['summary']['criminal_violations']}")
    print(f"    Estimated Damages: ${report['summary']['estimated_damages_total']:,.2f}")
    
    if 'dossier' in report:
        print(f"\n[7] Dossier generated:")
        print(f"    ID: {report['dossier']['id']}")
        print(f"    Path: {report['dossier']['json_path']}")
        print(f"    Pages: {report['dossier']['total_pages']}")
        print(f"    Exhibits: {report['dossier']['total_exhibits']}")
    
    print("\n" + "="*80)
    print("SINGLE FILING TEST: [OK] COMPLETE")
    print("="*80)
    
    # Show detailed violations if any
    if report.get('violations_detailed'):
        print(f"\nDetailed violations found: {len(report['violations_detailed'])}")
        for i, v in enumerate(report['violations_detailed'][:5], 1):
            print(f"\n{i}. {v.get('statute', 'UNKNOWN')}")
            print(f"   Severity: {v.get('severity')}")
            print(f"   Description: {v.get('description', '')[:150]}")
            if v.get('exact_quote'):
                print(f"   Quote: {v['exact_quote'][:100]}...")
            if v.get('estimated_damages'):
                print(f"   Damages: ${v['estimated_damages']:,}")
    
    return report

if __name__ == "__main__":
    try:
        result = asyncio.run(test_single_filing())
        print("\n[OK] Test completed successfully!")
        print(f"\nIf this shows violations (especially SOX 302 or restatements),")
        print(f"then the system is working correctly and ready for batch analysis.")
    except Exception as e:
        print(f"\n[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

