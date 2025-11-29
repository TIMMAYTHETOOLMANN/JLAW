# 🚀 JLAW FORENSICS - UNIVERSAL ANALYSIS ENGINE

## Production-Ready Parameterized Forensic Analysis System

**No more manual scripts!** Configure once, run anywhere.

---

## 📊 SYSTEM OVERVIEW

The JLAW Forensics Universal Analysis Engine is a production-ready system that allows you to:

✅ **Analyze any company** - Just provide CIK or company name  
✅ **Any date range** - Specify start/end dates or fiscal year  
✅ **Any filing types** - Select which SEC filings to analyze  
✅ **Multiple output formats** - DOJ-level reports, JSON, or both  
✅ **Consistent format** - Uses the proven PDF benchmark format  
✅ **No new scripts** - Same system, different parameters  

---

## 🎯 QUICK START

### Method 1: Command-Line Execution (Fastest)

```bash
# Analyze a company by year
python jlaw_forensics.py --company "Nike Inc." --cik 0000320187 --year 2019

# Analyze with specific date range
python jlaw_forensics.py --company "Apple Inc." --cik 0000320193 --start-date 2020-01-01 --end-date 2020-12-31

# Generate both report formats
python jlaw_forensics.py --company "Tesla Inc." --cik 0001318605 --year 2021 --output-format all

# Custom output directory
python jlaw_forensics.py --company "Microsoft" --cik 0000789019 --year 2022 --output-dir reports/microsoft
```

### Method 2: Configuration File (Most Flexible)

**Step 1:** Create configuration file `my_analysis.yaml`:

```yaml
company_name: "Nike Inc."
cik: "0000320187"
ticker: "NKE"
start_date: "2019-01-01"
end_date: "2019-12-31"
fiscal_year: 2019

filing_types:
  - "10-K"
  - "10-Q"
  - "8-K"
  - "4"
  - "SC 13G"
  - "SC 13G/A"

output_format: "all"  # doj_level, json, or all
output_directory: "forensic_reports"
generate_evidence_packages: true

enable_benfords: true
enable_contradiction: true
enable_temporal: true
enable_legal_correlation: true
```

**Step 2:** Run analysis:

```bash
python jlaw_forensics.py --config my_analysis.yaml
```

### Method 3: Interactive Mode (User-Friendly)

```bash
python jlaw_forensics.py --interactive
```

Then follow the prompts:
```
Company Name: Nike Inc.
CIK Number: 0000320187
Ticker Symbol (optional): NKE
Start Date (YYYY-MM-DD): 2019-01-01
End Date (YYYY-MM-DD): 2019-12-31
Filing Types: 10-K, 10-Q, 4
Output Format (1-3): 1
```

---

## 📋 COMPLETE PARAMETER REFERENCE

### Command-Line Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `--company` | Company name | `"Nike Inc."` |
| `--cik` | CIK number | `0000320187` |
| `--ticker` | Stock ticker | `NKE` |
| `--year` | Fiscal year | `2019` |
| `--start-date` | Start date | `2019-01-01` |
| `--end-date` | End date | `2019-12-31` |
| `--config` | Config file path | `config.yaml` |
| `--interactive` | Interactive mode | (flag) |
| `--output-format` | Report format | `doj_level`, `json`, `all` |
| `--output-dir` | Output directory | `reports/nike` |
| `--create-sample-config` | Create sample config | (flag) |

### Configuration File Options

#### Company Information
```yaml
company_name: "Company Name"    # Required
cik: "0000000000"              # Required
ticker: "TICK"                 # Optional
```

#### Date Range
```yaml
start_date: "2019-01-01"       # YYYY-MM-DD format
end_date: "2019-12-31"         # YYYY-MM-DD format
fiscal_year: 2019              # Optional shortcut
```

#### Filing Selection
```yaml
filing_types:                  # Which SEC filings to analyze
  - "10-K"                    # Annual reports
  - "10-Q"                    # Quarterly reports
  - "8-K"                     # Current reports
  - "4"                       # Insider trading reports
  - "SC 13G"                  # Beneficial ownership
  - "SC 13G/A"                # Amended ownership

max_filings: 100               # Limit number of filings (null = all)
```

