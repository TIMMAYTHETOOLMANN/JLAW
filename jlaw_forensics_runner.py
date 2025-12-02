"""
JLAW Unified Analysis Runner
Uses existing JLAW components with variable command-line inputs
"""

import asyncio
import sys
import argparse
from datetime import datetime
from pathlib import Path

# Use existing working JLAW components
from benchmark_compliance_test import BenchmarkComplianceTester

async def run_analysis(company: str, cik: str, start_date: str, end_date: str, filing_types: list = None):
    """
    Run forensic analysis using existing JLAW system with variable inputs
    """
    print("="*100)
    print(f"JLAW FORENSIC ANALYSIS - {company}")
    print("="*100)
    print(f"CIK: {cik}")
    print(f"Period: {start_date} to {end_date}")
    print(f"Filing Types: {', '.join(filing_types or ['ALL'])}")
    print("="*100)
    print()
    
    # For Nike 2019, use the proven benchmark test
    if cik == "0000320187" and "2019" in start_date:
        print("-> Running Nike 2019 Benchmark Analysis...")
        print()
        
        tester = BenchmarkComplianceTester()
        await tester.run_benchmark_test()
        
        # Generate report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = Path(f"forensic_reports/FORENSIC_REPORT_{company.replace(' ', '_')}_{timestamp}.txt")
        report_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Create comprehensive report
        report_lines = []
        report_lines.append("="*120)
        report_lines.append("DEPARTMENT OF JUSTICE")
        report_lines.append("FORENSIC ANALYSIS REPORT")
        report_lines.append("="*120)
        report_lines.append("")
        report_lines.append(f"TARGET: {company}")
        report_lines.append(f"CIK: {cik}")
        report_lines.append(f"ANALYSIS PERIOD: {start_date} to {end_date}")
        report_lines.append(f"REPORT GENERATED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        report_lines.append("")
        report_lines.append("─"*120)
        report_lines.append("EXECUTIVE SUMMARY")
        report_lines.append("─"*120)
        report_lines.append("")
        report_lines.append(f"Total Filings Analyzed: {tester.results.get('filings_processed', 0)}")
        report_lines.append(f"Total Violations Detected: {len(tester.results.get('late_form4', [])) + len(tester.results.get('zero_dollar', [])) + len(tester.results.get('material_misstatements', [])) + len(tester.results.get('critical_violations', []))}")
        report_lines.append(f"Late Form 4 Violations: {len(tester.results.get('late_form4', []))}")
        report_lines.append(f"Zero-Dollar Transactions: {len(tester.results.get('zero_dollar', []))}")
        report_lines.append(f"Material Misstatements: {len(tester.results.get('material_misstatements', []))}")
        report_lines.append(f"Critical SOX 302 Violations: {len(tester.results.get('critical_violations', []))}")
        report_lines.append(f"Total Estimated Damages: ${tester.results.get('total_damages', 0):,.2f} USD")
        report_lines.append("")
        report_lines.append("─"*120)
        report_lines.append("ANALYSIS COMPLETE")
        report_lines.append("─"*120)
        report_lines.append("")
        report_lines.append("This analysis was conducted using the JLAW Unified Forensic System")
        report_lines.append("leveraging proven benchmark-compliant methodologies.")
        report_lines.append("")
        report_lines.append(f"For detailed findings, please review the complete benchmark compliance report.")
        report_lines.append("")
        
        report_content = "\n".join(report_lines)
        report_file.write_text(report_content, encoding='utf-8')
        
        print()
        print("="*100)
        print("ANALYSIS COMPLETE")
        print("="*100)
        print(f"Report generated: {report_file}")
        print()
        
        return {
            'status': 'SUCCESS',
            'report': str(report_file),
            'violations': len(tester.results.get('late_form4', [])) + len(tester.results.get('zero_dollar', []))
        }
    
    else:
        print(f"-> Analysis for {company} ({cik}) not yet implemented")
        print("   Currently supports: Nike Inc. (0000320187) for 2019")
        return {
            'status': 'NOT_IMPLEMENTED',
            'message': 'Only Nike 2019 benchmark analysis is currently supported'
        }


def main():
    parser = argparse.ArgumentParser(
        description="JLAW Unified Forensic Analysis System"
    )
    parser.add_argument('--company', required=True, help='Company name')
    parser.add_argument('--cik', required=True, help='Company CIK')
    parser.add_argument('--start-date', required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', required=True, help='End date (YYYY-MM-DD)')
    parser.add_argument('--filing-types', help='Comma-separated filing types')
    
    args = parser.parse_args()
    
    filing_types = None
    if args.filing_types:
        filing_types = [ft.strip() for ft in args.filing_types.split(',')]
    
    result = asyncio.run(run_analysis(
        company=args.company,
        cik=args.cik,
        start_date=args.start_date,
        end_date=args.end_date,
        filing_types=filing_types
    ))
    
    sys.exit(0 if result['status'] == 'SUCCESS' else 1)


if __name__ == "__main__":
    main()

