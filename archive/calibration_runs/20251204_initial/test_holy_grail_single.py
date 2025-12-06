"""
Single Document Test - Holy Grail Universal SEC Extractor
Tests Form 4 extraction with comprehensive violation detection
"""

import asyncio
import sys
sys.path.insert(0, 'C:/Users/timot/IdeaProjects/JLAW')

from src.forensics.universal_sec_extractor import (
    UniversalDocumentExtractor,
    DocumentFormat,
    ExtractionResult
)

async def test_holy_grail_form4():
    """Test Holy Grail extraction on Nike Form 4 from 2019."""
    
    print("="*80)
    print("HOLY GRAIL SINGLE DOCUMENT TEST")
    print("="*80)
    print("\nTarget: Nike Form 4 (2019-01-22)")
    print("Expected: Zero-dollar transaction (625,000 shares gift)")
    print("Expected: Transaction data with proper nested <value> extraction")
    print("\n" + "-"*80 + "\n")
    
    # Initialize Universal Extractor
    extractor = UniversalDocumentExtractor()
    
    # Test URL - Nike Form 4 with gift transaction
    test_url = "https://www.sec.gov/Archives/edgar/data/320187/000032018719000015/edgardoc.xml"
    
    print(f"[1] Fetching document from SEC...")
    print(f"    URL: {test_url}")
    
    # Fetch the document
    import aiohttp
    async with aiohttp.ClientSession(headers={"User-Agent": "NITS Recon Unit contact@nits-secops.org"}) as session:
        async with session.get(test_url) as response:
            if response.status != 200:
                print(f"    [ERROR] HTTP {response.status}")
                return False
            
            xml_content = await response.text()
            print(f"    [OK] Fetched {len(xml_content)} bytes")
    
    print("\n[2] Extracting document with Holy Grail...")
    
    # Extract with Holy Grail
    result: ExtractionResult = await extractor.extract_document(
        content=xml_content,
        url=test_url,
        force_format=DocumentFormat.XML
    )
    
    print(f"    Format Detected: {result.format.value}")
    print(f"    Extraction Method: {result.extraction_method}")
    print(f"    Success: {result.success}")
    print(f"    Byte Coverage: {result.byte_coverage:.1%}")
    print(f"    Element Count: {result.element_count}")
    print(f"    Extraction Time: {result.extraction_time:.2f}s")
    
    if result.error_log:
        print(f"    Errors: {len(result.error_log)}")
        for err in result.error_log:
            print(f"      - {err}")
    
    print("\n[3] Analyzing extracted data...")
    
    # Check for ownership document extraction
    has_owner = 'reporting_owner' in result.structured_data
    has_transactions = 'transactions' in result.structured_data
    
    print(f"    Reporting Owner: {'[OK]' if has_owner else '[MISSING]'}")
    print(f"    Transactions: {'[OK]' if has_transactions else '[MISSING]'}")
    
    if has_owner:
        owner = result.structured_data['reporting_owner']
        print(f"      Owner: {owner.get('rptOwnerName', 'N/A')}")
        print(f"      CIK: {owner.get('rptOwnerCik', 'N/A')}")
    
    if has_transactions:
        transactions = result.structured_data['transactions']
        print(f"      Transaction Count: {len(transactions)}")
        
        print("\n[4] Transaction Details:")
        for i, tx in enumerate(transactions, 1):
            print(f"\n    Transaction #{i}:")
            print(f"      Type: {tx.get('type', 'N/A')}")
            print(f"      Date: {tx.get('transactionDate', 'N/A')}")
            print(f"      Code: {tx.get('transactionCode', 'N/A')}")
            print(f"      Shares: {tx.get('transactionShares', 'N/A')}")
            print(f"      Price: {tx.get('transactionPricePerShare', 'N/A')}")
            print(f"      Acq/Disp: {tx.get('transactionAcquiredDisposedCode', 'N/A')}")
            
            # Check for zero-dollar
            price_str = tx.get('transactionPricePerShare', '')
            try:
                price = float(price_str) if price_str else None
                if price == 0.0:
                    shares_str = tx.get('transactionShares', '')
                    code = tx.get('transactionCode', '')
                    print(f"\n      [VIOLATION DETECTED]")
                    print(f"      Type: Zero-Dollar Transaction")
                    print(f"      Code: {code} (Gift/RSU Vesting)")
                    print(f"      Shares: {shares_str}")
                    print(f"      Severity: HIGH")
                    print(f"      Statute: 15 USC § 78p(a)")
            except:
                pass
    
    # Check footnotes
    if result.footnotes:
        print(f"\n[5] Footnotes Found: {len(result.footnotes)}")
        for i, footnote in enumerate(result.footnotes[:3], 1):
            print(f"    {i}. {footnote[:100]}...")
    
    # Check signatures
    if result.signatures:
        print(f"\n[6] Signatures Found: {len(result.signatures)}")
        for sig in result.signatures:
            print(f"    - {sig.get('name', 'N/A')} ({sig.get('date', 'N/A')})")
    
    # Check metadata
    if result.metadata:
        print(f"\n[7] Metadata:")
        if 'namespaces' in result.metadata:
            print(f"    Namespaces: {len(result.metadata['namespaces'])}")
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    success_checks = []
    success_checks.append(("Document fetched", True))
    success_checks.append(("Extraction completed", result.success))
    success_checks.append(("Coverage >95%", result.byte_coverage > 0.95))
    success_checks.append(("Reporting owner extracted", has_owner))
    success_checks.append(("Transactions extracted", has_transactions and len(transactions) > 0))
    
    # Check for the specific gift transaction
    found_gift = False
    if has_transactions:
        for tx in transactions:
            if tx.get('transactionCode') == 'G' and '625000' in str(tx.get('transactionShares', '')):
                found_gift = True
                break
    
    success_checks.append(("Gift transaction found", found_gift))
    
    print()
    for check, passed in success_checks:
        status = "[OK]" if passed else "[FAIL]"
        print(f"  {status} {check}")
    
    all_passed = all(passed for _, passed in success_checks)
    
    print("\n" + "="*80)
    if all_passed:
        print("[SUCCESS] Holy Grail extraction working correctly!")
        print("Ready for full Nike 2019 batch analysis.")
    else:
        print("[PARTIAL] Some checks failed - review diagnostics above.")
    print("="*80 + "\n")
    
    return all_passed


if __name__ == "__main__":
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s:%(name)s:%(message)s'
    )
    
    result = asyncio.run(test_holy_grail_form4())
    exit(0 if result else 1)

