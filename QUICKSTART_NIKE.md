# JLAW Command Quick Start Guide

## Running JLAW with NIKE (2019 Analysis)

This guide covers how to run JLAW forensic analysis for NIKE, Inc. for the year 2019.

## Prerequisites

1. **Check Setup**:
   ```bash
   python setup_check.py
   ```

2. **Verify Company Lookup**:
   ```bash
   python verify_command.py
   ```

3. **Run End-to-End Test**:
   ```bash
   python test_nike_command.py
   ```

## Command Options

### Option 1: Full Command (Recommended)
```bash
python JLAW_UNIFIED.py --cik 320187 --company "NIKE" --year 2019 --auto
```

### Option 2: Ticker Only
```bash
python JLAW_UNIFIED.py --company "NKE" --year 2019 --auto
```

### Option 3: Company Name Only
```bash
python JLAW_UNIFIED.py --company "NIKE" --year 2019 --auto
```

### Option 4: Interactive Mode
```bash
python JLAW_UNIFIED.py
# Then enter: NIKE (or NKE)
# Year: 2019
# Auto mode: y
```

## What Happens

1. **Phase 1**: Configuration & Target Acquisition
   - Resolves "NIKE" to "NIKE, Inc." (CIK: 320187)
   - Sets date range: 2019-01-01 to 2019-12-31
   - Validates SEC API configuration

2. **Phase 2**: SEC EDGAR Data Collection
   - Fetches filings: 10-K, 10-Q, 8-K, DEF 14A, Form 4, etc.
   - Applies rate limiting (9 req/sec)

3. **Phase 3**: Document Parsing & Indexing
   - Extracts text from SEC filings
   - Builds vector search index

4. **Phase 4**: 15-Node Recursive Analysis
   - Node 1: Form 4 Insider Trading
   - Node 2: DEF 14A Compensation Analysis
   - ... (13 more nodes)

5. **Phases 5-9**: Pattern Detection, AI Validation, Evidence Chain, Report Generation

## Command Flags

- `--auto`: Run without confirmation prompts (recommended for batch)
- `--strict`: Enable DOJ-grade phase gates (halt on critical failures)
- `--strategy triage`: Fast 5-10 minute assessment
- `--strategy standard`: Standard 15-30 minute analysis
- `--strategy doj_referral`: Exhaustive 30-60 minute analysis
- `--type insider_trading`: Optimize for insider trading detection
- `--output DIR`: Specify output directory (default: ./output)
- `--no-pdf`: Skip PDF report generation

## Examples

### Standard Analysis
```bash
python JLAW_UNIFIED.py --company "NIKE" --year 2019 --auto
```

### Fast Triage (5-10 minutes)
```bash
python JLAW_UNIFIED.py --company "NIKE" --year 2019 --strategy triage --auto
```

### DOJ-Grade Strict Mode
```bash
python JLAW_UNIFIED.py --company "NIKE" --year 2019 --strict --auto
```

### Insider Trading Focus
```bash
python JLAW_UNIFIED.py --company "NIKE" --year 2019 --type insider_trading --auto
```

## Output Location

Results are saved to:
```
./output/
├── forensic_analysis_YYYYMMDD_HHMMSS.log
├── evidence_chain/
├── dossier_NIKE_Inc_2019.pdf  (if PDF generation enabled)
└── raw_data/
```

## Troubleshooting

### Issue: "SEC_USER_AGENT not set"
**Solution**: 
```bash
cp .env.example .env
# Edit .env and set: SEC_USER_AGENT=YourCompany/1.0 (your-email@company.com)
```

### Issue: "No module named 'aiohttp'"
**Solution**:
```bash
pip install -r requirements.txt
```

### Issue: "Company not found"
**Solution**: Use exact ticker or name from lookup table:
- ✅ "NIKE", "nike", "NKE", "nke"
- ❌ "Nike Corp", "NIKE INC"

## Supported Companies

JLAW includes built-in lookup for these companies:

| Company   | Ticker | CIK     | Usage Example              |
|-----------|--------|---------|----------------------------|
| Nike      | NKE    | 320187  | `--company "NIKE"`         |
| Apple     | AAPL   | 320193  | `--company "AAPL"`         |
| Microsoft | MSFT   | 789019  | `--company "MSFT"`         |
| Tesla     | TSLA   | 1318605 | `--company "TESLA"`        |
| Amazon    | AMZN   | 1018724 | `--company "AMZN"`         |
| Meta      | META   | 1326801 | `--company "META"`         |
| Google    | GOOGL  | 1652044 | `--company "GOOGLE"`       |
| Netflix   | NFLX   | 1065280 | `--company "NFLX"`         |
| Nvidia    | NVDA   | 1045810 | `--company "NVIDIA"`       |

## Need Help?

- Check setup: `python setup_check.py`
- Verify lookup: `python verify_command.py`
- Run tests: `python test_nike_command.py`
- Read docs: `README.md`, `HOLY_GRAIL_PIPELINE.md`
