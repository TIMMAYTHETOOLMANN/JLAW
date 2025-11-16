"""
JARVIS:LAW Black Site Protocol - SEC Forensics Workflow Orchestrator
Autonomous scanning and analysis of SEC filings with evidence chain integrity
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.sec_crawler import fetch_sec_filings_by_cik, search_company_by_ticker
from tools.utils import log_violation, export_evidence_chain, sha256_url


def analyze_sec_filing(filing_url: str, filing_content: str = None) -> Dict[str, Any]:
    """
    Analyze SEC filing for violations (stub for integration with jarvis_law_alpha).
    
    This function will be replaced with actual forensic analysis from 
    jarvis_law_alpha.py when integrated.
    
    Args:
        filing_url: URL to SEC filing
        filing_content: Optional pre-fetched filing content
        
    Returns:
        Analysis results with violation detection
    """
    # TODO: Integrate with jarvis_law_alpha.py analyze_filing() function
    # For now, return mock analysis structure
    
    return {
        "filing_url": filing_url,
        "violation_detected": False,
        "analysis_timestamp": datetime.utcnow().isoformat() + "Z",
        "findings": [],
        "status": "analyzed"
    }


def scan_company_filings(
    cik: str,
    form_type: str,
    year_start: int,
    year_end: int,
    company_name: str = "Unknown",
    limit: int = 100
) -> Dict[str, Any]:
    """
    Complete workflow: Fetch, analyze, and log violations for company filings.
    
    Args:
        cik: Company CIK number
        form_type: SEC form type (e.g., "4", "10-K")
        year_start: Start year
        year_end: End year
        company_name: Company name for reporting
        
    Returns:
        Scan results with flagged violations
    """
    print(f"\n{'='*70}")
    print(f"🚨 JARVIS:LAW BLACK SITE PROTOCOL - ASSET EXTRACTION")
    print(f"{'='*70}")
    print(f"Target: {company_name} (CIK: {cik})")
    print(f"Form Type: {form_type}")
    print(f"Period: {year_start}-{year_end}")
    print(f"{'='*70}\n")
    
    # Phase 1: Fetch filings from SEC.gov
    print("📡 Phase 1: Live SEC.gov extraction...")
    print(f"  Limit: {limit} filings per year")
    filings = fetch_sec_filings_by_cik(cik, form_type, year_start, year_end, limit=limit)
    print(f"✓ Extraction complete: {len(filings)} filings retrieved\n")
    
    if not filings:
        print("⚠️ No filings found. Scan aborted.")
        return {
            "status": "no_filings",
            "total_filings": 0,
            "violations": [],
            "company": company_name,
            "cik": cik
        }
    
    # Phase 2: Metadata validation and display
    print("🔍 Phase 2: Metadata Validation & Display...")
    print("\nFiling Details:")
    print("-" * 70)
    
    for i, filing in enumerate(filings, 1):
        print(f"\n[{i}/{len(filings)}] Filing Metadata:")
        print(f"  Title: {filing.get('title', 'MISSING')}")
        print(f"  Filing Date: {filing.get('filing_date', 'MISSING')}")
        print(f"  Accession #: {filing.get('accession_number', 'MISSING')}")
        print(f"  Form Type: {filing.get('form_type', 'MISSING')}")
        print(f"  CIK: {filing.get('cik', 'MISSING')}")
        print(f"  URL: {filing.get('url', 'MISSING')[:80]}...")
        
        # Check archived status
        archived = filing.get('archived', {})
        if archived:
            print(f"  Archive Status: {archived.get('status', 'UNKNOWN')}")
            print(f"  Archive Path: {archived.get('filename', 'MISSING')}")
            print(f"  Content Hash: {archived.get('content_hash', 'MISSING')[:16]}...")
            print(f"  Size: {archived.get('size_bytes', 0)} bytes")
        else:
            print(f"  Archive Status: NOT ARCHIVED")
    
    print("\n" + "-" * 70)
    
    # Phase 3: Forensic Batch Analysis
    print("\n🔬 Phase 3: Forensic Batch Analysis...")
    print("="*70)
    
    flagged = []
    batch_findings = []
    
    for i, filing in enumerate(filings, 1):
        print(f"\n[Filing {i}/{len(filings)}] {filing['accession_number']}")
        print(f"  Date: {filing['filing_date']}")
        print(f"  Processing...", end=" ")
        
        # Analyze filing content
        archived_path = filing.get('archived', {}).get('archived_path')
        
        if archived_path and Path(archived_path).exists():
            # Read archived filing content
            with open(archived_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Basic forensic analysis
            findings = {
                "filing_number": i,
                "accession_number": filing['accession_number'],
                "filing_date": filing['filing_date'],
                "content_size": len(content),
                "transactions_detected": content.count('<transactionCode>') if '<transactionCode>' in content else 0,
                "dollar_amounts": len(re.findall(r'\$[\d,]+(?:\.\d{2})?', content)),
                "zero_dollar_flags": len(re.findall(r'\$0(?:\.00)?(?!\d)', content)),
                "class_mentions": content.lower().count('class a') + content.lower().count('class b'),
                "stock_options": content.lower().count('stock option'),
                "derivative_securities": content.lower().count('derivative'),
                "footnotes": content.count('<footnote'),
            }
            
            # Violation detection (basic pattern matching)
            violation_flags = []
            if findings['zero_dollar_flags'] > 0:
                violation_flags.append(f"Zero-dollar transactions detected ({findings['zero_dollar_flags']})")
            if findings['class_mentions'] > 5:
                violation_flags.append(f"Multiple class mentions ({findings['class_mentions']})")
            if findings['footnotes'] > 10:
                violation_flags.append(f"Excessive footnotes ({findings['footnotes']})")
            
            findings['violation_flags'] = violation_flags
            findings['violation_detected'] = len(violation_flags) > 0
            
            batch_findings.append(findings)
            
            if findings['violation_detected']:
                # Log violation to evidence chain
                result = {
                    "violation_detected": True,
                    "hash": sha256_url(filing["url"]),
                    "source_url": filing["url"],
                    "filing_meta": filing,
                    "company": company_name,
                    "cik": cik,
                    "findings": findings,
                    "flags": violation_flags
                }
                violation_id = log_violation(result)
                result["violation_id"] = violation_id
                flagged.append(result)
                
                print(f"🚨 FLAGGED")
                for flag in violation_flags:
                    print(f"    └─ {flag}")
            else:
                print(f"✓ Clean")
                print(f"    └─ Transactions: {findings['transactions_detected']}, Size: {findings['content_size']} bytes")
        else:
            print(f"✗ Archive not found")
            batch_findings.append({
                "filing_number": i,
                "accession_number": filing['accession_number'],
                "error": "Archive not accessible"
            })
    
    # Generate batch analysis report
    print("\n" + "="*70)
    print("📊 BATCH ANALYSIS REPORT")
    print("="*70)
    
    total_transactions = sum(f.get('transactions_detected', 0) for f in batch_findings)
    total_zero_dollar = sum(f.get('zero_dollar_flags', 0) for f in batch_findings)
    total_violations = len(flagged)
    
    print(f"\nBatch Summary:")
    print(f"  Total Filings Analyzed: {len(batch_findings)}")
    print(f"  Total Transactions Detected: {total_transactions}")
    print(f"  Zero-Dollar Flags: {total_zero_dollar}")
    print(f"  Violations Flagged: {total_violations}")
    print(f"  Clean Filings: {len(batch_findings) - total_violations}")
    
    if total_violations > 0:
        print(f"\nFlagged Filings:")
        for result in flagged:
            print(f"  • {result['filing_meta']['accession_number']} ({result['filing_meta']['filing_date']})")
            for flag in result.get('flags', []):
                print(f"    └─ {flag}")
    
    print(f"\n✓ Analysis complete: {len(flagged)} violations flagged\n")
    
    # Phase 4: Evidence chain export
    print("📦 Phase 4: Evidence chain compilation...")
    export_path = export_evidence_chain(
        f"evidence_{company_name.replace(' ', '_')}_{form_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    print(f"✓ Evidence chain exported: {export_path}\n")
    
    # Summary report
    print(f"{'='*70}")
    print(f"📊 SCAN SUMMARY")
    print(f"{'='*70}")
    print(f"Total Filings Scanned: {len(filings)}")
    print(f"Violations Detected: {len(flagged)}")
    print(f"Evidence Chain: {export_path}")
    print(f"{'='*70}\n")
    
    return {
        "status": "complete",
        "total_filings": len(filings),
        "violations_count": len(flagged),
        "violations": flagged,
        "batch_findings": batch_findings,
        "evidence_chain": export_path,
        "company": company_name,
        "cik": cik,
        "form_type": form_type,
        "period": f"{year_start}-{year_end}"
    }


def scan_nike_form4s() -> Dict[str, Any]:
    """
    Nike Form 4 scanner - Target: Nike Inc insider trading filings.
    Controlled batch analysis: First 10 filings from fiscal year 2019.
    
    Returns:
        Scan results with flagged violations
    """
    CIK_NIKE = "0000320187"  # Nike Inc
    return scan_company_filings(
        cik=CIK_NIKE,
        form_type="4",
        year_start=2019,  # Ground zero - fiscal year 2019
        year_end=2019,    # Single year for controlled analysis
        company_name="Nike Inc",
        limit=10  # Controlled batch: first 10 filings
    )


def scan_by_ticker(
    ticker: str,
    form_type: str = "4",
    year_start: int = 2019,
    year_end: int = 2025
) -> Dict[str, Any]:
    """
    Scan company by ticker symbol.
    
    Args:
        ticker: Stock ticker symbol (e.g., "NIKE", "AAPL")
        form_type: SEC form type
        year_start: Start year
        year_end: End year
        
    Returns:
        Scan results
    """
    print(f"🔍 Looking up CIK for ticker: {ticker}")
    cik = search_company_by_ticker(ticker)
    
    if not cik:
        print(f"❌ Error: Could not find CIK for ticker '{ticker}'")
        return {
            "status": "failed",
            "error": f"CIK not found for ticker '{ticker}'"
        }
    
    print(f"✓ Found CIK: {cik}\n")
    
    return scan_company_filings(
        cik=cik,
        form_type=form_type,
        year_start=year_start,
        year_end=year_end,
        company_name=ticker.upper()
    )


if __name__ == "__main__":
    # Default execution: Nike Form 4 scan
    print("\n🚀 Launching Black Site Protocol - Default Target: Nike Inc\n")
    results = scan_nike_form4s()
    
    # Print summary
    print("\n" + "="*70)
    print("🎯 MISSION COMPLETE")
    print("="*70)
    print(json.dumps(results, indent=2, default=str))

