"""
JARVIS:LAW - Surgical Form 4 Extraction
Process all 10 control group Form 4 files with 100% data extraction
NO N/A. NO True/False. ONLY REAL DATA or ERRORS.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from form4_html_parser import Form4HTMLParser

# Output directories
OUTPUT_DIR = Path(__file__).parent / "memory/forensic_analysis"
CALIBRATION_DIR = Path(__file__).parent / "memory/calibration_runs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CALIBRATION_DIR.mkdir(parents=True, exist_ok=True)

# Control group files
CONTROL_GROUP = [
    "0000320187_4_2019-12-31_000112760219035995.xml",
    "0000320187_4_2019-12-26_000112760219035842.xml",
    "0000320187_4_2019-12-26_000112760219035840.xml",
    "0000320187_4_2019-12-03_000112760219034173.xml",
    "0000320187_4_2019-11-15_000112760219032863.xml",
    "0000320187_4_2019-10-31_000112760219031375.xml",
    "0000320187_4_2019-10-31_000112760219031373.xml",
    "0000320187_4_2019-10-31_000112760219031371.xml",
    "0000320187_4_2019-10-31_000112760219031367.xml",
    "0000320187_4_2019-10-31_000032018719000077.xml",
]

FILING_DIR = Path(__file__).parent / "memory/sec_filings_archive"

def validate_transaction(trans: Dict) -> tuple[bool, List[str]]:
    """
    Validate that transaction has ALL required fields with REAL data.
    Returns (is_valid, missing_fields)
    """
    required_fields = {
        'transaction_date': 'Transaction Date',
        'transaction_code': 'Transaction Code',
        'shares': 'Share Count',
        'price_per_share': 'Price Per Share',
        'acquired_disposed': 'Acquired/Disposed Flag',
        'shares_owned_after': 'Shares Owned After Transaction',
        'direct_indirect': 'Ownership Type (D/I)'
    }
    
    missing = []
    for field, label in required_fields.items():
        if field not in trans or not trans[field] or trans[field] in ['N/A', 'Unknown', 'None']:
            missing.append(label)
    
    return (len(missing) == 0, missing)

def generate_forensic_report(filing_num: int, file_name: str, data: Dict) -> str:
    """
    Generate detailed forensic report with 100% data validation.
    """
    lines = []
    lines.append("=" * 100)
    lines.append(f"JARVIS:LAW SURGICAL FORM 4 EXTRACTION - FILING #{filing_num}")
    lines.append("=" * 100)
    
    lines.append(f"\nFile: {file_name}")
    lines.append(f"Extraction Time: {datetime.now().isoformat()}")
    
    # Reporting Owner
    lines.append("\n" + "=" * 100)
    lines.append("REPORTING OWNER")
    lines.append("=" * 100)
    
    owner = data.get('reporting_owner', {})
    lines.append(f"Name: {owner.get('name', 'ERROR - NOT EXTRACTED')}")
    lines.append(f"CIK: {owner.get('cik', 'ERROR - NOT EXTRACTED')}")
    
    if 'address' in owner:
        addr = owner['address']
        lines.append(f"Address: {addr.get('street', 'ERROR')}")
        lines.append(f"         {addr.get('city', 'ERROR')}, {addr.get('state', 'ERROR')} {addr.get('zipcode', 'ERROR')}")
    
    if 'relationship' in owner:
        lines.append("\nRelationship to Issuer:")
        rel = owner['relationship']
        for key, value in rel.items():
            lines.append(f"  {key}: {value}")
    
    # Issuer
    lines.append("\n" + "=" * 100)
    lines.append("ISSUER INFORMATION")
    lines.append("=" * 100)
    
    issuer = data.get('issuer', {})
    lines.append(f"Company: {issuer.get('name', 'ERROR - NOT EXTRACTED')}")
    lines.append(f"CIK: {issuer.get('cik', 'ERROR - NOT EXTRACTED')}")
    lines.append(f"Trading Symbol: {issuer.get('trading_symbol', 'ERROR - NOT EXTRACTED')}")
    
    # Transactions
    lines.append("\n" + "=" * 100)
    transactions = data.get('transactions', [])
    lines.append(f"TRANSACTIONS ({len(transactions)} total)")
    lines.append("=" * 100)
    
    valid_count = 0
    validation_errors = []
    
    for i, trans in enumerate(transactions, 1):
        lines.append(f"\nTransaction #{i} - {trans.get('type', 'UNKNOWN').upper()}")
        lines.append("-" * 80)
        
        # Display all fields
        lines.append(f"  Security Title: {trans.get('security_title', 'NOT EXTRACTED')}")
        lines.append(f"  Transaction Date: {trans.get('transaction_date', 'NOT EXTRACTED')}")
        lines.append(f"  Transaction Code: {trans.get('transaction_code', 'NOT EXTRACTED')}")
        lines.append(f"  Shares: {trans.get('shares', 'NOT EXTRACTED')}")
        
        if 'exercise_price' in trans:
            lines.append(f"  Exercise Price: ${trans.get('exercise_price')}")
        
        lines.append(f"  Price Per Share: ${trans.get('price_per_share', 'NOT EXTRACTED')}")
        lines.append(f"  Acquired/Disposed: {trans.get('acquired_disposed', 'NOT EXTRACTED')}")
        lines.append(f"  Shares Owned After: {trans.get('shares_owned_after', 'NOT EXTRACTED')}")
        lines.append(f"  Ownership Type: {trans.get('direct_indirect', 'NOT EXTRACTED')}")
        
        if 'nature_of_indirect' in trans and trans['nature_of_indirect']:
            lines.append(f"  Nature of Indirect: {trans['nature_of_indirect']}")
        
        if 'underlying_security_title' in trans:
            lines.append(f"  Underlying Security: {trans.get('underlying_security_title')}")
            lines.append(f"  Underlying Shares: {trans.get('underlying_security_shares', 'NOT EXTRACTED')}")
        
        if 'expiration_date' in trans:
            lines.append(f"  Expiration Date: {trans.get('expiration_date')}")
        
        # Validate
        is_valid, missing = validate_transaction(trans)
        if is_valid:
            valid_count += 1
            lines.append(f"  [STATUS] VALID - All required fields extracted")
        else:
            lines.append(f"  [STATUS] INVALID - Missing: {', '.join(missing)}")
            validation_errors.append(f"Transaction #{i}: Missing {', '.join(missing)}")
    
    # Footnotes
    if data.get('footnotes'):
        lines.append("\n" + "=" * 100)
        lines.append(f"EXPLANATORY FOOTNOTES ({len(data['footnotes'])} total)")
        lines.append("=" * 100)
        for fn in data['footnotes']:
            lines.append(f"\n[{fn.get('id')}] {fn.get('text')}")
    
    # Summary
    lines.append("\n" + "=" * 100)
    lines.append("EXTRACTION QUALITY SUMMARY")
    lines.append("=" * 100)
    
    if valid_count == len(transactions) and len(transactions) > 0:
        lines.append(f"\n[PASS] {valid_count}/{len(transactions)} transactions have complete data")
        lines.append("[PASS] This filing meets forensic extraction standards")
    else:
        lines.append(f"\n[FAIL] Only {valid_count}/{len(transactions)} transactions have complete data")
        lines.append("\nValidation Errors:")
        for error in validation_errors:
            lines.append(f"  - {error}")
        lines.append("\n[FAIL] This filing does NOT meet forensic extraction standards")
    
    lines.append("\n" + "=" * 100)
    
    return "\n".join(lines)

def main():
    """
    Process all 10 control group Form 4 files.
    """
    print("=" * 100)
    print("JARVIS:LAW SURGICAL FORM 4 EXTRACTION - CONTROL GROUP ANALYSIS")
    print("=" * 100)
    print(f"\nProcessing {len(CONTROL_GROUP)} Form 4 filings...")
    print(f"Source: {FILING_DIR}")
    
    all_results = []
    successful = 0
    failed = 0
    
    for i, filename in enumerate(CONTROL_GROUP, 1):
        print(f"\n[{i}/{len(CONTROL_GROUP)}] Processing: {filename}")
        
        file_path = FILING_DIR / filename
        
        if not file_path.exists():
            print(f"  [ERROR] File not found: {file_path}")
            failed += 1
            continue
        
        try:
            # Parse the Form 4
            parser = Form4HTMLParser(file_path)
            data = parser.extract_all()
            
            # Extract accession number from filename
            accession = filename.split('_')[3].replace('.xml', '')
            
            # Generate report
            report = generate_forensic_report(i, filename, data)
            
            # Save individual report
            report_file = CALIBRATION_DIR / f"filing_{i:02d}_{accession}_surgical_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            
            print(f"  [OK] Report saved: {report_file.name}")
            
            # Add to results
            all_results.append({
                'filing_number': i,
                'filename': filename,
                'accession': accession,
                'data': data,
                'report_file': str(report_file)
            })
            
            successful += 1
            
        except Exception as e:
            print(f"  [ERROR] Extraction failed: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    # Save complete JSON
    complete_file = CALIBRATION_DIR / f"complete_surgical_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(complete_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2)
    
    print("\n" + "=" * 100)
    print("EXTRACTION COMPLETE")
    print("=" * 100)
    print(f"\nSuccessful: {successful}/{len(CONTROL_GROUP)}")
    print(f"Failed: {failed}/{len(CONTROL_GROUP)}")
    print(f"\nComplete analysis saved: {complete_file}")
    print("=" * 100)

if __name__ == "__main__":
    main()

