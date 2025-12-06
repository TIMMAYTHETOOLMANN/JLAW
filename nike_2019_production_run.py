"""
Nike 2019 Full Batch Analysis - Production Run
Target: 54+ violations from 89 filings (BENCHMARK GOLDSTANDARD)
"""

import asyncio
import sys
import json
from datetime import datetime

sys.path.insert(0, 'C:/Users/timot/IdeaProjects/JLAW')

from src.forensics.forensic_orchestrator import ForensicOrchestrator, ForensicCase
from src.forensics.config_manager import ConfigurationManager

async def run_nike_2019_production():
    """Execute full Nike 2019 analysis with Holy Grail integration."""
    
    print("="*80)
    print("NIKE 2019 PRODUCTION ANALYSIS - HOLY GRAIL ENABLED")
    print("="*80)
    print(f"\nTarget: 54+ violations from 89 filings")
    print(f"Company: Nike Inc (CIK: 0000320187)")
    print(f"Period: 2019-01-01 to 2019-12-31")
    print(f"Forms: 10-K, 10-Q, 4")
    print("\n" + "-"*80 + "\n")
    
    # Initialize system
    config_mgr = ConfigurationManager()
    config = config_mgr.config  # Get SystemConfig
    
    # Create storage config
    from src.forensics.immutable_storage import StorageConfig
    storage_config = StorageConfig(
        provider=config.storage_provider  # LOCAL, AWS, or AZURE
    )
    
    orchestrator = ForensicOrchestrator(
        govinfo_api_key=config.govinfo.api_key,
        storage_config=storage_config,
        audit_signing_key=b"nike-2019-production-key",
        user_agent="NITS Recon Unit contact@nits-secops.org"
    )
    
    # Create case
    case = ForensicCase(
        case_id=f"NIKE_2019_PROD_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        target_cik="0000320187",
        target_company="Nike Inc",
        investigation_start=datetime.now()
    )
    
    print("[1] Collecting filings from SEC...")
    
    # Collect filings (years parameter is ignored, hardcoded for 2019)
    filings = await orchestrator._collect_filings(
        case=case,
        filing_types=["10-K", "10-Q", "4"],
        years=1  # Actually hardcoded to 2019 in the method
    )
    
    print(f"    ✓ Collected {len(filings)} filings")
    
    # Count by type
    form_counts = {}
    for filing in filings:
        form_type = filing.get('form_type', 'UNKNOWN')
        form_counts[form_type] = form_counts.get(form_type, 0) + 1
    
    print(f"\n    Filing breakdown:")
    for form_type, count in sorted(form_counts.items()):
        print(f"      {form_type}: {count}")
    
    print(f"\n[2] Analyzing filings with Holy Grail Universal Extractor...")
    print(f"    (This will take 5-10 minutes with rate limiting)")
    
    all_violations = []
    analyzed_count = 0
    
    for i, filing in enumerate(filings, 1):
        form_type = filing.get('form_type', 'UNKNOWN')
        filing_date = filing.get('filing_date', 'UNKNOWN')
        
        print(f"\n    [{i}/{len(filings)}] {form_type} ({filing_date})")
        
        try:
            if form_type in ('4', '4/A'):
                # Form 4 analysis with Holy Grail
                from src.forensics.insider_form4_analyzer import InsiderForm4Analyzer
                
                analyzer = InsiderForm4Analyzer(user_agent="NITS Recon Unit contact@nits-secops.org")
                violations = await analyzer.analyze_form4(
                    xml_url=filing.get('document_url', ''),
                    viewer_url=filing.get('viewer_url'),
                    filing_date_str=filing_date
                )
                
                if violations:
                    print(f"        ✓ Found {len(violations)} violations")
                    for v in violations:
                        print(f"          - {v.type}: {v.description}")
                    all_violations.extend(violations)
                else:
                    print(f"        • No violations")
                
                analyzed_count += 1
                
            elif form_type in ('10-K', '10-K/A', '10-Q', '10-Q/A'):
                # 10-K/10-Q analysis using SEC EDGAR Analyzer
                from src.forensics.sec_edgar_analyzer import SECForensicAnalyzer
                
                analyzer = SECForensicAnalyzer(user_agent="NITS Recon Unit contact@nits-secops.org")
                
                # Extract accession number from the filing
                accession = filing.get('accession', '')
                
                analysis = await analyzer.analyze_filing(
                    cik=case.target_cik,
                    accession_number=accession,
                    filing_type=form_type,
                    document_url=filing.get('document_url'),
                    viewer_url=filing.get('viewer_url')
                )
                
                # Convert red_flags to violation format
                for flag in analysis.red_flags:
                    # Create a violation record
                    from src.forensics.insider_form4_analyzer import Form4ViolationRecord
                    
                    violation = Form4ViolationRecord(
                        type=flag.get('type', 'unknown'),
                        severity=flag.get('severity', 'MEDIUM'),
                        statute_title=15,
                        statute_section='78m',  # Section 13 - Periodic Reports
                        description=flag.get('description', ''),
                        exact_quote=flag.get('exact_quote'),
                        document_url=flag.get('document_url', filing.get('document_url', '')),
                        viewer_url=flag.get('viewer_url', filing.get('viewer_url')),
                        document_section=flag.get('section'),
                        prosecutorial_merit='STRONG' if flag.get('severity') == 'CRITICAL' else 'MODERATE',
                        estimated_damages=flag.get('estimated_damages', 1000000),
                        evidence_refs=flag.get('evidence_refs', [])
                    )
                    all_violations.append(violation)
                
                if analysis.red_flags:
                    print(f"        ✓ Found {len(analysis.red_flags)} violations")
                    for flag in analysis.red_flags:
                        print(f"          - {flag.get('type')}: {flag.get('description', 'No description')[:60]}")
                else:
                    print(f"        • No violations")
                
                analyzed_count += 1
                
            else:
                # Unknown form type
                print(f"        • Skipping (unsupported form type: {form_type})")
        
        except Exception as e:
            print(f"        [ERROR] {str(e)[:100]}")
    
    print(f"\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)
    
    print(f"\nFiling Summary:")
    print(f"  Total Filings: {len(filings)}")
    print(f"  Analyzed: {analyzed_count}")
    print(f"  Skipped: {len(filings) - analyzed_count}")
    
    print(f"\nViolation Summary:")
    print(f"  Total Violations: {len(all_violations)}")
    
    # Group by type
    violation_types = {}
    for v in all_violations:
        v_type = v.type
        violation_types[v_type] = violation_types.get(v_type, 0) + 1
    
    print(f"\n  Breakdown:")
    for v_type, count in sorted(violation_types.items()):
        print(f"    {v_type}: {count}")
    
    # Benchmark comparison
    print(f"\n" + "="*80)
    print("BENCHMARK COMPARISON")
    print("="*80)
    
    benchmark_target = 54
    benchmark_late_form4 = 29
    benchmark_zero_dollar = 19
    
    actual_late = violation_types.get('late_form4', 0)
    actual_zero = violation_types.get('zero_dollar_transaction', 0)
    
    print(f"\nTarget Violations: {benchmark_target}")
    print(f"Actual Violations: {len(all_violations)}")
    print(f"Status: {'✓ PASS' if len(all_violations) >= benchmark_target else '✗ BELOW TARGET'}")
    
    print(f"\nLate Form 4 Filings:")
    print(f"  Target: {benchmark_late_form4}")
    print(f"  Actual: {actual_late}")
    print(f"  Status: {'✓ PASS' if actual_late >= benchmark_late_form4 else '✗ BELOW TARGET'}")
    
    print(f"\nZero-Dollar Transactions:")
    print(f"  Target: {benchmark_zero_dollar}")
    print(f"  Actual: {actual_zero}")
    print(f"  Status: {'✓ PASS' if actual_zero >= benchmark_zero_dollar else '✗ BELOW TARGET'}")
    
    # Save results
    results = {
        'timestamp': datetime.now().isoformat(),
        'case_id': case.case_id,
        'filings_total': len(filings),
        'filings_analyzed': analyzed_count,
        'violations_total': len(all_violations),
        'violations_by_type': violation_types,
        'benchmark_target': benchmark_target,
        'benchmark_met': len(all_violations) >= benchmark_target,
        'violations': [
            {
                'type': v.type,
                'severity': v.severity,
                'description': v.description,
                'quote': v.exact_quote,
                'statute': f"{v.statute_title} USC § {v.statute_section}",
                'url': v.document_url
            }
            for v in all_violations
        ]
    }
    
    output_file = f"nike_2019_production_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✓ Results saved to: {output_file}")
    print("="*80 + "\n")
    
    return len(all_violations) >= benchmark_target


if __name__ == "__main__":
    import logging
    logging.basicConfig(
        level=logging.WARNING,  # Reduce noise
        format='%(levelname)s:%(name)s:%(message)s'
    )
    
    result = asyncio.run(run_nike_2019_production())
    exit(0 if result else 1)

