"""
JARVIS:LAW Black Site Protocol - Enhanced Forensic Extraction
COMPLETE detail capture - Every field, every value, every line
INTEGRATED: Statute mapping, fraud detection, chain of custody
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

sys.path.insert(0, str(Path(__file__).parent))

from tools.document_parser import DocumentParser
from tools.sec_crawler import fetch_sec_filings_by_cik
from forensic_core import (
    ChainOfCustody, ViolationType, StatuteMapper,
    HardFailureException, logger
)
from filing_analyzer import (
    FilingMetadata, FraudPatternDetector, ContentAnalyzer
)
from forensic_report_generator import ForensicReportGenerator
from visual_analytics import VisualAnalyticsEngine

# Configuration
CIK_NIKE = "0000320187"
CONTROL_GROUP_YEAR = 2019
CONTROL_GROUP_SIZE = 10
ANALYSIS_OUTPUT_DIR = Path("./memory/forensic_analysis")
ANALYSIS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def generate_detailed_forensic_report(filing_data: Dict, profile: Dict, filing_number: int,
                                      fraud_analysis: Dict = None, custody: ChainOfCustody = None) -> str:
    """
    Generate COMPLETE forensic breakdown with every detail.
    Leave nothing out.
    ENHANCED: Includes fraud detection and statute mapping.
    """
    report = []
    report.append("="*100)
    report.append(f"JARVIS:LAW COMPLETE FORENSIC EXTRACTION - FILING #{filing_number}")
    report.append("="*100)
    
    # Chain of Custody Header
    if custody:
        report.append(f"\n[CHAIN OF CUSTODY]")
        report.append(f"Evidence ID: {custody.evidence_id}")
        report.append(f"Initial Hash: {custody.initial_hash}")
        report.append(f"Created: {custody.created_at}")
        report.append(f"Custody Chain Length: {len(custody.custody_chain)}")
    
    Generate COMPLETE forensic breakdown with every detail.
    Leave nothing out.
    """
    report = []
    report.append("="*100)
    report.append(f"JARVIS:LAW COMPLETE FORENSIC EXTRACTION - FILING #{filing_number}")
    report.append("="*100)
    
    # Filing Identification
    report.append(f"\n[FILING IDENTIFICATION]")
    report.append(f"Accession Number: {filing_data['accession_number']}")
    report.append(f"Filing Date: {filing_data['filing_date']}")
    report.append(f"Form Type: {filing_data.get('form_type', 'Form 4')}")
    report.append(f"Year: {filing_data.get('year', 'N/A')}")
    report.append(f"CIK: {filing_data.get('cik', 'N/A')}")
    report.append(f"Source URL: {filing_data.get('url', 'N/A')}")
    
    # File Metadata
    report.append(f"\n[FILE METADATA]")
    meta = profile['file_metadata']
    report.append(f"Filename: {meta['filename']}")
    report.append(f"File Size: {meta['file_size']:,} bytes")
    report.append(f"Content Length: {meta['content_length']:,} characters")
    report.append(f"Line Count: {meta['line_count']} lines")
    report.append(f"Format: {profile['document_structure']['format_type']}")
    report.append(f"Last Modified: {meta['modified_time']}")
    
    # Reporting Owner - COMPLETE DETAILS
    report.append(f"\n[REPORTING OWNER - COMPLETE PROFILE]")
    owner = profile['reporting_owner']
    if owner:
        # Clean the name extraction
        raw_name = owner.get('name', 'NOT FOUND')
        # Extract clean name from HTML
        name_match = re.search(r'>([^<]+)</a>', raw_name)
        clean_name = name_match.group(1) if name_match else raw_name
        
        report.append(f"Full Name: {clean_name}")
        
        # Address
        if owner.get('address'):
            addr = owner['address']
            report.append(f"Physical Address:")
            report.append(f"  Street: {addr.get('street1', 'N/A')}")
            if addr.get('street2'):
                report.append(f"  Street 2: {addr['street2']}")
            # Try to extract city/state/zip from raw data
            report.append(f"  Location: [Full address in raw data]")
        
        # Relationship to Company
        if owner.get('relationship'):
            rel = owner['relationship']
            report.append(f"Relationship to Issuer:")
            report.append(f"  Director: {'YES' if rel.get('is_director') else 'NO'}")
            report.append(f"  Officer: {'YES' if rel.get('is_officer') else 'NO'}")
            if rel.get('officer_title'):
                report.append(f"    Title: {rel['officer_title']}")
            report.append(f"  10% Owner: {'YES' if rel.get('is_ten_percent_owner') else 'NO'}")
            report.append(f"  Other: {'YES' if rel.get('is_other') else 'NO'}")
    else:
        report.append("NOT EXTRACTED")
    
    # Issuer Information
    report.append(f"\n[ISSUER (COMPANY) INFORMATION]")
    issuer = profile['issuer_info']
    if issuer:
        report.append(f"Company Name: {issuer.get('name', 'N/A')}")
        report.append(f"Trading Symbol: {issuer.get('trading_symbol', 'N/A')}")
        report.append(f"CIK: {issuer.get('cik', 'N/A')}")
    else:
        report.append("NOT EXTRACTED")
    
    # TRANSACTIONS - EVERY DETAIL
    report.append(f"\n[TRANSACTIONS - COMPLETE BREAKDOWN]")
    transactions = profile['transactions']
    report.append(f"Total Transactions Detected: {len(transactions)}")
    
    if transactions:
        for i, trans in enumerate(transactions, 1):
            report.append(f"\n  Transaction #{i}:")
            report.append(f"    Type: {trans.get('type', 'N/A')}")
            
            # Transaction details
            if trans.get('transaction_date'):
                report.append(f"    Date: {trans['transaction_date']}")
            if trans.get('transaction_code'):
                code = trans['transaction_code']
                code_meaning = {
                    'P': 'Purchase',
                    'S': 'Sale',
                    'A': 'Award/Grant',
                    'D': 'Disposition',
                    'F': 'Tax Withholding',
                    'I': 'Discretionary Transaction',
                    'M': 'Exercise of Options',
                    'X': 'Exercise',
                    'G': 'Gift',
                    'J': 'Other'
                }
                report.append(f"    Transaction Code: {code} ({code_meaning.get(code, 'See SEC code definitions')})")
            
            if trans.get('security_title'):
                report.append(f"    Security: {trans['security_title']}")
            
            if trans.get('shares'):
                report.append(f"    Shares: {trans['shares']}")
            
            if trans.get('price_per_share'):
                report.append(f"    Price Per Share: {trans['price_per_share']}")
            
            if trans.get('acquired_disposed'):
                report.append(f"    Acquired (A) or Disposed (D): {trans['acquired_disposed']}")
            
            if trans.get('shares_owned_following'):
                report.append(f"    Shares Owned After Transaction: {trans['shares_owned_following']}")
            
            if trans.get('ownership_form'):
                report.append(f"    Ownership Type: {trans['ownership_form']}")
            
            # Raw data for validation
            if trans.get('raw_data'):
                report.append(f"    Raw Table Data: {trans['raw_data'][:3] if len(trans['raw_data']) > 3 else trans['raw_data']}")
    else:
        report.append("  No transactions detected in this filing")
    
    # HOLDINGS
    report.append(f"\n[HOLDINGS (NON-TRANSACTION OWNERSHIP)]")
    holdings = profile['holdings']
    if holdings:
        report.append(f"Total Holdings Reported: {len(holdings)}")
        for i, holding in enumerate(holdings, 1):
            report.append(f"\n  Holding #{i}:")
            report.append(f"    Type: {holding.get('type', 'N/A')}")
            report.append(f"    Security: {holding.get('security_title', 'N/A')}")
            report.append(f"    Shares Owned: {holding.get('shares_owned', 'N/A')}")
            report.append(f"    Ownership Form: {holding.get('ownership_form', 'N/A')}")
    else:
        report.append("  No holdings data in this filing")
    
    # FOOTNOTES - COMPLETE TEXT
    report.append(f"\n[FOOTNOTES]")
    footnotes = profile['footnotes']
    report.append(f"Total Footnotes: {footnotes['total_count']}")
    if footnotes['footnotes']:
        for fn in footnotes['footnotes']:
            report.append(f"\n  Footnote ID: {fn['id']}")
            report.append(f"    Text: {fn['text']}")
    
    # FINANCIAL FIGURES
    report.append(f"\n[FINANCIAL FIGURES - ALL DOLLAR AMOUNTS]")
    dollars = profile['dollar_amounts']
    report.append(f"Total Dollar Amounts Found: {dollars['count']}")
    if dollars['count'] > 0:
        report.append(f"  Amounts: {dollars['all_amounts']}")
        report.append(f"  Range: ${dollars['min']:.2f} to ${dollars['max']:.2f}")
        report.append(f"  Total Sum: ${dollars['total']:.2f}")
        report.append(f"  Zero-Dollar Entries: {dollars['zero_dollar_count']}")
    
    # DATES
    report.append(f"\n[ALL DATES IN DOCUMENT]")
    dates = profile['dates']
    report.append(f"Unique Dates Found: {dates['count']}")
    if dates['all_dates']:
        for date in sorted(dates['all_dates'])[:10]:  # Show first 10
            report.append(f"  - {date}")
    
    # NAMES
    report.append(f"\n[ALL NAMES IN DOCUMENT]")
    names = profile['names']
    report.append(f"Unique Names Found: {names['count']}")
    if names['names']:
        for name in names['names']:
            report.append(f"  - {name}")
    
    # STOCK CLASSES
    report.append(f"\n[STOCK CLASS ANALYSIS]")
    classes = profile['stock_classes']
    report.append(f"Class A Mentions: {classes['class_a_mentions']}")
    report.append(f"Class B Mentions: {classes['class_b_mentions']}")
    report.append(f"Class C Mentions: {classes['class_c_mentions']}")
    report.append(f"Total Class References: {classes['total_class_mentions']}")
    
    # FRAUD DETECTION ANALYSIS
    if fraud_analysis:
        report.append(f"\n{'='*100}")
        report.append("[FRAUD DETECTION ANALYSIS - ENHANCED]")
        report.append(f"{'='*100}")
        
        if fraud_analysis.get('patterns_detected'):
    """Execute complete forensic analysis run with fraud detection"""
            for pattern in fraud_analysis['patterns_detected']:
                report.append(f"\n  Pattern: {pattern['pattern']}")
                report.append(f"    Confidence: {pattern['confidence']:.2%}")
                report.append(f"    Indicators:")
                for indicator in pattern['indicators']:
                    report.append(f"      - {indicator}")
                if pattern.get('recommendation'):
                    report.append(f"    Recommendation: {pattern['recommendation']}")
        else:
            report.append(f"\nNo fraud patterns detected in this filing")
        
    # Initialize fraud detector and content analyzer
    fraud_detector = FraudPatternDetector()
    content_analyzer = ContentAnalyzer()
    
        report.append(f"\nOverall Risk Score: {fraud_analysis.get('risk_score', 0):.2%}")
        
        # STATUTE VIOLATIONS
        if fraud_analysis.get('statute_references'):
            report.append(f"\n[POTENTIAL VIOLATIONS - STATUTE MAPPING]")
            report.append(f"Total Potential Violations: {len(fraud_analysis['statute_references'])}")
            
            for i, statute_ref in enumerate(fraud_analysis['statute_references'], 1):
                report.append(f"\n  Violation #{i}:")
                report.append(f"    Type: {statute_ref['violation']}")
                report.append(f"    Citation: {statute_ref['citation']}")
    # Create filing metadata for fraud analysis
    filing_metadata_list = []
    for filing in filings:
        try:
            filing_date = datetime.strptime(filing['filing_date'], '%Y-%m-%d')
            period_end = filing_date  # Simplified - would parse from content
            
            metadata = FilingMetadata(
                cik=filing.get('cik', CIK_NIKE),
                form_type=filing.get('form_type', '4'),
        # Create chain of custody
        with open(archived_path, 'rb') as f:
            content_bytes = f.read()
        
        custody = ChainOfCustody(
            case_id=f"NIKE-FORM4-{filing['accession_number']}",
            collected_by={
                "system": "JARVIS-LAW",
                "operator": "AUTONOMOUS",
                "method": "SEC_EDGAR_ARCHIVE"
            },
            initial_hash=ChainOfCustody._compute_transfer_hash.__func__(
                ChainOfCustody(initial_hash="temp")
            )  # Simplified - would use actual hash
        )
        
                filing_date=filing_date,
                period_end=period_end,
                accession_number=filing['accession_number'],
                file_number=None,
        # Analyze content for violations
        content_analysis = content_analyzer.analyze_content(parser.content)
        
        # Combine with cross-filing analysis for this specific filing
        filing_fraud_analysis = {
            "patterns_detected": [],
            "violations": content_analysis.get('violations', []),
            "risk_score": cross_filing_analysis['risk_score'],
            "statute_references": []
        }
        
        # Map violations to statutes
        if filing_fraud_analysis['violations']:
            for violation in filing_fraud_analysis['violations']:
                statute = StatuteMapper.get_statute(violation['type'])
                if statute:
                    filing_fraud_analysis['statute_references'].append({
                        "violation": violation['type'].value,
                        "citation": statute.citation,
                        "description": statute.description,
                        "criminal_penalty": statute.criminal_penalty,
                        "civil_penalty": statute.civil_penalty,
                        "priority": statute.enforcement_priority,
                        "reason": violation.get('reason'),
                        "confidence": violation.get('confidence')
                    })
        
        # Generate detailed report with fraud analysis
        detailed_report = generate_detailed_forensic_report(
            filing, profile, i,
            fraud_analysis=filing_fraud_analysis,
            custody=custody
        )
            filing_metadata_list.append(metadata)
        except Exception as e:
            logger.warning(f"Could not create metadata for {filing['accession_number']}: {e}")
    
    # Run cross-filing fraud detection
    print("Phase 2: Cross-Filing Fraud Pattern Analysis...")
    cross_filing_analysis = fraud_detector.analyze_filings(filing_metadata_list)
    print(f"Risk Score: {cross_filing_analysis['risk_score']:.2%}")
    print(f"Patterns Detected: {len(cross_filing_analysis['patterns_detected'])}\n")
    
                report.append(f"    Description: {statute_ref['description']}")
                if statute_ref.get('criminal_penalty'):
                    report.append(f"    Criminal Penalty: {statute_ref['criminal_penalty']}")
                if statute_ref.get('civil_penalty'):
                    report.append(f"    Civil Penalty: {statute_ref['civil_penalty']}")
                report.append(f"    Enforcement Priority: {statute_ref['priority']} (1=highest)")
    
    # DERIVATIVES
    report.append(f"\n[DERIVATIVE SECURITIES]")
    derivs = profile['derivative_securities']
    report.append(f"Stock Options Mentioned: {derivs['stock_options']}")
    report.append(f"Warrants Mentioned: {derivs['warrants']}")
    report.append(f"Derivative Transactions: {derivs['derivative_transaction_count']}")
    report.append(f"Derivative Holdings: {derivs['derivative_holding_count']}")
    
    # SIGNATURES
    report.append(f"\n[SIGNATURES]")
    sigs = profile['signatures']
    if sigs:
        for sig in sigs:
            report.append(f"  Signed By: {sig.get('signature_name', 'N/A')}")
            report.append(f"  Date: {sig.get('signature_date', 'N/A')}")
    else:
        report.append("  No signature data extracted")
    
    report.append(f"\n{'='*100}")
    report.append("END OF COMPLETE FORENSIC EXTRACTION")
    report.append(f"{'='*100}\n")
    
    return '\n'.join(report)

def run_forensic_analysis(run_number: int) -> Dict[str, Any]:
    """Execute complete forensic analysis run"""
    
    run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = ANALYSIS_OUTPUT_DIR / f"run_{run_number}_{run_timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{'='*100}")
    print(f"FORENSIC ANALYSIS RUN #{run_number}")
    print(f"Timestamp: {run_timestamp}")
    print(f"Output Directory: {run_dir}")
    print(f"{'='*100}\n")
    
    # Fetch control group
    print("Phase 1: Securing Control Group...")
    filings = fetch_sec_filings_by_cik(
        cik=CIK_NIKE,
        form_type="4",
        year_start=CONTROL_GROUP_YEAR,
        year_end=CONTROL_GROUP_YEAR,
        limit=CONTROL_GROUP_SIZE
    )
    print(f"Control group secured: {len(filings)} filings\n")
    
    # Process each filing
    results = []
    
    for i, filing in enumerate(filings, 1):
        print(f"\n{'='*100}")
        print(f"Processing Filing {i}/{len(filings)}: {filing['accession_number']}")
        print(f"{'='*100}")
        
        archived_path = filing.get('archived', {}).get('archived_path')
        
        if not archived_path or not Path(archived_path).exists():
            print(f"ERROR: Archive not found")
            continue
        
        # Parse document
        parser = DocumentParser(archived_path)
        profile = parser.extract_complete_profile()
        
        # Generate detailed report
        detailed_report = generate_detailed_forensic_report(filing, profile, i)
        
        # Save report
        report_path = run_dir / f"filing_{i:02d}_{filing['accession_number'].replace('-', '')}_COMPLETE.txt"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(detailed_report)
        
        print(f"\nSaved: {report_path.name}")
        
        # For first 2 filings, also print to console
        if i <= 2:
            print(f"\n{'#'*100}")
            print(f"DETAILED BREAKDOWN - FILING #{i}")
            print(f"{'#'*100}")
            print(detailed_report)
        
        results.append({
            "filing_number": i,
            "accession_number": filing['accession_number'],
            "filing_date": filing['filing_date'],
            "report_path": str(report_path),
            "profile": profile
        })
    
    # Save comprehensive JSON
    json_path = run_dir / f"complete_analysis_run_{run_number}.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n{'='*100}")
    print(f"RUN #{run_number} COMPLETE")
    print(f"Reports: {len(results)}")
    print(f"JSON: {json_path}")
    print(f"{'='*100}\n")
    
    # PHASE: Generate Human-Interpretable Reports
    print("="*100)
    print("GENERATING HUMAN-INTERPRETABLE FORENSIC REPORTS")
    print("="*100)
    
    # Prepare analysis data for report
    analysis_summary = {
        "report_id": f"NIKE-FORM4-{run_timestamp}",
        "company": "Nike Inc",
        "cik": CIK_NIKE,
        "period": f"{CONTROL_GROUP_YEAR}",
        "total_filings": len(results),
        "total_violations": sum(len(r['profile'].get('violations', [])) for r in results),
        "risk_score": cross_filing_analysis.get('risk_score', 0),
        "patterns_detected": cross_filing_analysis.get('patterns_detected', []),
        "statute_references": cross_filing_analysis.get('statute_references', []),
        "filings_analyzed": [
            {
                "accession_number": r['accession_number'],
                "filing_date": r['filing_date'],
                "form_type": r['profile']['file_metadata'].get('filename', '').split('_')[2] if '_' in r['profile']['file_metadata'].get('filename', '') else '4',
                "reporting_owner": self._extract_clean_name(r['profile'].get('reporting_owner', {}).get('name', 'Unknown')),
                "transactions": r['profile'].get('transactions', []),
                "violations": r['profile'].get('violations', []),
                "late_filing": False,  # Would be calculated
                "amendments": 0
            }
            for r in results
        ]
    }
    
    # Generate human-readable report
    report_gen = ForensicReportGenerator()
    report_path = report_gen.generate_complete_report(
        analysis_summary,
        run_dir / f"FORENSIC_REPORT_RUN_{run_number}.txt"
    )
    print(f"\nHuman-Readable Report: {report_path}")
    
    # PHASE: Generate Visual Analytics
    print("\n" + "="*100)
    print("GENERATING VISUAL ANALYTICS")
    print("="*100)
    
    visual_engine = VisualAnalyticsEngine(run_dir / "visuals")
    visual_outputs = visual_engine.generate_all_analytics(analysis_summary)
    
    print(f"\nVisual Analytics Generated:")
    for viz_type, viz_path in visual_outputs.items():
        print(f"  - {viz_type.upper()}: {viz_path}")
    
    print(f"\n{'='*100}")
    print(f"COMPLETE OUTPUT PACKAGE - RUN #{run_number}")
    print(f"{'='*100}")
    print(f"1. JSON (Machine Receipt): {json_path}")
    print(f"2. Human Report: {report_path}")
    print(f"3. Visual Analytics: {len(visual_outputs)} graphics generated")
    print(f"{'='*100}\n")
    
    return {
        "run_number": run_number,
        "timestamp": run_timestamp,
        "total_filings": len(results),
        "results": results,
        "output_dir": str(run_dir),
        "report_path": str(report_path),
        "visual_outputs": {k: str(v) for k, v in visual_outputs.items()},
        "json_path": str(json_path)
    }

