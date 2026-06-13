# SEC Filings

This directory holds SEC EDGAR filings retrieved for forensic analysis.

## Included Filing Types

- 10-K (annual reports)
- 10-Q (quarterly reports)
- DEF 14A (proxy statements / executive compensation)
- Form 4 (insider transactions)
- 8-K (material events)
- SC 13D / SC 13G (beneficial ownership)
- 13F-HR (institutional holdings)
- Form 144 (restricted stock sales)
- ESG / sustainability disclosures

## File Naming Convention

```
{CIK}_{form_type}_{filing_date}_{accession_number}.{ext}
```

Example: `0000320187_10-K_2019-07-26_0000320187-19-000009.htm`

## Notes

- Files in this directory are source documents. Do not modify them.
- Register each file in the evidence manifest with its SHA-256 hash before analysis.
- Filing dates and accession numbers are available from SEC EDGAR's EDGAR Full-Text Search and EDGAR API.
