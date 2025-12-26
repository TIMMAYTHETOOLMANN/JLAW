#!/usr/bin/env python3
"""Check 10-Q filings for NIKE in 2019."""
import asyncio
from datetime import date
from src.integrations.sec_edgar.edgar_client import SECEdgarClient

async def check_filings():
    async with SECEdgarClient() as client:
        filings = await client.get_filings(
            cik="320187",
            form_types=["10-Q"],
            start_date=date(2019, 1, 1),
            end_date=date(2019, 12, 31)
        )
        print(f"Total 10-Q filings found: {len(filings)}")
        for f in filings:
            print(f"  - {f.form_type} filed {f.filing_date} (accession: {f.accession_number})")

        # Check NIKE's fiscal year - ends May 31
        print("\nNote: NIKE fiscal year ends May 31")
        print("Fiscal 2019 would be June 1, 2018 - May 31, 2019")
        print("Fiscal 2020 would be June 1, 2019 - May 31, 2020")

        # Check broader date range
        print("\n--- Checking broader range (2018-2020) ---")
        filings_broad = await client.get_filings(
            cik="320187",
            form_types=["10-Q"],
            start_date=date(2018, 6, 1),
            end_date=date(2020, 5, 31)
        )
        print(f"Total 10-Q filings (2018-2020): {len(filings_broad)}")
        for f in filings_broad:
            print(f"  - {f.form_type} filed {f.filing_date}")

if __name__ == "__main__":
    asyncio.run(check_filings())

