# JLAW FORENSICS - QUICK REFERENCE GUIDE
**Production System v9.0.0**

---

## 🚀 QUICK START

### Run Analysis (Recommended Method)
```bash
python jlaw_forensics.py --config config/nike_2019.yaml
```

### Check System Status
```bash
python jlaw_forensics.py --status
```

---

## 📝 CREATING A NEW ANALYSIS

### Step 1: Create Config File

Copy the template:
```bash
cp config/analysis_template.yaml config/mycompany_2023.yaml
```

Edit the config:
```yaml
company_name: "My Company Inc."
cik: "0001234567"  # 10-digit zero-padded
ticker: "MYCO"
start_date: "2023-01-01"
end_date: "2023-12-31"
fiscal_year: 2023

filing_types:
  - "10-K"
  - "10-Q"
  - "8-K"
  - "4"

output_directory: "forensic_reports/mycompany_2023"
```

### Step 2: Run Analysis
```bash
python jlaw_forensics.py --config config/mycompany_2023.yaml
```

---

## 💻 COMMAND LINE OPTIONS

### Basic Analysis
```bash
python jlaw_forensics.py \
  --company "Tesla Inc." \
  --cik 1318605 \
  --year 2022
```

### Advanced Analysis
```bash
python jlaw_forensics.py \
  --company "Apple Inc." \
  --cik 320193 \
  --ticker "AAPL" \
  --start-date "2023-01-01" \
  --end-date "2023-12-31" \
  --filing-types "10-K,10-Q,8-K,4" \
  --output-dir "forensic_reports/apple_2023" \
  --output-format "doj_level"
```

### Validate Only (No Analysis)
```bash
python jlaw_forensics.py \
  --company "Microsoft Corp." \
  --cik 789019 \
  --year 2023 \
  --validate-only
```

---

## 🔒 SYSTEM LOCK COMMANDS

### Lock System for Production
```bash
python jlaw_forensics.py --lock-system
```

### Check Lock Status
```bash
python jlaw_forensics.py --status
```

### Unlock System (Development Only)
```bash
python jlaw_forensics.py --unlock-system
```

---

## 📊 AVAILABLE CONFIG FILES

### Nike Inc. 2019
```bash
python jlaw_forensics.py --config config/nike_2019.yaml
```

### Apple Inc. 2023
```bash
python jlaw_forensics.py --config config/apple_2023.yaml
```

### Blank Template
```bash
cp config/analysis_template.yaml config/newcompany.yaml
```

---

## 📁 OUTPUT LOCATIONS

### Default Directory
```
forensic_reports/<company>_<year>/
├── forensic_report_<timestamp>.txt    # Main DOJ-level report
└── analysis_summary_<timestamp>.json  # Structured data
```

### Custom Directory
```bash
python jlaw_forensics.py \
  --config config/myconfig.yaml \
  --output-dir "custom/path"
```

---

## 🔍 FINDING CIK NUMBERS

### SEC EDGAR CIK Lookup
1. Go to: https://www.sec.gov/cgi-bin/browse-edgar
2. Search for company name
3. CIK is shown in search results
4. Example: Nike Inc. → CIK: 0000320187

### Auto-Normalization
- Input: `320187` → Normalized: `0000320187`
- System auto-pads to 10 digits

---

## 📋 SUPPORTED FILING TYPES

### Common Types
- `10-K` - Annual Report
- `10-Q` - Quarterly Report
- `8-K` - Current Report
- `4` - Insider Trading (Form 4)
- `SC 13G` - Beneficial Ownership
- `DEF 14A` - Proxy Statement

### Full List
System supports 60+ SEC form types. See config templates for complete list.

---

## ✅ INPUT VALIDATION

### CIK Format
- **Valid:** `320187`, `0000320187`, `1318605`
- **Invalid:** `abc123`, `32018`, `00320187000`

### Date Format
- **Valid:** `2023-01-01`, `2023-12-31`
- **Invalid:** `01/01/2023`, `2023-1-1`, `23-01-01`

### Filing Types
- **Valid:** `10-K`, `10-Q`, `8-K`, `4`
- **Auto-Correct:** `10K` → `10-K`, `4/A` → `4`

---

## 🎯 TYPICAL WORKFLOW

