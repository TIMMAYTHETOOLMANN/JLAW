#!/usr/bin/env python3
"""
Zero-Dollar Transaction Acquisition Demo
=========================================

Demonstrates the SEC EDGAR Data Acquisition Module functionality including:
- Form 4 filing acquisition from SEC EDGAR
- XML parsing for zero-dollar transactions
- Integration with Transaction model
- Evidence integrity tracking

This example shows how to use the acquisition module but does NOT make
real API calls. For actual usage, remove mock_mode or set SEC_MOCK_MODE=false.

Reference:
- JLAW Zero-Dollar Transaction Forensic Specification v1.0
- Section 12.2: SEC EDGAR Acquisition Module
"""

import sys
import asyncio
from pathlib import Path
from datetime import date
from decimal import Decimal

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.zero_dollar.acquisition import (
    SECEdgarAcquisition,
    FilingMetadata,
    Form4Filing,
    EdgarRateLimiter,
)
from src.zero_dollar.models import Transaction
from src.zero_dollar.constants import (
    classify_magnitude,
    get_transaction_code_info,
    is_zero_dollar_suspicious,
)


def demo_filing_metadata():
    """Demonstrate FilingMetadata dataclass."""
    print("\n" + "=" * 70)
    print("DEMO 1: Filing Metadata")
    print("=" * 70)
    
    metadata = FilingMetadata(
        accession_number="0000320187-20-000001",
        cik="0000320187",
        filing_date=date(2020, 1, 15),
        primary_document="doc4.xml",
        form_type="4",
    )
    
    print(f"\nFiling Metadata:")
    print(f"  Accession Number: {metadata.accession_number}")
    print(f"  CIK: {metadata.cik}")
    print(f"  Filing Date: {metadata.filing_date}")
    print(f"  Primary Document: {metadata.primary_document}")
    print(f"  Form Type: {metadata.form_type}")


def demo_form4_filing():
    """Demonstrate Form4Filing with zero-dollar transactions."""
    print("\n" + "=" * 70)
    print("DEMO 2: Form 4 Filing with Zero-Dollar Transactions")
    print("=" * 70)
    
    # Create example zero-dollar transaction
    transaction1 = Transaction(
        accession_number="0000320187-20-000001",
        issuer_cik="0000320187",
        issuer_name="NIKE, Inc.",
        reporting_person_cik="0001234567",
        reporting_person_name="John Donahoe",
        transaction_date=date(2020, 1, 10),
        filing_date=date(2020, 1, 15),
        transaction_code="A",  # Award/Grant - legitimate at zero-dollar
        shares=Decimal("50000"),
        price_per_share=None,  # Zero-dollar
        transaction_acquired_disposed="A",
        shares_owned_following=Decimal("1500000"),
        direct_indirect="I",
        nature_of_ownership="By Donahoe Family Trust",
        security_title="Restricted Stock Units",
    )
    
    # Create suspicious zero-dollar transaction
    transaction2 = Transaction(
        accession_number="0000320187-20-000001",
        issuer_cik="0000320187",
        issuer_name="NIKE, Inc.",
        reporting_person_cik="0001234567",
        reporting_person_name="John Donahoe",
        transaction_date=date(2020, 1, 12),
        filing_date=date(2020, 1, 15),
        transaction_code="P",  # Purchase - SUSPICIOUS at zero-dollar
        shares=Decimal("250000"),
        price_per_share=None,  # Zero-dollar - UNUSUAL for purchase
        transaction_acquired_disposed="A",
        shares_owned_following=Decimal("1750000"),
        direct_indirect="I",
        nature_of_ownership="By Donahoe Family Trust",
        security_title="Common Stock",
    )
    
    # Create Form4Filing
    filing = Form4Filing(
        accession_number="0000320187-20-000001",
        filing_date=date(2020, 1, 15),
        issuer_cik="0000320187",
        issuer_name="NIKE, Inc.",
        issuer_ticker="NKE",
        reporting_owner_cik="0001234567",
        reporting_owner_name="John Donahoe",
        is_director=False,
        is_officer=True,
        is_ten_percent_owner=False,
        officer_title="President and CEO",
        transactions=[transaction1, transaction2],
        footnotes={
            "F1": "Restricted stock units vest over 4 years",
            "F2": "Transaction executed pursuant to Rule 10b5-1 plan",
        },
        xml_hash="abc123def456789",
    )
    
    print(f"\nForm 4 Filing:")
    print(f"  Accession: {filing.accession_number}")
    print(f"  Issuer: {filing.issuer_name} ({filing.issuer_ticker})")
    print(f"  Reporting Owner: {filing.reporting_owner_name}")
    print(f"  Officer Title: {filing.officer_title}")
    print(f"  Total Transactions: {len(filing.transactions)}")
    print(f"  Evidence Hash: {filing.xml_hash}")
    
    print(f"\n  Footnotes:")
    for fid, text in filing.footnotes.items():
        print(f"    {fid}: {text}")
    
    # Analyze each transaction
    print(f"\n  Transaction Analysis:")
    for i, txn in enumerate(filing.transactions, 1):
        print(f"\n  Transaction {i}:")
        print(f"    Date: {txn.transaction_date}")
        print(f"    Code: {txn.transaction_code}")
        print(f"    Security: {txn.security_title}")
        print(f"    Shares: {txn.shares:,}")
        print(f"    Price: {'$0.00 (ZERO-DOLLAR)' if txn.is_zero_dollar else f'${txn.price_per_share}'}")
        print(f"    Ownership: {txn.direct_indirect} - {txn.nature_of_ownership}")
        
        # Check if suspicious
        code_info = get_transaction_code_info(txn.transaction_code)
        tier = classify_magnitude(int(txn.shares))
        suspicious = is_zero_dollar_suspicious(txn.transaction_code, tier.value)
        
        print(f"    Code Info: {code_info.description}")
        print(f"    Legitimacy: {code_info.zero_dollar_legitimacy:.2f}/1.0")
        print(f"    Magnitude: {tier.value}")
        print(f"    Days to Filing: {txn.days_to_filing}")
        
        if suspicious:
            print(f"    ⚠️  WARNING: SUSPICIOUS ZERO-DOLLAR TRANSACTION")
            print(f"    Code '{txn.transaction_code}' with {tier.value} is unusual")
        else:
            print(f"    ✓ Normal zero-dollar transaction for code '{txn.transaction_code}'")