#### Analysis Features
```yaml
enable_benfords: true          # Benford's Law analysis
enable_contradiction: true     # Contradiction detection
enable_temporal: true          # Timeline analysis
enable_legal_correlation: true # Legal statute mapping
```

#### Output Configuration
```yaml
output_format: "doj_level"     # doj_level, json, or all
output_directory: "forensic_reports"
generate_evidence_packages: true
save_intermediate_results: true
generate_summary_only: false
```

#### Detection Thresholds
```yaml
late_filing_tolerance_days: 2  # SEC requirement
zero_dollar_threshold: 0.01    # Consider <$0.01 as zero
misstatement_keywords:
  - "restated"
  - "restate"
  - "restating"
  - "modified retrospective"
```

#### Advanced Options
```yaml
parallel_processing: true
max_workers: 5
```

---

## 📦 GENERATED OUTPUT

### Directory Structure

After running analysis, you'll get:

```
forensic_reports/
├── forensic_report_20251129_021218.txt    # DOJ-level report (80KB+)
├── forensic_report_20251129_021218.json   # JSON format
└── analysis_summary_20251129_021218.json  # Quick summary
```

### Output Files Explained

#### 1. DOJ-Level Report (`.txt`)
- **Format:** Matches PDF benchmark exactly
- **Content:** Complete forensic analysis
- **Sections:**
  - Report header with case info
  - Executive summary
  - Per-filing detailed analysis
  - All violations with evidence
  - Exact quotes from documents
  - Damage calculations
  - Prosecutorial assessments

#### 2. JSON Report (`.json`)
- **Format:** Machine-readable JSON
- **Content:** All violations with metadata
- **Use cases:**
  - API integration
  - Database import
  - Custom processing
  - Data analysis

#### 3. Analysis Summary (`.json`)
- **Format:** Lightweight JSON
- **Content:** High-level metrics
- **Includes:**
  - Case ID
  - Company info
  - Filing counts
  - Violation counts by type
  - Total damages
  - Timestamp

---

## 🎯 COMMON USE CASES

### Use Case 1: Quick Company Analysis

```bash
# Analyze any company for a specific year
python jlaw_forensics.py --company "Amazon.com Inc." --cik 0001018724 --year 2020
```

**Result:** Complete forensic report in `forensic_reports/` directory

### Use Case 2: Multi-Year Analysis

Create `multi_year.yaml`:
```yaml
company_name: "Tesla Inc."
cik: "0001318605"
start_date: "2018-01-01"
end_date: "2022-12-31"
output_format: "all"
```

Run:
```bash
python jlaw_forensics.py --config multi_year.yaml
```

### Use Case 3: Specific Filing Types Only

```yaml
company_name: "Apple Inc."
cik: "0000320193"
year: 2021
filing_types:
  - "10-K"
  - "10-Q"
# Only analyze annual and quarterly reports
```

### Use Case 4: Batch Processing

Create config files for multiple companies:

```bash
# Create configs
cat > nike_2019.yaml << EOF
company_name: "Nike Inc."
cik: "0000320187"
year: 2019
EOF

cat > apple_2020.yaml << EOF
company_name: "Apple Inc."
cik: "0000320193"
year: 2020
EOF

# Run batch
python jlaw_forensics.py --config nike_2019.yaml
python jlaw_forensics.py --config apple_2020.yaml
```

### Use Case 5: JSON Output for Integration

```bash
# Generate JSON for API/database
python jlaw_forensics.py --company "Microsoft" --cik 0000789019 --year 2021 --output-format json

# Process JSON output
python process_violations.py forensic_reports/forensic_report_*.json
```

---

## 🔧 CONFIGURATION TEMPLATES

### Template 1: Standard Analysis

```yaml
# standard_analysis.yaml
company_name: "COMPANY NAME HERE"
cik: "CIK NUMBER HERE"
ticker: "TICKER HERE"
year: 2019

filing_types:
  - "10-K"
  - "10-Q"
  - "8-K"
  - "4"

output_format: "doj_level"
output_directory: "forensic_reports"
```

