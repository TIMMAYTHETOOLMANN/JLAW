# Nike Unified Analysis - Quick Start Guide

## Overview

This guide explains how to run the comprehensive Nike 2019 forensic analysis and understand the output.

## Running the Analysis

### Option 1: One-Click Execution (Recommended)

```bash
python "Execute Nike Unified Analysis.py"
```

This is the simplest way to run the analysis. The script will:
- Check dependencies and report status
- Run complete 13-phase forensic analysis
- Generate comprehensive reports in multiple formats
- Show progress and final results

### Option 2: Using the PowerShell Wrapper (Windows)

```powershell
PowerShell -ExecutionPolicy Bypass -File .\one_click_analyze.ps1 -Ticker NKE -Year 2019
```

### Option 3: Direct Command Line

```bash
python jlaw_forensic.py --ticker NKE --year 2019 --output-dir output --verbose
```

## Understanding the Output

### Output Structure

When the analysis completes, you'll get TWO types of output:

#### 1. Structured Directory (Primary Output)

```
output/NIKE_Inc_2019_FORENSIC_ANALYSIS_YYYYMMDD_HHMMSS/
├── FORENSIC_REPORT.md          # Main comprehensive report (markdown)
├── executive_summary.md         # 2-page executive brief
├── machine_readable/
│   ├── summary.json            # High-level statistics
│   ├── violations.json         # All violations in JSON format
│   ├── parsed_documents.json   # Document metadata
│   └── ...                     # Additional data files
├── evidence/
│   ├── chain_of_custody.json   # Evidence tracking
│   └── source_documents/       # Original documents
└── appendices/
    └── methodology.md          # Analysis methodology
```

#### 2. Root Directory Files (Backwards Compatible)

```
NIKE_Inc_2019_FORENSIC_ANALYSIS_YYYYMMDD_HHMMSS.md    # Copy of main report
NIKE_Inc_2019_FORENSIC_ANALYSIS_YYYYMMDD_HHMMSS.json  # Copy of summary JSON
```

### What You Get

#### FORENSIC_REPORT.md Contains:
- **Executive Summary**: High-level findings and statistics
- **Statutory Framework**: Legal citations and penalties
- **Per-Filing Analysis**: Detailed analysis of each SEC filing
  - Document URLs and accession numbers
  - Violations identified with evidence
  - Exact quotes from documents
  - Prosecutorial merit assessment
  - Estimated damages
- **Severity Distribution**: Breakdown by violation severity
- **Recommendations**: Action items based on findings

#### Machine-Readable Files:
- **summary.json**: Key statistics for dashboards/automation
- **violations.json**: All violations with full metadata
- **chain_of_custody.json**: Evidence tracking for legal proceedings

## What Makes Output "Comprehensive"

A comprehensive report includes:

1. **Executive Summary** ✓
   - Total filings analyzed
   - Violation counts by type
   - Criminal referral recommendations
   - Estimated damages

2. **Statutory Analysis** ✓
   - Citations to 15 U.S.C., 17 CFR, 18 U.S.C.
   - GovInfo.gov references
   - Penalty ranges

3. **Per-Filing Details** ✓
   - Filing metadata (accession number, date, type)
   - Violation descriptions
   - Evidence with exact quotes
   - Document URLs for verification
   - Severity assessment

4. **Multiple Output Formats** ✓
   - Human-readable markdown
   - Machine-readable JSON
   - Evidence chain documentation

## Expected Results (Nike 2019 Baseline)

The baseline analysis should find approximately:
- **89 filings** analyzed
- **54-97 violations** identified (depending on configuration)
- **26-29 late Form 4 filings**
- **19-66 zero-dollar transactions**
- **4-5 material misstatements**
- **1 SOX 302 violation**
- **$61-65 million** in estimated damages

## Common Issues and Solutions

### Issue: "Module not found" errors

**Solution**: Install dependencies
```bash
pip install -r requirements.txt
```

### Issue: "Only JSON output, no markdown"

**Solution**: Check the output directory structure. The markdown file is at:
```
output/NIKE_Inc_2019_FORENSIC_ANALYSIS_*/FORENSIC_REPORT.md
```

NOT in the root directory by default (though a copy is created there too).

### Issue: "Report seems incomplete"

**Solution**: Check the file size:
- Comprehensive markdown reports are typically 50KB-200KB
- Should contain 2,000-5,000 lines
- If file is < 10KB, check error logs

Use this to verify:
```bash
wc -l output/*/FORENSIC_REPORT.md
```

### Issue: "Analysis takes too long"

**Explanation**: Normal! The analysis:
- Fetches 89 SEC filings from EDGAR
- Parses HTML/XML documents
- Analyzes each filing in detail
- Expected time: 5-15 minutes

To speed up (at cost of completeness):
```bash
python jlaw_forensic.py --ticker NKE --year 2019 --filing-types "4,10-K"
```

## Validating Report Quality

A production-quality report should have:

1. **File exists and is substantial**
   ```bash
   ls -lh output/*/FORENSIC_REPORT.md
   # Should be 50KB+
   ```

2. **Contains all sections**
   ```bash
   grep -c "##" output/*/FORENSIC_REPORT.md
   # Should return 100+ (section headers)
   ```

3. **Has violation details**
   ```bash
   grep -c "Violation [0-9]:" output/*/FORENSIC_REPORT.md
   # Should return 50+ (violation entries)
   ```

4. **Includes evidence quotes**
   ```bash
   grep -c "EXACT QUOTE FROM DOCUMENT" output/*/FORENSIC_REPORT.md
   # Should return 50+ (evidence citations)
   ```

## Module Availability Status

When you run the analysis, you'll see:

```
MODULE STATUS:
  ✓ Unified 13-Phase Pipeline: Available
  ✓ Unified Report Generator:  Available
  ✓ Baseline Production System: Available
```

Or:

```
MODULE STATUS:
  ⚠ Unified 13-Phase Pipeline: Not Available (using baseline)
  ⚠ Unified Report Generator:  Not Available (using baseline)
  ✓ Baseline Production System: Available (guaranteed comprehensive reports)
```

**Both modes produce comprehensive reports!** The unified mode adds:
- ML fraud detection scores
- Temporal anomaly detection
- Cross-document contradiction detection
- Enhanced linguistic analysis

But the baseline mode (which always runs) includes:
- Complete Form 4 violation detection
- 10-K/10-Q analysis
- Material misstatement detection
- SOX 302 compliance checks
- Full statutory framework

## Getting Help

If reports are not comprehensive:

1. Check the log file: `unified_complete_YYYYMMDD_HHMMSS.log`
2. Run with verbose mode: `python jlaw_forensic.py --ticker NKE --year 2019 --verbose`
3. Verify output directory contents: `ls -R output/*/`
4. Check file sizes: `du -h output/*/`

## System Requirements

- Python 3.8+
- Internet connection (for SEC EDGAR access)
- 500MB+ free disk space
- Recommended: 8GB+ RAM for full dataset

## Dependencies

Core (required for baseline):
- aiohttp
- python-dotenv
- beautifulsoup4
- lxml
- python-dateutil

Enhanced (optional):
- numpy
- pandas
- aiofiles
- scikit-learn
- torch / transformers

Install all:
```bash
pip install -r requirements.txt
```

Or just core:
```bash
pip install aiohttp python-dotenv beautifulsoup4 lxml python-dateutil
```
