"""
JARVISed out. OK say it with me. LAW Black Site Protocol - Recursive Calibration System
Continuously analyze control group until clinical repeatability is achieved
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

sys.path.insert(0, str(Path(__file__).parent))

from tools.document_parser import DocumentParser
from tools.sec_crawler import fetch_sec_filings_by_cik
from data_quality_validator import validate_complete_filing, generate_error_report

print("""
================================================================================
   JARVIS:LAW BLACK SITE PROTOCOL
   Recursive Calibration System - Control Group Analysis
================================================================================
""")

# Configuration
CIK_NIKE = "0000320187"
CONTROL_GROUP_YEAR = 2019
CONTROL_GROUP_SIZE = 10
ANALYSIS_OUTPUT_DIR = Path("./memory/calibration_runs")
ANALYSIS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print(f"[TARGET] Control Group: Nike Inc - First {CONTROL_GROUP_SIZE} Form 4 filings from {CONTROL_GROUP_YEAR}")
print(f"[MODE] Analysis Mode: Complete Document Ingestion")
print(f"[CALIBRATION] Recursive until consistency achieved\n")

# Fetch control group if not already archived
print("[PHASE 1] Securing Control Group Filings...")
filings = fetch_sec_filings_by_cik(
    cik=CIK_NIKE,
    form_type="4",
    year_start=CONTROL_GROUP_YEAR,
    year_end=CONTROL_GROUP_YEAR,
    limit=CONTROL_GROUP_SIZE
)

if len(filings) != CONTROL_GROUP_SIZE:
    print(f"[WARNING] Expected {CONTROL_GROUP_SIZE} filings, got {len(filings)}")

print(f"[OK] Control group secured: {len(filings)} filings\n")

# Comprehensive analysis
print("="*80)
print("[PHASE 2] COMPLETE DOCUMENT INGESTION")
print("="*80)

analysis_results = []
run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

for i, filing in enumerate(filings, 1):
    print(f"\n{'='*80}")
    print(f"Filing {i}/{len(filings)}: {filing['accession_number']}")
    print(f"{'='*80}")
    
    archived_path = filing.get('archived', {}).get('archived_path')
    
    if not archived_path or not Path(archived_path).exists():
        print(f"[ERROR] Archive not found: {archived_path}")
        continue
    
    print(f"[FILE] {Path(archived_path).name}")
    print(f"[SIZE] {Path(archived_path).stat().st_size:,} bytes")
    print(f"\n[EXTRACTING] Initiating complete extraction...\n")
    
    # Use comprehensive document parser
    parser = DocumentParser(archived_path)
    profile = parser.extract_complete_profile()
    
    # STRICT VALIDATION - Zero tolerance for N/A, True/False, or missing data
    print(f"\n[VALIDATING] Checking data quality...")
    is_valid, errors = validate_complete_filing(profile)
    
    if not is_valid:
        # Generate ERROR report instead of garbage
        report = generate_error_report(filing, errors)
        print(f"[FAILED] Data quality check failed with {len(errors)} errors")
        print("First 3 errors:")
        for e in errors[:3]:
            print(f"  - {e[:150]}")
    else:
        # Generate report only if data passes validation
        report = parser.generate_report()
        print(f"[PASSED] Data quality check successful")
    
    # Save individual filing report (either valid or error report)
    report_path = ANALYSIS_OUTPUT_DIR / f"filing_{i:02d}_{filing['accession_number'].replace('-', '')}_run_{run_timestamp}.txt"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(report)
    
    # Add to analysis results
    analysis_results.append({
        "filing_number": i,
        "accession_number": filing['accession_number'],
        "filing_date": filing['filing_date'],
        "archive_path": archived_path,
        "report_path": str(report_path),
        "extracted_profile": profile,
    })
    
    print(f"\n[OK] Report saved: {report_path}")

# Save comprehensive analysis JSON
analysis_json_path = ANALYSIS_OUTPUT_DIR / f"complete_analysis_run_{run_timestamp}.json"
with open(analysis_json_path, 'w', encoding='utf-8') as f:
    json.dump(analysis_results, f, indent=2, default=str)

print(f"\n{'='*80}")
print("[SUMMARY] CALIBRATION RUN SUMMARY")
print(f"{'='*80}")
print(f"Run Timestamp: {run_timestamp}")
print(f"Total Filings Analyzed: {len(analysis_results)}")
print(f"Reports Generated: {len(analysis_results)}")
print(f"Analysis JSON: {analysis_json_path}")
print(f"{'='*80}\n")

# Consistency check across filings
print("[PHASE 3] Cross-Filing Consistency Analysis")
print("="*80)

# Aggregate statistics
total_transactions = sum(len(r['extracted_profile']['transactions']) for r in analysis_results)
total_holdings = sum(len(r['extracted_profile']['holdings']) for r in analysis_results)
total_footnotes = sum(r['extracted_profile']['footnotes']['total_count'] for r in analysis_results)
total_dollar_amounts = sum(r['extracted_profile']['dollar_amounts']['count'] for r in analysis_results)
total_zero_dollars = sum(r['extracted_profile']['dollar_amounts']['zero_dollar_count'] for r in analysis_results)
total_class_mentions = sum(r['extracted_profile']['stock_classes']['total_class_mentions'] for r in analysis_results)

print(f"\nAggregate Statistics Across Control Group:")
print(f"  Total Transactions: {total_transactions}")
print(f"  Total Holdings: {total_holdings}")
print(f"  Total Footnotes: {total_footnotes}")
print(f"  Dollar Amounts Found: {total_dollar_amounts}")
print(f"  Zero-Dollar Flags: {total_zero_dollars}")
print(f"  Stock Class Mentions: {total_class_mentions}")

# Identify unique patterns
print(f"\n{'='*80}")
print("[ANALYSIS] Unique Elements Detected:")
print(f"{'='*80}")

# Collect all unique reporting owners
all_owners = set()
for r in analysis_results:
    owner = r['extracted_profile']['reporting_owner'].get('name')
    if owner:
        all_owners.add(owner)

print(f"\nUnique Reporting Owners ({len(all_owners)}):")
for owner in sorted(all_owners):
    print(f"  - {owner}")

# Collect all unique officer titles
all_titles = set()
for r in analysis_results:
    title = r['extracted_profile']['reporting_owner'].get('relationship', {}).get('officer_title')
    if title:
        all_titles.add(title)

print(f"\nUnique Officer Titles ({len(all_titles)}):")
for title in sorted(all_titles):
    print(f"  - {title}")

# Date range
all_dates = [r['filing_date'] for r in analysis_results if r['filing_date']]
if all_dates:
    print(f"\nDate Range: {min(all_dates)} to {max(all_dates)}")

print(f"\n{'='*80}")
print("[COMPLETE] CALIBRATION RUN COMPLETE")
print(f"{'='*80}")
print(f"\n[OUTPUT] All reports saved to: {ANALYSIS_OUTPUT_DIR}")
print(f"[FILES] Individual filing reports: {len(analysis_results)} files")
print(f"[JSON] Comprehensive JSON: {analysis_json_path}")
print(f"\n[STATUS] Ready for next calibration iteration")
print(f"{'='*80}\n")