def _extract_clean_name(name_html: str) -> str:
    """Extract clean name from HTML"""
    import re
    match = re.search(r'>([^<]+)</a>', name_html)
    return match.group(1) if match else name_html

if __name__ == "__main__":
    print("""
================================================================================
   JARVIS:LAW BLACK SITE PROTOCOL
   DUAL-PASS FORENSIC EXTRACTION
   Complete Detail Capture - Leave Nothing Behind
================================================================================
    """)
    
    # RUN #1
    print("\n[INITIATING RUN #1 - FULL EXTRACTION]")
    run1_results = run_forensic_analysis(1)
    
    print("\n[CLEARING MEMORY CACHE]")
    import gc
    gc.collect()
    print("Memory cleared\n")
    
    # RUN #2
    print("\n[INITIATING RUN #2 - VERIFICATION PASS]")
    run2_results = run_forensic_analysis(2)
    
    # COMPARISON
    print(f"\n{'='*100}")
    print("DUAL-PASS COMPARISON")
    print(f"{'='*100}")
    
    print(f"\nRun #1: {run1_results['total_filings']} filings processed")
    print(f"Run #2: {run2_results['total_filings']} filings processed")
    
    if run1_results['total_filings'] == run2_results['total_filings']:
        print("\n[OK] Identical filing count")
    else:
        print("\n[WARNING] Filing count mismatch!")
    
    # Compare first 2 filings in detail
    print(f"\n{'='*100}")
    print("DETAILED COMPARISON - FIRST 2 FILINGS")
    print(f"{'='*100}")
    
    for i in range(min(2, len(run1_results['results']))):
        filing1 = run1_results['results'][i]
        filing2 = run2_results['results'][i]
        
        print(f"\nFiling #{i+1}:")
        print(f"  Accession: {filing1['accession_number']}")
        print(f"  Run #1 Transactions: {len(filing1['profile']['transactions'])}")
        print(f"  Run #2 Transactions: {len(filing2['profile']['transactions'])}")
        print(f"  Match: {'YES' if len(filing1['profile']['transactions']) == len(filing2['profile']['transactions']) else 'NO'}")
        
        print(f"  Run #1 Footnotes: {filing1['profile']['footnotes']['total_count']}")
        print(f"  Run #2 Footnotes: {filing2['profile']['footnotes']['total_count']}")
        print(f"  Match: {'YES' if filing1['profile']['footnotes']['total_count'] == filing2['profile']['footnotes']['total_count'] else 'NO'}")
    
    print(f"\n{'='*100}")
    print("[DUAL-PASS FORENSIC EXTRACTION COMPLETE]")
    print(f"{'='*100}\n")

