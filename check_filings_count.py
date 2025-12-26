"""Script to verify total SEC filings count for Nike 2019."""
import asyncio
from src.integrations.sec_edgar.edgar_client import SECEdgarClient


async def check_filings():
    """Query SEC EDGAR for all Nike 2019 filings."""
    async with SECEdgarClient(user_agent='JLAW-Forensics/3.0 forensics@jlaw.io') as client:
        submissions = await client.get_submissions('320187')

        # Get all filings in 2019
        recent = submissions.get('filings', {}).get('recent', {})
        accessions = recent.get('accessionNumber', [])
        forms = recent.get('form', [])
        dates = recent.get('filingDate', [])

        count_2019 = 0
        filings_by_type = {}
        all_filings = []

        for acc, form, filing_date in zip(accessions, forms, dates):
            if filing_date.startswith('2019'):
                count_2019 += 1
                filings_by_type[form] = filings_by_type.get(form, 0) + 1
                all_filings.append({
                    'accession': acc,
                    'form': form,
                    'date': filing_date
                })

        print(f'=' * 60)
        print(f'NIKE INC (CIK: 320187) - 2019 SEC FILINGS SUMMARY')
        print(f'=' * 60)
        print(f'\nTotal filings in 2019: {count_2019}')
        print()
        print('Breakdown by filing type:')
        print('-' * 40)
        for form, count in sorted(filings_by_type.items(), key=lambda x: -x[1]):
            print(f'  {form:15s}: {count:3d}')
        print('-' * 40)
        print(f'  {"TOTAL":15s}: {count_2019:3d}')

        # List all filings
        print(f'\n{"=" * 60}')
        print('ALL FILINGS:')
        print(f'{"=" * 60}')
        for i, f in enumerate(all_filings, 1):
            print(f'{i:3d}. {f["date"]} | {f["form"]:15s} | {f["accession"]}')

        return count_2019, filings_by_type, all_filings


if __name__ == '__main__':
    asyncio.run(check_filings())

