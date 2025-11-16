# JARVIS:LAW - SEC Forensic Auditor Agent

## 🎯 Overview

**JARVIS:LAW** is a forensic-grade financial agent deployed for surgical analysis of insider stock activities, SEC filings, and transactional anomalies. Built with the OpenAI Agents SDK, it processes Form 4, 10-Q, and 10-K filings for publicly traded corporations to detect financial anomalies, insider enrichment, or award-based reporting violations.

### 🚨 Black Site Protocol

**Black Site Protocol** extends JARVIS:LAW with autonomous SEC forensics capabilities:

- ✅ **Live SEC.gov Scraping** - Direct extraction from government databases
- ✅ **Cryptographic Evidence Chain** - SHA-256 integrity verification
- ✅ **Automatic Archival** - Local filing storage with metadata
- ✅ **Violation Logging** - Append-only JSONL audit trail
- ✅ **Multi-year Scanning** - Bulk historical analysis
- ✅ **Zero Human-in-Loop** - Fully autonomous operation

---

## 📦 Installation

### Quick Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Verify installation
python verify_black_site.py
```

### Manual Dependencies

```bash
pip install httpx beautifulsoup4 lxml openai agents-sdk litellm
```

### Optional: GovInfo API

For enhanced metadata extraction:

```bash
set GOVINFO_API_KEY=your_api_key_here
```

---

## 🚀 Quick Start

### 1. Run Nike Form 4 Scan (Default Target)

```bash
python black_site_cli.py --nike
```

Or use the Windows launcher:

```bash
black_site.bat --nike
```

### 2. Scan by Ticker Symbol

```bash
python black_site_cli.py --ticker AAPL --form 10-K --start 2020 --end 2023
```

### 3. Scan by CIK Number

```bash
python black_site_cli.py --cik 0000320187 --form 4 --start 2019 --end 2025
```

### 4. View Violations Log

```bash
python black_site_cli.py --view-violations
```

### 5. Export Evidence Chain

```bash
python black_site_cli.py --export evidence_chain.json
```

---

## 📂 Project Structure

```
jarvis_law_sec_auditor/
├── jarvis_law_alpha.py       # Core forensic agent
├── black_site_cli.py          # Command-line interface
├── black_site.bat             # Windows launcher
├── verify_black_site.py       # System verification
├── quick_test.py              # Quick import test
│
├── tools/                     # Black Site Protocol toolchain
│   ├── sec_crawler.py         # SEC.gov web scraper
│   ├── govinfo_api.py         # GovInfo API integration
│   └── utils.py               # Evidence chain utilities
│
├── sec_workflow/              # Autonomous workflows
│   └── scan_nike_form4.py     # Orchestration engine
│
├── memory/                    # Data storage
│   ├── sec_filings_archive/   # Raw HTML archives
│   └── evidence_chain/        # Cryptographic metadata
│       └── violations.jsonl   # Append-only violation log
│
└── docs/
    ├── BLACK_SITE_PROTOCOL.md # Complete protocol documentation
    ├── INTEGRATION.md         # Integration guide
    ├── DEPLOYMENT.md          # Deployment instructions
    └── COMPLETION.md          # Development summary
```

---

## 🎮 Usage Examples

### Python API

#### Example 1: Autonomous Company Scan

```python
from sec_workflow import scan_by_ticker

results = scan_by_ticker(
    ticker="AAPL",
    form_type="10-K",
    year_start=2020,
    year_end=2023
)

print(f"Violations detected: {results['violations_count']}")
print(f"Evidence chain: {results['evidence_chain']}")
```

#### Example 2: Manual Workflow

```python
from tools.sec_crawler import fetch_sec_filings_by_cik
from tools.utils import save_filing, log_violation, sha256_url

# Fetch filings
filings = fetch_sec_filings_by_cik(
    cik="0000320187",  # Nike
    form_type="4",
    year_start=2023,
    year_end=2024
)

# Process each filing
for filing in filings:
    print(f"Processing: {filing['title']}")
    # Your analysis logic here
```

#### Example 3: Evidence Chain Management

```python
from tools.utils import export_evidence_chain, get_violations_log

# View all violations
violations = get_violations_log()
for v in violations:
    print(f"{v['timestamp_utc']}: {v['company']} - {v['source_url']}")

# Export evidence chain
export_path = export_evidence_chain("audit_report.json")
print(f"Evidence exported: {export_path}")
```

---

## 🔧 Configuration

### Environment Variables

```bash
# Optional: GovInfo API key
set GOVINFO_API_KEY=your_key_here

