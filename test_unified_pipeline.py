#!/usr/bin/env python3
"""
Simple test script to verify unified pipeline infrastructure.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.forensics.forensic_context import ForensicContext, SECFiling, Violation
from src.forensics.unified_report_generator import UnifiedReportGenerator


async def test_basic_report_generation():
    """Test report generation with minimal data."""
    print("Testing basic report generation...")
    
    # Create minimal context
    context = ForensicContext(
        company_name="Test Company Inc.",
        cik="0000123456",
        analysis_period_start="2019-01-01",
        analysis_period_end="2019-12-31"
    )
    
    # Add sample filing
    filing = SECFiling(
        accession_number="0000123456-19-000001",
        filing_type="10-K",
        filing_date="2019-03-15",
        cik="0000123456",
        company_name="Test Company Inc.",
        document_url="https://www.sec.gov/test/doc.htm",
        raw_content="Sample filing content for testing purposes."
    )
    context.filings.append(filing)
    
    # Add sample violation
    violation = Violation(
        violation_id="V001",
        violation_type="Test Violation Type",
        statute="15 U.S.C. § 78j(b)",
        severity="MEDIUM",
        description="This is a test violation for verification purposes.",
        evidence="Test evidence supporting the violation.",
        document_url="https://www.sec.gov/test/doc.htm",
        exact_quote="This is an exact quote from the test document.",
        prosecutorial_merit="MODERATE",
        estimated_damages=50000.00,
        criminal_referral=False,
        metadata={'accession_number': '0000123456-19-000001'}
    )
    context.violations.append(violation)
    
    # Generate report
    output_dir = Path("/tmp/test_forensic_report")
    generator = UnifiedReportGenerator(output_dir)
    report_path = generator.generate_full_report(context)
    
    print(f"✅ Report generated at: {report_path}")
    
    # Verify files exist
    expected_files = [
        "FORENSIC_REPORT.md",
        "executive_summary.md",
        "machine_readable/violations.json",
        "evidence/chain_of_custody.json",
        "appendices/methodology.md"
    ]
    
    all_exist = True
    for file_path in expected_files:
        full_path = output_dir / file_path
        if full_path.exists():
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} missing")
            all_exist = False
    
    if all_exist:
        print("\n✅ All expected files generated successfully!")
        
        # Print preview of main report
        main_report = output_dir / "FORENSIC_REPORT.md"
        content = main_report.read_text()
        print("\n" + "=" * 80)
        print("MAIN REPORT PREVIEW (first 50 lines):")
        print("=" * 80)
        for line in content.split('\n')[:50]:
            print(line)
        print("=" * 80)
        
        return True
    else:
        print("\n❌ Some expected files are missing")
        return False


if __name__ == "__main__":
    result = asyncio.run(test_basic_report_generation())
    sys.exit(0 if result else 1)