### 1. Create Config
```bash
cp config/analysis_template.yaml config/tesla_2022.yaml
# Edit tesla_2022.yaml with company details
```

### 2. Validate Inputs
```bash
python jlaw_forensics.py --config config/tesla_2022.yaml --validate-only
```

### 3. Run Analysis
```bash
python jlaw_forensics.py --config config/tesla_2022.yaml
```

### 4. Review Results
```bash
cat forensic_reports/tesla_2022/forensic_report_*.txt
```

---

## 🐛 TROUBLESHOOTING

### "System must be locked to run"
**Solution:**
```bash
python jlaw_forensics.py --lock-system
```

### "Invalid CIK format"
**Solution:** Use 10-digit zero-padded format: `0001234567`

### "Start date must be before end date"
**Solution:** Check date order in config file

### "Unknown filing type"
**Solution:** Use standard SEC form names: `10-K`, `10-Q`, `8-K`, `4`

---

## 📞 SYSTEM STATUS CHECK

### Full Status Report
```bash
python jlaw_forensics.py --status
```

**Expected Output:**
```
JLAW FORENSICS SYSTEM STATUS
================================================================================
State: LOCKED
Lock File: forensic_storage/system.lock.json
Lock File Exists: True
Signature: 0c99250f6dd41db9...

Locked Configuration:
  system_version: 1.0.0
  enhancement_protocol_version: 9.0
  late_filing_tolerance_days: 2
  zero_dollar_threshold: 0.01
  default_output_format: doj_level
  evidence_chain_required: True
================================================================================
```

---

## 🚦 PRODUCTION BEST PRACTICES

### ✅ DO
- Use configuration files for repeatability
- Keep system locked in production
- Version control all config files
- Review validation warnings
- Archive analysis outputs

### ❌ DON'T
- Modify locked system parameters
- Use hardcoded values in scripts
- Skip input validation
- Ignore system warnings
- Delete output files

---

## 📚 DOCUMENTATION

### Key Documents
- `PRODUCTION_STATUS_VERIFICATION.md` - Current system status
- `NIKE_2019_ENHANCED_ANALYSIS_COMPARISON.md` - Baseline comparison
- `ENHANCEMENT_PROTOCOL_README.md` - Full system documentation
- `ENHANCEMENT_PROTOCOL_COMPLETE_VALIDATION.md` - Phase validation

### Config Templates
- `config/analysis_template.yaml` - Blank template
- `config/nike_2019.yaml` - Nike example
- `config/apple_2023.yaml` - Apple example

---

## 🎓 EXAMPLES

### Example 1: Nike 2019
```bash
python jlaw_forensics.py --config config/nike_2019.yaml
```

### Example 2: Apple CLI
```bash
python jlaw_forensics.py \
  --company "Apple Inc." \
  --cik 320193 \
  --year 2023 \
  --filing-types "10-K,10-Q,4"
```

### Example 3: Custom Date Range
```bash
python jlaw_forensics.py \
  --company "Microsoft Corp." \
  --cik 789019 \
  --start-date "2023-01-01" \
  --end-date "2023-06-30" \
  --filing-types "10-Q,8-K"
```

---

## 🔧 MAINTENANCE

### Update System Lock
```bash
# Unlock
python jlaw_forensics.py --unlock-system

# Make changes (if needed)
# ...

# Re-lock
python jlaw_forensics.py --lock-system
```

### Verify Configuration
```bash
python jlaw_forensics.py --config config/myconfig.yaml --validate-only
```

### Check Logs
```bash
ls -la jlaw_forensics_*.log
tail -f jlaw_forensics_*.log
```

---

## ⚡ QUICK COMMANDS

### Most Common Commands
```bash
# Run Nike 2019 analysis
python jlaw_forensics.py --config config/nike_2019.yaml

# Run Apple 2023 analysis
python jlaw_forensics.py --config config/apple_2023.yaml

# Check system status
python jlaw_forensics.py --status

# Lock system
python jlaw_forensics.py --lock-system

# Validate config only
python jlaw_forensics.py --config config/test.yaml --validate-only
```

---

**System Version:** 9.0.0  
**Status:** Production-Locked  
**Last Updated:** November 29, 2025

