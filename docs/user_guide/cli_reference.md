# JLAW CLI Reference Guide

## Overview

`jlaw_cli.py` is the unified command-line interface for JLAW (Justice Law Analytics Workbench), providing DOJ-grade SEC forensic analysis capabilities through a modular, maintainable architecture.

**Version:** 3.0.0

## Quick Start

```bash
# Basic analysis
python jlaw_cli.py --cik 0000320187 --company "Apple Inc." --year 2019

# Strict forensic mode (DOJ-grade)
python jlaw_cli.py --cik 0000320187 --year 2019 --mode forensic --strict --auto

# Pre-flight validation
python jlaw_cli.py --validate-only

# Dry run (show execution plan)
python jlaw_cli.py --cik 0000320187 --year 2019 --dry-run
```

## Installation

Ensure dependencies are installed:

```bash
pip install -r requirements.txt
```

Download required ML models:

```bash
python jlaw_cli.py --download-models
```

## Command-Line Options

### Target Selection

| Option | Description | Example |
|--------|-------------|---------|
| `--cik CIK` | Company CIK number | `--cik 0000320187` |
| `--company NAME` | Company name or ticker | `--company "NIKE"` |

The `--company` flag supports auto-lookup for known tickers (NIKE, NKE, AAPL, etc.).

### Date Range

| Option | Description | Example |
|--------|-------------|---------|
| `--year YYYY` | Analysis year (Jan 1 - Dec 31) | `--year 2019` |
| `--start-date YYYY-MM-DD` | Start date | `--start-date 2019-01-01` |
| `--end-date YYYY-MM-DD` | End date | `--end-date 2019-12-31` |

### Execution Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| `standard` | Full 9-phase analysis | Default comprehensive analysis |
| `auto` | Intelligent triage | Resource-constrained environments |
| `forensic` | DOJ-grade forensic | Court-admissible evidence |
| `batch` | Batch processing | Multiple targets from file |
| `daemon` | Continuous monitoring | Real-time watchlist monitoring |

**Usage:**
```bash
--mode forensic
```

### Execution Flags

| Flag | Description |
|------|-------------|
| `--auto` | Auto mode (no user confirmations) |
| `--strict` | Strict execution (enforce phase gates, halt on failures) |
| `--verbose` | Enable verbose output |
| `--debug` | Enable debug logging |

### Investigation Focus

Optimize node execution for specific investigation types:

| Type | Optimizes For |
|------|---------------|
| `comprehensive` | All 15 nodes (default) |
| `insider-trading` | Form 4, 144, short-swing analysis |
| `compensation` | DEF 14A, proxy statements |
| `sox-compliance` | 10-K, SOX certifications |
| `tax-exposure` | IRC §83, equity grants |
| `market-timing` | Material events, market correlation |

**Usage:**
```bash
--investigation insider-trading
```

### Advanced Features

| Flag | Description |
|------|-------------|
| `--validate-only` | Run pre-flight checks only (no analysis) |
| `--dry-run` | Generate execution plan without running |
| `--profile` | Enable performance profiling |
| `--export-config PATH` | Export effective configuration to file |

### Output Configuration

| Option | Description | Default |
|--------|-------------|---------|
| `--output-dir PATH` | Output directory | `output` |
| `--no-pdf` | Skip PDF report generation | False |

### ML Model Management

| Command | Description |
|---------|-------------|
| `--download-models` | Download all required ML models and exit |
| `--verify-models` | Verify cached ML models and exit |
| `--clear-model-cache` | Clear ML model cache and exit |

### System Commands

| Flag | Description |
|------|-------------|
| `--check-deps` | Check dependencies and exit |
| `--version` | Print version and exit |

### Batch Processing

```bash
--batch targets.json
```

**Batch File Format (JSON):**
```json
{
  "targets": [
    {
      "cik": "0000320187",
      "company": "Apple Inc.",
      "start_date": "2019-01-01",
      "end_date": "2019-12-31"
    },
    {
      "cik": "0000320193",
      "company": "NIKE, Inc.",
      "start_date": "2019-01-01",
      "end_date": "2019-12-31"
    }
  ]
}
```

### Daemon Mode

Continuous monitoring of watchlist:

```bash
--daemon --watchlist companies.txt
```

**Watchlist Format:**
```
0000320187  # Apple Inc.
0000320193  # NIKE, Inc.
0001318605  # Tesla, Inc.
```

## Usage Examples

### Example 1: Basic Analysis

```bash
python jlaw_cli.py \
  --cik 0000320187 \
  --company "Apple Inc." \
  --year 2019
```

### Example 2: Strict Forensic Analysis (DOJ-Grade)

