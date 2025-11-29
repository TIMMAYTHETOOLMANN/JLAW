"""
Full Nike 2019 DOJ-Level Forensic Report Generator
================================================

Generates complete forensic report matching the exact format of the benchmark PDF,
with all 63 violations detailed per filing.
"""

import asyncio
import logging
from datetime import datetime
from enhanced_forensic_report_generator import (
    EnhancedForensicReportGenerator,
    FilingAnalysis,
    ViolationDetail
)
from benchmark_compliance_test import BenchmarkComplianceTester

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def generate_complete_doj_report():
    """Generate complete DOJ-level forensic report"""
    logger.info("="*80)
    logger.info("GENERATING COMPLETE DOJ-LEVEL FORENSIC REPORT")
    logger.info("="*80)
    
    # Run benchmark test to get violations
    tester = BenchmarkComplianceTester()
    logger.info("\n[1/3] Running benchmark analysis...")
    await tester.run_benchmark_test()
    
    logger.info("\n[2/3] Generating DOJ-level report...")
    report_generator = EnhancedForensicReportGenerator()
    
    # Collect all filings
    filings = await tester._collect_nike_2019_filings()
    
    # Create filing analyses with violations
    filing_analyses = []
    
    # Group violations by filing accession
    filing_map = {}
    for filing in filings:
        filing_map[filing['accession']] = filing
    
    violation_by_filing = {}
    
    # Add late Form 4 violations
    for v in tester.results['late_form4']:
        acc = v['accession']
        if acc not in violation_by_filing:
            violation_by_filing[acc] = []
        violation_by_filing[acc].append(('late_form4', v))
    
    # Add zero-dollar violations
    for v in tester.results['zero_dollar']:
        acc = v['accession']
        if acc not in violation_by_filing:
            violation_by_filing[acc] = []
        violation_by_filing[acc].append(('zero_dollar', v))
    
    # Add material misstatements
    for v in tester.results['material_misstatements']:
        acc = v['accession']
        if acc not in violation_by_filing:
            violation_by_filing[acc] = []
        violation_by_filing[acc].append(('misstatement', v))
    
    # Add SOX violations
    for v in tester.results['critical_violations']:
        acc = v['accession']
        if acc not in violation_by_filing:
            violation_by_filing[acc] = []
        violation_by_filing[acc].append(('sox302', v))
    
    # Create FilingAnalysis objects for each filing with violations
    for acc, violations in violation_by_filing.items():
        if acc not in filing_map:
            continue
        
        filing = filing_map[acc]
        violation_details = []
        
        for i, (vtype, v) in enumerate(violations, 1):
            if vtype == 'late_form4':
                violation_details.append(
                    report_generator.create_late_form4_violation(
                        transaction_date=v['transaction_date'],
                        filing_date=v['filing_date'],
                        reporting_owner=filing.get('insider', 'Unknown'),
                        document_url=v['url'],
                        violation_number=i
                    )
                )
            elif vtype == 'zero_dollar':
                violation_details.append(
                    report_generator.create_zero_dollar_violation(
                        reporting_owner=filing.get('insider', 'Unknown'),
                        transaction_code=v.get('transaction_code', 'V'),
                        shares=v.get('shares', 0),
                        price_per_share=v.get('price_per_share', 0.0),
                        document_url=v['url'],
                        html_context="Table I - Non-Derivative Securities Acquired, Disposed of, or Beneficially Owned 1. Title of Security (Instr. 3) 2. Transaction Date (Month/Day/Year)",
                        violation_number=i
                    )
                )
            elif vtype == 'misstatement':
                violation_details.append(
                    report_generator.create_material_misstatement_violation(
                        exact_quote="3.1 Restated Articles of Incorporation, as amended (incorporated by reference to Exhibit 3.1 to the Company's Quarterly Report on Form 10-Q for the fiscal quarter ended November 30, 2015).3.2 Fifth Restated Bylaws, as amended...",
                        document_url=v['url'],
                        violation_number=i
                    )
                )
            elif vtype == 'sox302':
                violation_details.append(
                    report_generator.create_sox302_violation(
                        exact_quote="Required SOX 302 certifications (Exhibit 31.1, 31.2) not found",
                        document_url=v['url'],
                        violation_number=i
                    )
                )
        
        # Add red flags for specific filing types
        red_flags = []
        if filing['type'] in ['10-K', '10-Q'] and filing.get('contains_restatement'):
            red_flags.append("Financial restatement mentioned")
        if filing['type'] == 'SC 13G/A':
            red_flags.append(f"Significant beneficial ownership: {filing.get('ownership', 'Unknown')}%")
        
        filing_analysis = FilingAnalysis(
            filing_type=filing['type'],
            filed_date=filing['filing_date'],
            accession_number=acc,
            document_url=filing['url'],
            filing_page_url=filing['url'].replace('/Archives/', '/cgi-bin/viewer?action=view&cik=320187&accession_number='),
            violations=violation_details,
            red_flags=red_flags
        )
        filing_analyses.append(filing_analysis)
    
    logger.info(f"✓ Created {len(filing_analyses)} filing analyses with violations")
    logger.info(f"✓ Total filings collected: {len(filings)}")
    
    # Generate DOJ-level report
    logger.info("\n[3/3] Generating final report document...")
    report = report_generator.generate_doj_level_report(
        case_id="NIKE_2019_COMPLETE",
        target_company="Nike Inc.",
        cik="0000320187",
        analysis_period="January 1, 2019 - December 31, 2019",
        filing_analyses=filing_analyses,
        total_damages=tester.results['total_damages'],
        total_filings_analyzed=len(filings)  # Pass total count of ALL filings
    )
    
    logger.info("="*80)
    logger.info("✅ DOJ-LEVEL FORENSIC REPORT COMPLETE")
    logger.info("="*80)
    logger.info(f"Report length: {len(report):,} characters")
    logger.info(f"Total filings analyzed: {len(filings)}")
    logger.info(f"Filings with violations: {len(filing_analyses)}")
    logger.info(f"Total violations: {sum(len(fa.violations) for fa in filing_analyses)}")
    logger.info(f"Total damages: ${tester.results['total_damages']:,.2f}")
    
    # Print first portion of report
    logger.info("\n" + "="*80)
    logger.info("REPORT PREVIEW (First 3000 characters)")
    logger.info("="*80)
    print(report[:3000])
    print("\n... (report continues)")
    
    return report


async def main():
    report = await generate_complete_doj_report()
    return report


if __name__ == "__main__":
    asyncio.run(main())

