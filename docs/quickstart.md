# Quick Start Guide

Get up and running with JLAW in 5 minutes.

---

## Prerequisites

Before you begin, ensure you have:

- **Python 3.10+** installed
- **Git** for repository cloning
- **SEC EDGAR API access** (requires User-Agent configuration)
- **OpenAI API key** (for primary AI validation)
- **Anthropic API key** (for secondary AI validation)

Optional services (enhances analysis but not required):
- Neo4j database (Node 11 - Executive Network Analysis)
- Redis (rate limiting and caching)
- TimescaleDB (time-series metrics)
- Polygon.io API key (Node 15 - Market Correlation)

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/TIMMAYTHETOOLMANN/JLAW.git
cd JLAW
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

Or with optional dependencies:

```bash
pip install -e ".[dev,viz,docs]"
```

---

## Configuration

### 1. Create Environment File

Copy the example environment file:

```bash
cp .env.example .env
```

### 2. Configure SEC EDGAR Access

Edit `.env` and set your SEC User-Agent:

```bash
# REQUIRED: SEC requires a User-Agent with your organization and email
SEC_USER_AGENT=YourCompany/1.0 (your-email@company.com)
```

!!! warning "SEC User-Agent Required"
    The SEC requires a valid User-Agent header with your organization name and contact email. Requests without this will fail with HTTP 429 errors.
    
    See [SEC API Setup Guide](../SEC_API_SETUP.md) for details.

### 3. Configure API Keys

Add your AI provider API keys to `.env`:

```bash
# REQUIRED: OpenAI API key for primary AI validation
OPENAI_API_KEY=sk-proj-YOUR_OPENAI_API_KEY_HERE

# REQUIRED: Anthropic API key for secondary AI validation
ANTHROPIC_API_KEY=sk-ant-api03-YOUR_ANTHROPIC_KEY_HERE

# OPTIONAL: Polygon.io for market correlation (Node 15)
POLYGON_API_KEY=YOUR_POLYGON_API_KEY_HERE
```

### 4. Verify Configuration

Run the validation check:

```bash
python jlaw_cli.py --validate-only
```

Expected output:

```
✓ Loaded 15 environment variables
✓ SEC User-Agent: Valid
✓ OPENAI_API_KEY: Configured
✓ ANTHROPIC_API_KEY: Configured
⚠ POLYGON_API_KEY: Not configured (optional)
✓ All pre-flight checks passed!
```

---

## First Analysis

### Run a Simple Analysis

Analyze Nike's 2019 SEC filings:

```bash
python jlaw_cli.py --cik 320187 --company "NIKE, Inc." --year 2019
```

The system will:

1. **Validate configuration** (Phase 1)
2. **Download SEC filings** (Phase 2) - Form 4, 10-K, 10-Q, DEF 14A, 8-K, etc.
3. **Parse documents** (Phase 3)
4. **Execute 15-node analysis** (Phase 4)
5. **Run 23 detection patterns** (Phase 5)
6. **Cross-validate with AI** (Phase 6)
7. **Generate forensic dossier** (Phase 9)

### View Results

Results are saved to `output/NIKE_Inc_320187_2019/`:

```
output/NIKE_Inc_320187_2019/
├── dossier_NIKE_Inc_320187_2019.json    # Complete forensic report
├── evidence_chain/                       # Evidence integrity proof
│   ├── custody_log.json
│   ├── merkle_tree.json
│   └── timestamps/
├── node_reports/                         # Individual node outputs
│   ├── node1_form4.json
│   ├── node2_def14a.json
│   └── ...
└── summary_report.txt                    # Human-readable summary
```

---

## Common Use Cases

### Dry Run (Show Execution Plan)

Preview what will be executed without running analysis:

```bash
python jlaw_cli.py --cik 320187 --year 2019 --dry-run
```

### Automatic Execution

Run without interactive confirmations:

```bash
python jlaw_cli.py --cik 320187 --year 2019 --auto
```

### Strict Forensic Mode

Run with DOJ-grade forensic protocols:

```bash
python jlaw_cli.py --cik 320187 --year 2019 --strict --auto
```

!!! info "Strict Mode"
    Strict mode enforces mandatory phase gates, cascade abort on failures, and generates detailed failure reports. See [Strict Execution Mode](../STRICT_EXECUTION_MODE.md) for details.

### Investigation Type Optimization

Optimize for specific investigation types:

```bash
# Insider trading investigation
python jlaw_cli.py --cik 320187 --year 2019 --investigation insider-trading --auto

# Accounting fraud investigation
python jlaw_cli.py --cik 320187 --year 2019 --investigation accounting-fraud --auto

# Executive compensation investigation
python jlaw_cli.py --cik 320187 --year 2019 --investigation executive-compensation --auto
```

---

## Verifying Results

### Check Execution Status

Look for the exit code in the output:

- **Exit Code 0**: Complete success
- **Exit Code 1**: Configuration failure
- **Exit Code 2**: Data collection failure
- **Exit Code 3**: Document parsing failure
- **Exit Code 4**: Node execution below threshold
- **Exit Code 5**: Pattern detection failure
- **Exit Code 6**: Evidence chain integrity failure
- **Exit Code 7**: Dossier generation failure

### Verify Evidence Chain

Check evidence chain integrity:

```bash
python -c "
from src.core.evidence_chain.merkle_tree import MerkleTree
import json

# Load merkle tree
with open('output/NIKE_Inc_320187_2019/evidence_chain/merkle_tree.json') as f:
    tree_data = json.load(f)
    
print(f'Merkle Root: {tree_data[\"root\"]}')
print(f'Leaf Count: {tree_data[\"leaf_count\"]}')
"
```

### View Dossier Summary

```bash
cat output/NIKE_Inc_320187_2019/summary_report.txt
```

---

## Next Steps

- **[CLI Reference](user_guide/cli_reference.md)**: Complete CLI documentation
- **[Batch Processing](user_guide/batch_processing.md)**: Analyze multiple companies
- **[Interpreting Results](user_guide/interpreting_results.md)**: Understanding dossier output
- **[Deployment Guide](deployment/prerequisites.md)**: Production deployment
- **[Architecture Overview](architecture/system_overview.md)**: System design details

---

## Troubleshooting

### Common Issues

**Issue: "SEC User-Agent not configured"**

Solution: Set `SEC_USER_AGENT` in `.env` file with your organization and email.

**Issue: "OpenAI API key required"**

Solution: Set `OPENAI_API_KEY` in `.env` file. Get your key from [OpenAI Platform](https://platform.openai.com/api-keys).

**Issue: "Rate limit exceeded (429)"**

Solution: JLAW automatically handles rate limiting with exponential backoff. If this persists, check your `SEC_USER_AGENT` is valid.

**Issue: "No filings found for date range"**

Solution: Verify the company's CIK is correct and expand the date range. Some companies may not have filed in the specified period.

For more troubleshooting, see [Troubleshooting Guide](deployment/troubleshooting.md) and [Strict Mode Troubleshooting](../STRICT_MODE_TROUBLESHOOTING.md).

---

## Getting Help

- **Documentation**: [Full documentation site](index.md)
- **GitHub Issues**: [Report bugs or request features](https://github.com/TIMMAYTHETOOLMANN/JLAW/issues)
- **Configuration Guide**: [Deployment Configuration](deployment/configuration.md)