```bash
python jlaw_cli.py \
  --cik 0000320187 \
  --company "Apple Inc." \
  --start-date 2019-01-01 \
  --end-date 2019-12-31 \
  --mode forensic \
  --strict \
  --auto
```

### Example 3: Pre-Flight Validation

```bash
python jlaw_cli.py --validate-only
```

Expected output:
```
✅ SEC User-Agent: Valid
✅ OPENAI_API_KEY: Configured
✅ ANTHROPIC_API_KEY: Configured
⚠️  POLYGON_API_KEY: Not configured (optional)
✅ All ML models cached
✅ All pre-flight checks passed!
```

### Example 4: Dry Run (Execution Plan)

```bash
python jlaw_cli.py \
  --cik 0000320187 \
  --year 2019 \
  --dry-run
```

Shows planned phases, nodes, and estimated time without running analysis.

### Example 5: Export Configuration

```bash
python jlaw_cli.py --export-config config.json
```

### Example 6: Download ML Models

```bash
python jlaw_cli.py --download-models
```

Expected output:
```
🤖 JLAW ML Model Downloader

Cache directory: /home/user/.cache/jlaw/models

⏬ Downloading deberta-v3-base (~440 MB)...
✅ Downloaded: deberta-v3-base
⏬ Downloading finbert (~440 MB)...
✅ Downloaded: finbert
✅ All models downloaded successfully!
```

### Example 7: Insider Trading Investigation

```bash
python jlaw_cli.py \
  --cik 0000320187 \
  --year 2019 \
  --investigation insider-trading \
  --output-dir investigations/apple_insider_trading
```

### Example 8: Batch Analysis

```bash
python jlaw_cli.py \
  --batch targets.json \
  --mode batch \
  --output-dir batch_output
```

### Example 9: Verbose Debugging

```bash
python jlaw_cli.py \
  --cik 0000320187 \
  --year 2019 \
  --debug \
  --verbose
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General failure |
| 130 | Interrupted by user (Ctrl+C) |

## Environment Variables

Required environment variables (set in `.env` file):

```bash
# SEC EDGAR API (REQUIRED)
SEC_USER_AGENT="YourCompany contact@example.com"

# AI Agents (Optional, for Phase 6)
OPENAI_API_KEY="sk-..."
ANTHROPIC_API_KEY="sk-ant-..."

# Market Data (Optional, for Node 15)
POLYGON_API_KEY="..."
```

## Output Structure

```
output/
├── forensic_analysis_YYYYMMDD_HHMMSS.log
├── dossier_CIK-XXXXXXX_YYYYMMDD_HHMMSS.json
├── dossier_CIK-XXXXXXX_YYYYMMDD_HHMMSS.pdf
├── evidence_chain/
│   ├── custody_log.json
│   ├── merkle_tree.json
│   └── hashes/
└── violations/
    ├── critical_violations.json
    └── all_violations.json
```

## Troubleshooting

### Issue: "SEC_USER_AGENT not configured"

**Solution:** Set SEC_USER_AGENT in `.env` file:
```bash
SEC_USER_AGENT="YourCompany contact@example.com"
```

### Issue: "Missing ML models"

**Solution:** Download models:
```bash
python jlaw_cli.py --download-models
```

### Issue: "Configuration validation failed"

**Solution:** Run validation checks:
```bash
python jlaw_cli.py --validate-only
```

### Issue: "Analysis failed at phase X"

**Solution:** Run with debug logging:
```bash
python jlaw_cli.py --cik XXX --year 2019 --debug --verbose
```

## Migration from JLAW_UNIFIED.py

The legacy `JLAW_UNIFIED.py` is deprecated. To migrate:

**Old:**
```bash
python JLAW_UNIFIED.py --cik 320187 --year 2019 --auto --strict
```

**New:**
```bash
python jlaw_cli.py --cik 320187 --year 2019 --auto --strict
```

See `docs/MIGRATION_V2_TO_V3.md` for complete migration guide.

## Performance Tips

1. **Pre-download models** before first run to avoid cold-start delays
2. **Use `--investigation` flag** to optimize node execution
3. **Enable `--strict` mode** for production DOJ-grade analysis
4. **Use batch mode** for analyzing multiple targets efficiently
5. **Monitor with `--profile`** to identify performance bottlenecks

## Support

For issues, see:
- GitHub Issues: https://github.com/TIMMAYTHETOOLMANN/JLAW/issues
- Documentation: `docs/`
- Examples: `examples/`

## Version History

- **v3.0.0** (2024-12-28): Modular CLI entry point, ML model pre-loading
- **v2.x**: Monolithic JLAW_UNIFIED.py (deprecated)
- **v1.x**: Initial release

## License

See LICENSE file for details.