### Template 2: Comprehensive Analysis

```yaml
# comprehensive_analysis.yaml
company_name: "COMPANY NAME HERE"
cik: "CIK NUMBER HERE"
start_date: "2019-01-01"
end_date: "2019-12-31"

filing_types:
  - "10-K"
  - "10-Q"
  - "8-K"
  - "4"
  - "SC 13G"
  - "SC 13G/A"
  - "DEF 14A"

output_format: "all"
generate_evidence_packages: true

enable_benfords: true
enable_contradiction: true
enable_temporal: true
enable_legal_correlation: true
```

### Template 3: Minimal Analysis (Fast)

```yaml
# minimal_analysis.yaml
company_name: "COMPANY NAME HERE"
cik: "CIK NUMBER HERE"
year: 2019

filing_types:
  - "10-K"
  - "10-Q"

output_format: "json"
generate_summary_only: true
max_filings: 20
```

---

## 📊 REAL EXAMPLES

### Example 1: Nike Inc. 2019 (Benchmark)

```bash
python jlaw_forensics.py --company "Nike Inc." --cik 0000320187 --year 2019 --output-format all
```

**Output:**
```
================================================================================
FORENSIC ANALYSIS: Nike Inc.
================================================================================
CIK: 0000320187
Period: 2019-01-01 to 2019-12-31
Filing Types: 10-K, 10-Q, 8-K, 4, SC 13G, SC 13G/A

[PHASE 1] Creating Forensic Case...
✓ Case created: CASE_NikeInc_20251129_081218

[PHASE 2] Collecting SEC Filings...
✓ Collected 100 filings

[PHASE 3] Detecting Violations...
✓ Detected 24 total violations

[PHASE 4] Calculating Damages...
✓ Total estimated damages: $105,425,000.00

[PHASE 5] Generating Forensic Reports...
✓ Generated 2 report(s)

[PHASE 6] Saving Results...
✓ Results saved to forensic_reports

================================================================================
✅ FORENSIC ANALYSIS COMPLETE
================================================================================

ANALYSIS COMPLETE
================================================================================
Company: Nike Inc.
Filings Analyzed: 100
Total Violations: 24
Total Damages: $105,425,000.00
Reports saved to: forensic_reports
================================================================================
```

### Example 2: Apple Inc. 2020

```yaml
# apple_2020.yaml
company_name: "Apple Inc."
cik: "0000320193"
ticker: "AAPL"
year: 2020
output_format: "all"
```

```bash
python jlaw_forensics.py --config apple_2020.yaml
```

### Example 3: Tesla Inc. Q1 2021

```yaml
# tesla_q1_2021.yaml
company_name: "Tesla Inc."
cik: "0001318605"
ticker: "TSLA"
start_date: "2021-01-01"
end_date: "2021-03-31"
filing_types:
  - "10-Q"
  - "8-K"
output_format: "json"
```

---

## 🎓 BEST PRACTICES

### 1. Start with Sample Config

```bash
# Generate sample configuration
python jlaw_forensics.py --create-sample-config

# Edit sample_analysis_config.yaml with your parameters
# Then run
python jlaw_forensics.py --config sample_analysis_config.yaml
```

### 2. Use Meaningful Output Directories

```bash
# Organize by company and year
python jlaw_forensics.py --company "Nike" --cik 0000320187 --year 2019 --output-dir reports/nike/2019
python jlaw_forensics.py --company "Nike" --cik 0000320187 --year 2020 --output-dir reports/nike/2020
```

### 3. Version Control Your Configs

```bash
git init forensic_configs
cd forensic_configs
cp ../nike_2019.yaml .
git add nike_2019.yaml
git commit -m "Add Nike 2019 analysis config"
```

### 4. Automate Batch Processing

```bash
# batch_analysis.sh
#!/bin/bash
for config in configs/*.yaml; do
    echo "Processing $config..."
    python jlaw_forensics.py --config "$config"
done
```

### 5. Monitor Long-Running Analyses

