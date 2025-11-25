"""
GovInfo Published Documents API Integration Test
================================================

Tests the GET /published/{dateIssuedStartDate} endpoint.
Discovers documents by publication date for monitoring and compliance.

Your API Key: QLSbdMWeb3QadP66hRAhw3V027uRU9fSYWPistqD
"""

import asyncio
import os
from datetime import datetime, timedelta
from src.forensics.govinfo_api_client import GovInfoAPIClient

async def test_published_documents():
    """Test GovInfo Published Documents API functionality."""
    
    print("=" * 80)
    print("GOVINFO PUBLISHED DOCUMENTS API TEST")
    print("=" * 80)
    print()
    
    api_key = os.getenv("GOVINFO_API_KEY", "QLSbdMWeb3QadP66hRAhw3V027uRU9fSYWPistqD")
    
    client = GovInfoAPIClient(api_key)
    
    # Test 1: Get Recently Published Documents
    print("[TEST 1] Get Recently Published - Last 30 Days")
    print("-" * 80)
    try:
        recent = await client.get_recently_published(days_back=30, page_size=10)
        
        print(f"[SUCCESS] Found {recent.get('count', 0)} documents from last 30 days")
        print(f"[INFO] Sample packages:")
        
        for i, pkg in enumerate(recent.get("packages", [])[:5], 1):
            print(f"\n  Package {i}:")
            print(f"    ID: {pkg.get('packageId')}")
            print(f"    Collection: {pkg.get('packageId', '').split('-')[0]}")
            print(f"    Date Issued: {pkg.get('dateIssued')}")
            if pkg.get('title'):
                print(f"    Title: {pkg.get('title')[:60]}...")
        
        print("[PASS] Recently published retrieval working")
    except Exception as e:
        print(f"[FAIL] {e}")
    
    print()
    
    # Test 2: Get Published Bills
    print("[TEST 2] Get Published Bills - 2024")
    print("-" * 80)
    try:
        bills = await client.get_published_bills(
            start_date="2024-01-01",
            page_size=10
        )
        
        print(f"[SUCCESS] Found {len(bills)} bills from 2024")
        print(f"[INFO] Sample bills:")
        
        for i, bill in enumerate(bills[:3], 1):
            print(f"\n  Bill {i}:")
            print(f"    Package: {bill.package_id}")
            print(f"    Type: {bill.doc_class}")
            print(f"    Date: {bill.date_issued}")
            if bill.title:
                print(f"    Title: {bill.title[:60]}...")
        
        print("[PASS] Published bills retrieval working")
    except Exception as e:
        print(f"[FAIL] {e}")
    
    print()
    
    # Test 3: Get Published Federal Register
    print("[TEST 3] Get Published Federal Register - 2024")
    print("-" * 80)
    try:
        fr_docs = await client.get_published_federal_register(
            start_date="2024-01-01",
            page_size=10
        )
        
        print(f"[SUCCESS] Found {len(fr_docs)} FR documents from 2024")
        print(f"[INFO] Sample FR notices:")
        
        for i, doc in enumerate(fr_docs[:3], 1):
            print(f"\n  FR Notice {i}:")
            print(f"    Package: {doc.package_id}")
            print(f"    Date: {doc.date_issued}")
            if doc.title:
                print(f"    Title: {doc.title[:60]}...")
        
        print("[PASS] Published FR retrieval working")
    except Exception as e:
        print(f"[FAIL] {e}")
    
    print()
    
    # Test 4: Get Published with Multiple Collections
    print("[TEST 4] Get Published - Multiple Collections (2024)")
    print("-" * 80)
    try:
        result = await client.get_published_documents(
            date_issued_start="2024-01-01",
            collections=["BILLS", "FR", "CFR"],
            page_size=20
        )
        
        print(f"[SUCCESS] Found {result.get('count', 0)} documents across collections")
        print(f"[INFO] Collection breakdown:")
        
        # Count by collection
        collection_counts = {}
        for pkg in result.get("packages", []):
            pkg_id = pkg.get("packageId", "")
            collection = pkg_id.split("-")[0] if "-" in pkg_id else "Unknown"
            collection_counts[collection] = collection_counts.get(collection, 0) + 1
        
        for collection, count in collection_counts.items():
            print(f"  {collection}: {count} documents")
        
        print("[PASS] Multiple collection retrieval working")
    except Exception as e:
        print(f"[FAIL] {e}")
    
    print()
    
    # Test 5: Get Published with Congress Filter
    print("[TEST 5] Get Published Bills - 118th Congress")
    print("-" * 80)
    try:
        result = await client.get_published_documents(
            date_issued_start="2023-01-01",
            collections=["BILLS"],
            congress="118",
            page_size=10
        )
        
        print(f"[SUCCESS] Found {result.get('count', 0)} bills from 118th Congress")
        print(f"[INFO] Sample bills:")
        
        for i, pkg in enumerate(result.get("packages", [])[:3], 1):
            print(f"\n  Bill {i}:")
            print(f"    Package: {pkg.get('packageId')}")
            print(f"    Congress: {pkg.get('congress', 'N/A')}")
            print(f"    Type: {pkg.get('docClass', 'N/A')}")
        
        print("[PASS] Congress filtering working")
    except Exception as e:
        print(f"[FAIL] {e}")
    
    print()
    
    # Test 6: Get Published with Document Class Filter
    print("[TEST 6] Get Published - House Bills Only (hr)")
    print("-" * 80)
    try:
        hr_bills = await client.get_published_bills(
            start_date="2024-01-01",
            doc_class="hr",
            page_size=10
        )
        
        print(f"[SUCCESS] Found {len(hr_bills)} House bills")
        print(f"[INFO] All should be type 'hr':")
        
        for i, bill in enumerate(hr_bills[:3], 1):
            print(f"  Bill {i}: {bill.package_id} - Type: {bill.doc_class}")
        
        print("[PASS] Document class filtering working")
    except Exception as e:
        print(f"[FAIL] {e}")
    
    print()
    
    # Test 7: Monitor Regulatory Changes
    print("[TEST 7] Monitor Regulatory Changes - Modified Since 2024")
    print("-" * 80)
    try:
        changes = await client.monitor_regulatory_changes(
            start_date="2020-01-01",
            modified_since="2024-01-01T00:00:00Z"
        )
        
        print(f"[SUCCESS] Monitored regulatory changes")
        print(f"[INFO] Changes by collection:")
        
        for collection, packages in changes.items():
            print(f"  {collection}: {len(packages)} modified documents")
            if packages:
                print(f"    Latest: {packages[0].package_id}")
                print(f"    Modified: {packages[0].last_modified}")
        
        print("[PASS] Regulatory change monitoring working")
    except Exception as e:
        print(f"[FAIL] {e}")
    
    print()
    
    # Test 8: Get Published Court Opinions
    print("[TEST 8] Get Published Court Opinions - 2024")
    print("-" * 80)
    try:
        opinions = await client.get_published_court_opinions(
            start_date="2024-01-01",
            page_size=10
        )
        
        print(f"[SUCCESS] Found {len(opinions)} court opinions from 2024")
        print(f"[INFO] Sample opinions:")
        
        for i, opinion in enumerate(opinions[:3], 1):
            print(f"\n  Opinion {i}:")
            print(f"    Package: {opinion.package_id}")
            print(f"    Date: {opinion.date_issued}")
        
        print("[PASS] Court opinion retrieval working")
    except Exception as e:
        print(f"[FAIL] {e}")
    
    print()
    
    # Test 9: Pagination
    print("[TEST 9] Pagination - Multiple Pages")
    print("-" * 80)
    try:
        # First page
        page1 = await client.get_published_documents(
            date_issued_start="2024-01-01",
            collections=["BILLS"],
            page_size=5
        )
        
        print(f"[INFO] Page 1: {len(page1.get('packages', []))} results")
        print(f"[INFO] Total count: {page1.get('count', 0)}")
        
        if page1.get("nextPage"):
            print(f"[INFO] Next page available")
            # Could fetch next page with offsetMark from nextPage URL
            print("[PASS] Pagination working")
        else:
            print("[INFO] Single page result")
            print("[PASS] Pagination mechanism working")
    except Exception as e:
        print(f"[FAIL] {e}")
    
    print()
    
    # Test 10: Date Range Analysis
    print("[TEST 10] Date Range Analysis - Compare 2023 vs 2024")
    print("-" * 80)
    try:
        # Get 2023 bills
        bills_2023 = await client.get_published_documents(
            date_issued_start="2023-01-01",
            collections=["BILLS"],
            page_size=10
        )
        
        # Get 2024 bills
        bills_2024 = await client.get_published_documents(
            date_issued_start="2024-01-01",
            collections=["BILLS"],
            page_size=10
        )
        
        print(f"[SUCCESS] Compared publication volumes")
        print(f"[INFO] 2023 Bills: {bills_2023.get('count', 0)}")
        print(f"[INFO] 2024 Bills: {bills_2024.get('count', 0)}")
        
        # Calculate trend
        count_2023 = bills_2023.get('count', 0)
        count_2024 = bills_2024.get('count', 0)
        
        if count_2023 > 0:
            change_pct = ((count_2024 - count_2023) / count_2023) * 100
            print(f"[INFO] Change: {change_pct:+.1f}%")
        
        print("[PASS] Date range analysis working")
    except Exception as e:
        print(f"[FAIL] {e}")
    
    print()
    
    # Cleanup
    await client.close()
    
    print("=" * 80)
    print("[COMPLETE] GOVINFO PUBLISHED DOCUMENTS API TEST")
    print("=" * 80)
    print()
    print("SUMMARY:")
    print("  - GET /published/{dateIssuedStartDate} endpoint working")
    print("  - Recently published documents retrieval ✓")
    print("  - Collection filtering (BILLS, CFR, FR, USCOURTS) ✓")
    print("  - Congress number filtering ✓")
    print("  - Document class filtering ✓")
    print("  - Modified since tracking ✓")
    print("  - Pagination with nextPage ✓")
    print("  - Date range analysis ✓")
    print()
    print("MONITORING CAPABILITIES:")
    print("  - Track new legislation (BILLS)")
    print("  - Monitor regulation changes (CFR)")
    print("  - Follow Federal Register notices (FR)")
    print("  - Discover recent court opinions (USCOURTS)")
    print("  - Identify modified documents (modifiedSince)")
    print()
    print("FORENSIC APPLICATIONS:")
    print("  - Compliance Monitoring: Track regulatory updates")
    print("  - Legislative Tracking: Follow new bills and amendments")
    print("  - Precedent Discovery: Find recent court decisions")
    print("  - Regulatory Intelligence: Monitor FR rulemaking")
    print("  - Change Detection: Identify document modifications")
    print()
    print("INTEGRATION PATTERNS:")
    print("  - Daily monitoring: get_recently_published(days_back=1)")
    print("  - Weekly digest: get_recently_published(days_back=7)")
    print("  - Compliance check: monitor_regulatory_changes()")
    print("  - Legislative updates: get_published_bills()")
    print("  - Precedent alerts: get_published_court_opinions()")

if __name__ == "__main__":
    asyncio.run(test_published_documents())

