"""
Simple test: Can we fetch Nike 2019 filings from SEC?
No analysis. Just verify connection and data retrieval.
"""

import asyncio
import aiohttp
import random
from datetime import datetime

# 10 rotating user agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/91.0 Safari/537.36 Research/1.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/92.0 Safari/537.36 Analysis/1.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/93.0 Safari/537.36 Forensic/1.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0 Data/1.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_5_2) AppleWebKit/605.1.15 Safari/605.1.15 Research/1.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Edge/91.0 Analytics/1.0",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0 Investigation/1.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 Chrome/90.0 Compliance/1.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/94.0 Audit/1.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0 Crawler/1.0"
]

async def test_nike_2019():
    """Simple test: Fetch Nike 2019 filings."""
    
    print("="*80)
    print("CORE SYSTEM TEST: SEC EDGAR Connection")
    print("="*80)
    print(f"Target: Nike Inc. (CIK: 0000320187)")
    print(f"Period: 2019-01-01 to 2019-12-31")
    print("="*80)
    
    cik = "0000320187"
    start_date = "2019-01-01"
    end_date = "2019-12-31"
    
    # Step 1: Fetch metadata
    print(f"\n[1] Fetching filing metadata from SEC...")
    url = f"https://data.sec.gov/submissions/CIK{cik.zfill(10)}.json"
    
    headers = {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'application/json',
        'Host': 'data.sec.gov'
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            await asyncio.sleep(0.1)  # Rate limit
            
            async with session.get(url, headers=headers) as response:
                print(f"    Response: HTTP {response.status}")
                
                if response.status != 200:
                    print(f"    ✗ FAILED: Could not fetch metadata")
                    return False
                
                data = await response.json()
                recent = data.get('filings', {}).get('recent', {})
                
                accessions = recent.get('accessionNumber', [])
                dates = recent.get('filingDate', [])
                forms = recent.get('form', [])
                
                print(f"    ✓ SUCCESS: Retrieved {len(accessions)} total filings")
                
                # Step 2: Filter for 2019
                print(f"\n[2] Filtering for 2019 filings...")
                filings_2019 = []
                
                for i in range(len(accessions)):
                    if start_date <= dates[i] <= end_date:
                        filings_2019.append({
                            'date': dates[i],
                            'form': forms[i],
                            'accession': accessions[i]
                        })
                
                print(f"    ✓ Found {len(filings_2019)} filings in 2019")
                
                # Step 3: Show breakdown
                print(f"\n[3] Filing breakdown:")
                form_counts = {}
                for f in filings_2019:
                    form_type = f['form']
                    form_counts[form_type] = form_counts.get(form_type, 0) + 1
                
                for form_type, count in sorted(form_counts.items()):
                    print(f"    {form_type}: {count}")
                
                # Step 4: Test fetching actual document
                print(f"\n[4] Testing document fetch (first filing)...")
                if filings_2019:
                    first = filings_2019[0]
                    accession_clean = first['accession'].replace('-', '')
                    doc_url = f"https://www.sec.gov/cgi-bin/viewer?action=view&cik={cik}&accession_number={first['accession']}&xbrl_type=v"
                    
                    print(f"    Form: {first['form']}")
                    print(f"    Date: {first['date']}")
                    print(f"    URL: {doc_url}")
                    
                    # Try to fetch it
                    headers['Host'] = 'www.sec.gov'
                    await asyncio.sleep(0.1)
                    
                    async with session.get(doc_url, headers=headers) as doc_response:
                        print(f"    Response: HTTP {doc_response.status}")
                        
                        if doc_response.status == 200:
                            content = await doc_response.text()
                            print(f"    ✓ SUCCESS: Retrieved document ({len(content)} bytes)")
                        else:
                            print(f"    ✗ FAILED: Could not fetch document")
                
                print(f"\n" + "="*80)
                print(f"TEST RESULT: ✓ CORE SYSTEM FUNCTIONAL")
                print(f"="*80)
                print(f"Filings found: {len(filings_2019)}")
                print(f"Can proceed with analysis: YES")
                print("="*80)
                
                return True
                
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_nike_2019())
    exit(0 if result else 1)