```bash
# Run with logging
python jlaw_forensics.py --config large_analysis.yaml > analysis.log 2>&1 &

# Monitor progress
tail -f jlaw_forensics_*.log
```

---

## 🚀 ADVANCED FEATURES

### Custom Filing Type Selection

```yaml
# Only analyze specific filings
filing_types:
  - "10-K"  # Annual reports only
  
# Or multiple types
filing_types:
  - "10-K"
  - "10-Q"
  - "8-K"
```

### Date Range Flexibility

```yaml
# Full year
year: 2019

# Specific quarter
start_date: "2019-01-01"
end_date: "2019-03-31"

# Multi-year
start_date: "2018-01-01"
end_date: "2020-12-31"
```

### Output Format Options

```yaml
# DOJ-level report only (default)
output_format: "doj_level"

# JSON only (for integration)
output_format: "json"

# Both formats
output_format: "all"
```

### Performance Tuning

```yaml
# Limit filings for faster analysis
max_filings: 50

# Parallel processing
parallel_processing: true
max_workers: 10

# Quick summary only
generate_summary_only: true
```

---

## 📁 FILE MANAGEMENT

### Organizing Reports

```bash
# By company
forensic_reports/
├── nike/
│   ├── 2019/
│   ├── 2020/
│   └── 2021/
├── apple/
│   └── 2020/
└── tesla/
    └── 2021/
```

### Cleanup Old Reports

```bash
# Remove reports older than 30 days
find forensic_reports/ -name "*.txt" -mtime +30 -delete
find forensic_reports/ -name "*.json" -mtime +30 -delete
```

### Archiving Results

```bash
# Create archive
tar -czf nike_2019_analysis.tar.gz forensic_reports/nike/2019/

# Extract later
tar -xzf nike_2019_analysis.tar.gz
```

---

## 🎯 SYSTEM ADVANTAGES

### ✅ NO MORE Manual Scripts

**Before:**
- Create new Python script for each analysis
- Hardcode company names, dates, parameters
- Duplicate code everywhere
- Messy project structure

**After:**
- One universal script
- Configure with parameters or config files
- Consistent output format
- Clean, organized reports

### ✅ Proven Format Locked In

The DOJ-level report format is **hard-coded** into the system:
- Matches PDF benchmark exactly
- All required fields present
- Consistent structure
- No manual tampering needed

### ✅ Easy to Scale

```bash
# Analyze 10 companies
for company in nike apple tesla microsoft amazon google meta netflix uber lyft; do
    python jlaw_forensics.py --company "$company" --cik $(get_cik $company) --year 2021
done
```

### ✅ Integration Ready

```python
# Use in your own scripts
from jlaw_forensics import UniversalForensicEngine, ForensicAnalysisConfig

config = ForensicAnalysisConfig()
config.company_name = "Nike Inc."
config.cik = "0000320187"
config.year = 2019

engine = UniversalForensicEngine(config)
results = await engine.execute_analysis()
```

---

## 🎊 SUMMARY

### What You Get

✅ **Universal analysis engine** - works with any company  
✅ **Parameterized execution** - no new scripts needed  
✅ **Proven output format** - matches PDF benchmark  
✅ **Multiple input methods** - CLI, config files, interactive  
✅ **Multiple output formats** - DOJ-level, JSON, or both  
✅ **Production ready** - logging, error handling, validation  

### How to Use

**Quick analysis:**
```bash
python jlaw_forensics.py --company "Nike Inc." --cik 0000320187 --year 2019
```

**With configuration:**
```bash
python jlaw_forensics.py --config my_analysis.yaml
```

**Interactive:**
```bash
python jlaw_forensics.py --interactive
```

### Next Steps

1. **Try it now:**
   ```bash
   python jlaw_forensics.py --create-sample-config
   python jlaw_forensics.py --config sample_analysis_config.yaml
   ```

2. **Create your own configs** for different companies

3. **Automate batch processing** for multiple analyses

4. **Integrate** into your workflow

---

**The system is ready. No more manual scripts. Just configure and run.** 🚀