def demo_rate_limiter():
    """Demonstrate rate limiter usage."""
    print("\n" + "=" * 70)
    print("DEMO 3: Rate Limiter")
    print("=" * 70)
    
    limiter = EdgarRateLimiter(max_requests_per_second=10)
    
    print(f"\nRate Limiter Configuration:")
    print(f"  Max Requests/Second: {limiter.max_requests_per_second}")
    print(f"  Min Interval: {limiter.min_interval:.3f}s")
    print(f"\nSEC EDGAR API Guidelines:")
    print(f"  - Maximum 10 requests per second")
    print(f"  - Proper User-Agent required")
    print(f"  - Cooldown period on 403/429 responses")


async def demo_acquisition_client():
    """Demonstrate SECEdgarAcquisition client initialization."""
    print("\n" + "=" * 70)
    print("DEMO 4: SEC EDGAR Acquisition Client")
    print("=" * 70)
    
    config = {
        'user_agent': 'JLAW-Demo/1.0 demo@example.com',
        'max_concurrent_requests': 10,
        'request_timeout': 30,
    }
    
    print(f"\nClient Configuration:")
    print(f"  User-Agent: {config['user_agent']}")
    print(f"  Max Concurrent: {config['max_concurrent_requests']}")
    print(f"  Timeout: {config['request_timeout']}s")
    
    # Note: In real usage, you would use:
    # async with SECEdgarAcquisition(config) as client:
    #     filings = await client.get_form4_filings(
    #         issuer_cik='0000320187',
    #         start_date=date(2020, 1, 1),
    #         end_date=date(2020, 12, 31)
    #     )
    
    print(f"\n  Usage Pattern:")
    print(f"    async with SECEdgarAcquisition(config) as client:")
    print(f"        filings = await client.get_form4_filings(")
    print(f"            issuer_cik='0000320187',")
    print(f"            start_date=date(2020, 1, 1),")
    print(f"            end_date=date(2020, 12, 31)")
    print(f"        )")
    print(f"\n  Features:")
    print(f"    ✓ Async HTTP with aiohttp")
    print(f"    ✓ Rate limiting (9 req/sec conservative)")
    print(f"    ✓ SHA-256 evidence integrity")
    print(f"    ✓ Zero-dollar transaction detection")
    print(f"    ✓ Footnote extraction and linking")


def demo_evidence_integrity():
    """Demonstrate evidence integrity tracking."""
    print("\n" + "=" * 70)
    print("DEMO 5: Evidence Integrity Tracking")
    print("=" * 70)
    
    # In real usage, the client computes SHA-256 hash
    import hashlib
    
    sample_xml = """<?xml version="1.0"?>
<ownershipDocument>
    <issuer>
        <issuerCik>0000320187</issuerCik>
        <issuerName>NIKE, Inc.</issuerName>
    </issuer>
</ownershipDocument>"""
    
    xml_hash = hashlib.sha256(sample_xml.encode('utf-8')).hexdigest()
    
    print(f"\nEvidence Integrity:")
    print(f"  Hash Algorithm: SHA-256")
    print(f"  Sample Hash: {xml_hash}")
    print(f"  Compliance: FRE 902(13)/(14)")
    print(f"\n  Usage in Filing:")
    print(f"    - Each Form 4 XML is hashed on acquisition")
    print(f"    - Hash stored in Form4Filing.xml_hash")
    print(f"    - Hash can verify document integrity")
    print(f"    - Chain of custody tracking enabled")


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 70)
    print("ZERO-DOLLAR TRANSACTION ACQUISITION MODULE")
    print("Demonstration")
    print("=" * 70)
    print("\nJLAW Zero-Dollar Transaction Forensic Specification v1.0")
    print("PR #2 of 8: SEC EDGAR Data Acquisition Module")
    
    # Run demonstrations
    demo_filing_metadata()
    demo_form4_filing()
    demo_rate_limiter()
    
    # Run async demo
    asyncio.run(demo_acquisition_client())
    
    demo_evidence_integrity()
    
    # Final summary
    print("\n" + "=" * 70)
    print("DEMONSTRATION COMPLETE")
    print("=" * 70)
    print("\n✅ SEC EDGAR Acquisition Module Features:")
    print("   - Form 4 XML parsing (derivative + non-derivative)")
    print("   - Zero-dollar transaction detection")
    print("   - SEC-compliant rate limiting (10 req/sec max)")
    print("   - Evidence integrity (SHA-256 hashing)")
    print("   - Footnote extraction and linking")
    print("   - Integration with Transaction model")
    print("   - Custom exception handling")
    print("\n✅ Ready for PR #3: Temporal Clustering & Anomaly Detection")
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