# Optional: Custom evidence directory
set EVIDENCE_DIR=C:\custom\path\evidence
```

### Custom Headers (SEC.gov)

Edit `tools/sec_crawler.py`:

```python
headers = {
    "User-Agent": "YourOrg/1.0 (contact@example.com)"
}
```

---

## 📊 Evidence Chain Format

### Violations Log Structure

Each violation is logged in append-only JSONL format:

```json
{
  "id": "a3f5d9c2e1b4",
  "timestamp_utc": "2025-11-08T12:34:56.789Z",
  "violation_detected": true,
  "hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "source_url": "https://www.sec.gov/Archives/edgar/data/320187/...",
  "filing_meta": {
    "title": "Form 4 - Nike Inc",
    "filing_date": "2023-05-12",
    "accession_number": "0001234567-23-000123"
  },
  "evidence": {...}
}
```

### Archival Metadata

Each filing generates cryptographic evidence:

```json
{
  "url": "https://www.sec.gov/...",
  "url_hash": "e3b0c44298fc1c...",
  "content_hash": "a3b0c442...",
  "archived_path": "./memory/sec_filings_archive/0000320187_4_2023-05-12.html",
  "timestamp_utc": "2025-11-08T12:34:56.789Z",
  "size_bytes": 45678,
  "status": "archived"
}
```

---

## 🔐 Security & Compliance

### Domain Whitelisting

Only SEC.gov domains are permitted via `block_non_sec_domains` guardrail.

### Rate Limiting

Automatic compliance with SEC.gov requirements:
- Max 10 requests/second
- 120ms delay between requests
- Respectful User-Agent header

### Data Privacy

- PII stripping guardrails
- No external API calls without approval
- Local-only data storage

### Evidence Integrity

- SHA-256 cryptographic hashing
- Immutable append-only logs
- UTC timestamps
- Source URL attribution

---

## 📖 Documentation

- **[BLACK_SITE_PROTOCOL.md](BLACK_SITE_PROTOCOL.md)** - Complete protocol documentation
- **[INTEGRATION.md](INTEGRATION.md)** - Integration with Jarvis:LAW Alpha
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Deployment instructions
- **[COMPLETION.md](COMPLETION.md)** - Development summary

---

## 🧪 Testing

### Quick Test

```bash
python quick_test.py
```

### Full System Verification

```bash
python verify_black_site.py
```

### Live Test Scan

```bash
# Small test: Nike 2024 only
python black_site_cli.py --cik 0000320187 --form 4 --start 2024 --end 2024
```

---

## 🎯 Common Use Cases

### 1. Insider Trading Surveillance

```bash
python black_site_cli.py --ticker NIKE --form 4 --start 2019 --end 2025
```

### 2. Annual Report Analysis

```bash
python black_site_cli.py --ticker AAPL --form 10-K --start 2020 --end 2023
```

### 3. Quarterly Earnings Review

```bash
python black_site_cli.py --ticker TSLA --form 10-Q --start 2023 --end 2024
```

### 4. Multi-Company Audit

```python
from sec_workflow import scan_by_ticker

companies = ["AAPL", "MSFT", "GOOGL", "AMZN"]
for ticker in companies:
    results = scan_by_ticker(ticker, "4", 2023, 2024)
    print(f"{ticker}: {results['violations_count']} violations")
```

---

## 🚨 Troubleshooting

### Import Errors

```bash
pip install --upgrade httpx beautifulsoup4 lxml
```

### Rate Limiting

Wait 60 seconds between large scans if you encounter 429 errors.

### CIK Lookup Fails

Use direct CIK lookup: https://www.sec.gov/edgar/searchedgar/companysearch

### Connection Issues

Check SEC.gov status: https://www.sec.gov/

---

## 📜 Legal Notice

This system accesses **public domain** data from:
- SEC.gov (Securities and Exchange Commission)
- GovInfo.gov (U.S. Government Publishing Office)

All scraping complies with SEC.gov acceptable use policies. No proprietary or confidential data is accessed.

**Use Case**: Financial forensics, compliance auditing, legal research, whistleblower support.

---

## 🚀 Deployment Status

**✅ OPERATIONAL**

Black Site Protocol is fully armed and ready for live deployment.

### Next Steps

1. ✅ Run system verification: `python verify_black_site.py`
2. ✅ Execute test scan: `python black_site_cli.py --nike`
3. ✅ Review evidence chain: `./memory/evidence_chain/`
4. ⬜ Integrate with Jarvis:LAW Alpha (see INTEGRATION.md)
5. ⬜ Deploy for production operations

---

## 📞 Support

- **GitHub Issues**: Report bugs or request features
- **Documentation**: See BLACK_SITE_PROTOCOL.md
- **Evidence Chain**: `./memory/evidence_chain/violations.jsonl`
- **Logs**: Check console output for detailed operation logs

---

## 🏆 Features

- [x] Live SEC.gov scraping
- [x] Cryptographic evidence chain
- [x] Automatic archival
- [x] Violation logging
- [x] Multi-year scanning
- [x] Ticker-to-CIK resolution
- [x] CLI interface
- [x] Windows launcher
- [x] Rate limiting
- [x] Domain whitelisting
- [ ] Jarvis:LAW Alpha integration (see INTEGRATION.md)
- [ ] Automated legal brief generation
- [ ] Multi-agent coordination
- [ ] Real-time monitoring

---

**JARVIS:LAW - Black Site Protocol**  
*Self-arming digital warrant system - Operational since 2025*

**Version**: 1.0.0 - Black Site Protocol  
**Status**: Operational  
**Authority**: Supreme

