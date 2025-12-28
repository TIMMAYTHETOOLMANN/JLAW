# JLAW v2 to v3 Migration Guide

## Overview

JLAW v3.0 introduces a modular architecture with a new CLI entry point (`jlaw_cli.py`) that replaces the monolithic `JLAW_UNIFIED.py`. This guide will help you migrate your scripts and workflows.

## What Changed?

### Major Changes

1. **New Entry Point**: `JLAW_UNIFIED.py` → `jlaw_cli.py`
2. **Modular CLI**: Centralized argument parsing in `src/cli/`
3. **Rich Output**: Colorized console output with progress tracking
4. **ML Model Management**: Pre-download ML models to avoid cold-start delays
5. **Enhanced Validation**: Pre-flight checks with `--validate-only`
6. **Deprecation Framework**: Systematic deprecation of v1 modules

### What Still Works?

✅ All existing command-line flags and arguments  
✅ Backward compatibility shim for `JLAW_UNIFIED.py`  
✅ All orchestrators (UnifiedForensicOrchestrator, etc.)  
✅ All 15 analysis nodes  
✅ Evidence chain and DOJ-grade output  

## Quick Migration

### Command Line Usage

**Before (v2.x):**
```bash
python JLAW_UNIFIED.py --cik 320187 --year 2019
```

**After (v3.0):**
```bash
python jlaw_cli.py --cik 320187 --year 2019
```

### Scripts and Automation

**Before:**
```bash
#!/bin/bash
python JLAW_UNIFIED.py \
  --cik 0000320187 \
  --company "Apple Inc." \
  --year 2019 \
  --auto \
  --strict
```

**After:**
```bash
#!/bin/bash
python jlaw_cli.py \
  --cik 0000320187 \
  --company "Apple Inc." \
  --year 2019 \
  --auto \
  --strict
```

## Detailed Migration Steps

### Step 1: Update Dependencies

Ensure you have the latest requirements:

```bash
pip install -r requirements.txt
```

New dependencies in v3.0:
- `rich>=13.0.0` - CLI formatting
- `pytest-asyncio>=0.23.0` - Async testing

### Step 2: Download ML Models (One-Time)

v3.0 supports pre-downloading ML models to avoid cold-start delays:

```bash
python jlaw_cli.py --download-models
```

This downloads:
- `microsoft/deberta-v3-base` (~440 MB)
- `ProsusAI/finbert` (~440 MB)
- `distilbert-base-uncased` (~250 MB)

### Step 3: Update Scripts

Replace `JLAW_UNIFIED.py` with `jlaw_cli.py` in all scripts:

```bash
# Find all scripts using JLAW_UNIFIED.py
grep -r "JLAW_UNIFIED.py" .

# Use sed to replace (Linux/Mac)
find . -type f -name "*.sh" -exec sed -i 's/JLAW_UNIFIED\.py/jlaw_cli.py/g' {} +
find . -type f -name "*.py" -exec sed -i 's/JLAW_UNIFIED\.py/jlaw_cli.py/g' {} +
```

### Step 4: Test Migration

Run validation checks:

```bash
python jlaw_cli.py --validate-only
```

Run a dry-run to verify execution plan:

```bash
python jlaw_cli.py --cik 0000320187 --year 2019 --dry-run
```

### Step 5: Update CI/CD Pipelines

**GitHub Actions Example:**

**Before:**
```yaml
- name: Run JLAW Analysis
  run: |
    python JLAW_UNIFIED.py \
      --cik 0000320187 \
      --year 2019 \
      --auto
```

**After:**
```yaml
- name: Download ML Models (cached)
  uses: actions/cache@v3
  with:
    path: ~/.cache/jlaw/models
    key: jlaw-models-v1

- name: Ensure Models Downloaded
  run: python jlaw_cli.py --download-models

- name: Run JLAW Analysis
  run: |
    python jlaw_cli.py \
      --cik 0000320187 \
      --year 2019 \
      --auto
```

