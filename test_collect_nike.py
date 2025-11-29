"""
Minimal Nike Filing Collector
Just collects filings and prints count - no analysis
"""
import asyncio
import sys
sys.path.insert(0, 'C:/Users/timot/IdeaProjects/JLAW')

async def main():
    print("Starting...")
    
    from src.forensics.sec_edgar_analyzer import SECForensicAnalyzer
    
    analyzer = SECForensicAnalyzer(user_agent="test@test.com")
    
    print("Collecting Nike 2019 filings from SEC EDGAR...")
    
    # Direct SEC EDGAR fetch
    import requests
    from datetime import datetime
    
    url = f"https://data.sec.gov/submissions/CIK0000320187.json"
    headers = {'User-Agent': 'test@test.com'}
    
    print(f"Fetching: {url}")
    response = requests.get(url, headers=headers)
    data = response.json()
    
    filings = data.get('filings', {}).get('recent', {})
    accessions = filings.get('accessionNumber', [])
    filing_dates = filings.get('filingDate', [])
    form_types = filings.get('form', [])
    
    # Filter to 2019
    filings_2019 = []
    for i, date in enumerate(filing_dates):
        if date.startswith('2019'):
            filings_2019.append({
                'form_type': form_types[i],
                'filing_date': date,
                'accession': accessions[i]
            })
    
    print(f"\nFound {len(filings_2019)} Nike filings from 2019")
    
    # Count by type
    type_counts = {}
    for f in filings_2019:
        ft = f['form_type']
        type_counts[ft] = type_counts.get(ft, 0) + 1
    
    print("\nBreakdown by type:")
    for ft, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {ft}: {count}")
    
    print(f"\nTotal: {len(filings_2019)} filings")
    print("SUCCESS!")
    
    return filings_2019

if __name__ == "__main__":
    result = asyncio.run(main())

