# SEC FORENSIC ANALYZER - PRODUCTION SYSTEM

## Universal Forensic Analysis for ANY SEC Filer

---

## Quick Start

```bash
# Analyze by CIK
python sec_forensic_analyzer.py --cik 320187 --year 2019

# Analyze by ticker
python sec_forensic_analyzer.py --ticker AAPL --year 2023

# Custom date range
python sec_forensic_analyzer.py --cik 320187 --start 2020-01-01 --end 2020-12-31

# Specific filing types only
python sec_forensic_analyzer.py --cik 320187 --year 2019 --filing-types 4,10-K,10-Q

# By category
python sec_forensic_analyzer.py --cik 320187 --year 2019 --category insider

# Custom output directory
python sec_forensic_analyzer.py --cik 320187 --year 2019 --output ./reports
```

---

## Command Line Options

| Option | Description | Example |
|--------|-------------|---------|
| `--cik` | Company CIK number | `--cik 320187` |
| `--ticker` | Stock ticker (auto-lookup CIK) | `--ticker AAPL` |
| `--year` | Full year analysis | `--year 2023` |
| `--start` | Start date (YYYY-MM-DD) | `--start 2020-01-01` |
| `--end` | End date (YYYY-MM-DD) | `--end 2020-12-31` |
| `--filing-types` | Comma-separated types | `--filing-types 4,10-K` |
| `--category` | Filing category | `--category insider` |
| `--output` | Output directory | `--output ./reports` |
| `--no-govinfo` | Disable GovInfo API | `--no-govinfo` |
| `--no-dual-agent` | Disable dual-agent | `--no-dual-agent` |

---

## Filing Categories

| Category | Filing Types |
|----------|--------------|
| `insider` | 3, 3/A, 4, 4/A, 5, 5/A |
| `periodic` | 10-K, 10-K/A, 10-Q, 10-Q/A, 20-F, 40-F |
| `current` | 8-K, 8-K/A, 6-K, 6-K/A |
| `proxy` | DEF 14A, DEFA14A, DEF 14C |
| `registration` | S-1, S-3, S-4, S-8, F-1, F-3 |
| `beneficial` | SC 13D, SC 13D/A, SC 13G, SC 13G/A |

---

## Violation Types Detected

### Section 16(a) - Insider Reporting
- Late Form 3 filings (>10 days)
- Late Form 4 filings (>2 business days)
- Late Form 5 filings
- Zero-dollar transactions (potential gift disguise)

### Section 10(b) - Anti-Fraud
- Material misstatements
- Restatements
- Revenue recognition issues

### SOX Compliance
- Section 302 certification deficiencies
- Section 404 internal control issues
- Section 906 criminal certification gaps

### Section 13(d) - Beneficial Ownership
- Late Schedule 13D filings
- Threshold crossing violations

---

## Output Files

The analyzer generates two reports for each run:

1. **Markdown Report** (`{COMPANY}_FORENSIC_ANALYSIS_{TIMESTAMP}.md`)
   - Human-readable DOJ-level investigation report
   - Executive summary
   - Per-filing detailed analysis
   - Criminal referral summary
   - Statutory framework

2. **JSON Report** (`{COMPANY}_FORENSIC_ANALYSIS_{TIMESTAMP}.json`)
   - Machine-readable data
   - Complete violation database
   - Evidence hashes for chain of custody

---

## Statutory Framework

All violations are grounded in specific U.S. Code and CFR:

| Statute | Name |
|---------|------|
| 15 U.S.C. § 78j(b) | Section 10(b) - Anti-Fraud |
| 15 U.S.C. § 78p(a) | Section 16(a) - Insider Reporting |
| 15 U.S.C. § 78m(d) | Section 13(d) - Beneficial Ownership |
| 15 U.S.C. § 7241 | SOX Section 302 |
| 15 U.S.C. § 7262 | SOX Section 404 |
| 17 CFR § 240.10b-5 | Rule 10b-5 |
| 18 U.S.C. § 1343 | Wire Fraud |
| 18 U.S.C. § 1348 | Securities Fraud |

---

## Example Companies

```bash
# Technology
python sec_forensic_analyzer.py --ticker AAPL --year 2023
python sec_forensic_analyzer.py --ticker MSFT --year 2023
python sec_forensic_analyzer.py --ticker GOOGL --year 2023

# Financial
python sec_forensic_analyzer.py --ticker JPM --year 2023
python sec_forensic_analyzer.py --ticker GS --year 2023

# Healthcare
python sec_forensic_analyzer.py --ticker JNJ --year 2023
python sec_forensic_analyzer.py --ticker PFE --year 2023

# Retail
python sec_forensic_analyzer.py --cik 320187 --year 2019  # Nike
python sec_forensic_analyzer.py --ticker WMT --year 2023
```

---

## System Requirements

- Python 3.10+
- aiohttp
- SEC EDGAR API access
- GovInfo API key (optional, for statute cross-reference)
- Dual-agent credentials (optional, for enhanced analysis)

---

## Integrations

| Component | Status | Purpose |
|-----------|--------|---------|
| SEC EDGAR | ✅ Live | Filing data source |
| GovInfo API | ✅ Ready | Statute verification |
| Dual-Agent | ✅ Ready | OpenAI + Anthropic validation |

---

*SEC Forensic Analyzer v1.0 - Production Ready*