## New Features in v3.0

### 1. Pre-Flight Validation

Check configuration before running analysis:

```bash
python jlaw_cli.py --validate-only
```

Output:
```
✅ SEC User-Agent: Valid
✅ OPENAI_API_KEY: Configured
✅ ANTHROPIC_API_KEY: Configured
⚠️  POLYGON_API_KEY: Not configured (optional)
✅ All ML models cached
✅ All pre-flight checks passed!
```

### 2. Dry Run Mode

Preview execution plan without running:

```bash
python jlaw_cli.py --cik 0000320187 --year 2019 --dry-run
```

### 3. ML Model Management

```bash
# List models
python jlaw_cli.py --verify-models

# Download all models
python jlaw_cli.py --download-models

# Clear cache
python jlaw_cli.py --clear-model-cache
```

### 4. Export Configuration

```bash
python jlaw_cli.py --export-config config.json
```

### 5. Execution Modes

```bash
# Intelligent triage (resource-constrained)
python jlaw_cli.py --cik XXX --year 2019 --mode auto

# Standard analysis (default)
python jlaw_cli.py --cik XXX --year 2019 --mode standard

# DOJ-grade forensic
python jlaw_cli.py --cik XXX --year 2019 --mode forensic --strict

# Batch processing
python jlaw_cli.py --batch targets.json --mode batch

# Continuous monitoring
python jlaw_cli.py --daemon --watchlist companies.txt --mode daemon
```

## Flag Compatibility

All v2.x flags are supported in v3.0:

| v2.x Flag | v3.0 Flag | Status | Notes |
|-----------|-----------|--------|-------|
| `--cik` | `--cik` | ✅ Same | - |
| `--company` | `--company` | ✅ Same | - |
| `--year` | `--year` | ✅ Same | - |
| `--start` | `--start-date` | ⚠️ Updated | Now `--start-date` |
| `--end` | `--end-date` | ⚠️ Updated | Now `--end-date` |
| `--auto` | `--auto` | ✅ Same | - |
| `--strict` | `--strict` | ✅ Same | - |
| `--output` | `--output-dir` | ⚠️ Updated | Now `--output-dir` |
| `--no-pdf` | `--no-pdf` | ✅ Same | - |
| `--check-deps` | `--check-deps` | ✅ Same | - |
| `--investigation` | `--investigation` | ✅ Same | - |
| `--strategy` | `--strategy` | ✅ Same | - |
| `--batch` | `--batch` | ✅ Same | - |
| `--daemon` | `--daemon` | ✅ Same | - |
| `--watchlist` | `--watchlist` | ✅ Same | - |

### New Flags in v3.0

| Flag | Description |
|------|-------------|
| `--mode MODE` | Execution mode (auto, standard, forensic, batch, daemon) |
| `--validate-only` | Run pre-flight checks only |
| `--dry-run` | Show execution plan without running |
| `--profile` | Enable performance profiling |
| `--export-config PATH` | Export configuration to file |
| `--download-models` | Download ML models |
| `--verify-models` | Verify cached models |
| `--clear-model-cache` | Clear model cache |
| `--verbose` | Enable verbose output |
| `--debug` | Enable debug logging |
| `--version` | Print version |

## Python API Changes

### Importing

**Before:**
```python
# Direct import from JLAW_UNIFIED
from JLAW_UNIFIED import UnifiedForensicEngine, TargetConfig
```

**After:**
```python
# Import from modular structure
from src.core.unified_orchestrator import UnifiedForensicOrchestrator
from src.cli.argument_parser import JLAWArgumentParser
```

### Orchestrator Usage

**Before:**
```python
config = TargetConfig(
    cik="320187",
    company_name="NIKE, Inc.",
    start_date=date(2019, 1, 1),
    end_date=date(2019, 12, 31),
    auto_mode=True,
    strict_mode=True
)

engine = UnifiedForensicEngine(config)
dossier = await engine.execute()
```

**After:**
```python
orchestrator = UnifiedForensicOrchestrator(
    cik="320187",
    company_name="NIKE, Inc.",
    start_date=date(2019, 1, 1),
    end_date=date(2019, 12, 31),
    output_dir=Path("output"),
    strict_mode=True,
    auto_mode=True
)

result = await orchestrator.execute_full_analysis()
```

## Deprecation Timeline

| Version | Status | Action |
|---------|--------|--------|
| v3.0 | Current | `JLAW_UNIFIED.py` deprecated with shim |
| v3.1 | Future | Deprecation warnings become errors |
| v4.0 | Future | `JLAW_UNIFIED.py` removed entirely |

**Timeline**: 6 months for migration (until approximately June 2025)

## Common Migration Issues

### Issue 1: Import Errors

**Error:**
```
ImportError: cannot import name 'UnifiedForensicEngine' from 'src.core'
```

**Solution:**
```python
# Old (v2)
from src.core import UnifiedForensicEngine

# New (v3)
from src.core.unified_orchestrator import UnifiedForensicOrchestrator
```

### Issue 2: Deprecation Warnings

**Warning:**
```
DeprecationWarning: JLAW_UNIFIED.py is deprecated and will be removed in v3.0.
Please use jlaw_cli.py instead.
```

**Solution:**
Replace `JLAW_UNIFIED.py` with `jlaw_cli.py` in your scripts.

### Issue 3: ML Model Cold Start

**Issue:** First run takes 2-5 minutes downloading models

**Solution:** Pre-download models once:
```bash
python jlaw_cli.py --download-models
```

### Issue 4: Configuration Not Found

**Error:**
```
Configuration error: SEC_USER_AGENT not configured
```

**Solution:** Set in `.env` file:
```bash
SEC_USER_AGENT="YourCompany contact@example.com"
```

## Testing Your Migration

### Test Suite

Run the test suite to ensure compatibility:

```bash
# Run all tests
pytest tests/ -v

# Run CLI tests specifically
pytest tests/unit/test_cli_argument_parser.py -v

# Run deprecation tests
pytest tests/unit/test_deprecation_framework.py -v
```

### Smoke Tests

```bash
# 1. Validate environment
python jlaw_cli.py --validate-only

# 2. Check version
python jlaw_cli.py --version

# 3. Dry run
python jlaw_cli.py --cik 0000320187 --year 2019 --dry-run

# 4. Quick analysis (demo mode)
python jlaw_cli.py --demo
```

## Getting Help

If you encounter issues during migration:

1. **Check Documentation**: `docs/CLI_REFERENCE.md`
2. **Run Validation**: `python jlaw_cli.py --validate-only`
3. **Enable Debug**: `python jlaw_cli.py --debug --verbose`
4. **GitHub Issues**: https://github.com/TIMMAYTHETOOLMANN/JLAW/issues

## Rollback Plan

If you need to temporarily rollback to v2.x:

```bash
# Use deprecated version explicitly
python JLAW_UNIFIED_DEPRECATED.py --cik XXX --year 2019

# Or checkout v2.x branch
git checkout v2.x
```

**Note:** The shim in `JLAW_UNIFIED.py` will continue to work, but is not recommended for production.

## Migration Checklist

- [ ] Update dependencies (`pip install -r requirements.txt`)
- [ ] Download ML models (`python jlaw_cli.py --download-models`)
- [ ] Update all scripts (`JLAW_UNIFIED.py` → `jlaw_cli.py`)
- [ ] Update CI/CD pipelines
- [ ] Test with `--validate-only`
- [ ] Test with `--dry-run`
- [ ] Run full smoke tests
- [ ] Update documentation/wikis
- [ ] Train team on new CLI
- [ ] Monitor first production runs

## Conclusion

The v3.0 migration is straightforward - primarily a search-and-replace of the entry point. The new modular architecture provides better maintainability, enhanced features, and improved performance.

For questions or issues, please open a GitHub issue or consult the documentation.

**Happy analyzing! 🚀**
