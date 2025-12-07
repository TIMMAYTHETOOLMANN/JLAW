#!/usr/bin/env python3
"""
Simple Usage Example - JLAW Unified Forensic Analyzer
======================================================

This example demonstrates basic usage of the unified forensic pipeline.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.forensics.unified_forensic_pipeline import UnifiedForensicPipeline
from src.forensics.unified_report_generator import UnifiedReportGenerator
from datetime import datetime


async def analyze_company(ticker: str, year: int):
    """
    Analyze a company for a specific year.
    
    Args:
        ticker: Stock ticker symbol (e.g., "NKE")
        year: Analysis year (e.g., 2019)
    """
    print("=" * 80)
    print(f"JLAW Unified Forensic Analysis: {ticker} {year}")
    print("=" * 80)
    print()
    
    # Initialize pipeline
    print("Initializing forensic pipeline...")
    pipeline = UnifiedForensicPipeline()
    
    # Execute 13-phase analysis
    print(f"Executing comprehensive forensic analysis of {ticker} for {year}...")
    print("This will run all 13 phases:")
    print("  1. Document Acquisition")
    print("  2. DocsGPT Parsing")
    print("  3. Agent-Powered Scraping")
    print("  4. Quantitative Forensics")
    print("  5. Revenue Recognition Analysis")
    print("  6. Financial Flow Analysis")
    print("  7. Linguistic Deception Detection")
    print("  8. Temporal Analysis")
    print("  9. Contradiction Detection")
    print("  10. ML Fraud Detection")
    print("  11. Statutory Mapping")
    print("  12. Dual-Agent Prosecution")
    print("  13. Report Generation")
    print()
    
    try:
        # Execute pipeline
        context = await pipeline.execute(
            ticker=ticker,
            year=year
        )
        
        # Display summary
        print()
        print("=" * 80)
        print("ANALYSIS COMPLETE")
        print("=" * 80)
        print()
        print("Summary:")
        print(f"  Company: {context.company_name}")
        print(f"  CIK: {context.cik}")
        print(f"  Period: {context.analysis_period_start} to {context.analysis_period_end}")
        print(f"  Filings Analyzed: {len(context.filings)}")
        print(f"  Documents Parsed: {len(context.parsed_documents)}")
        print()
        print("Forensic Findings:")
        print(f"  Violations Identified: {len(context.violations)}")
        print(f"  Criminal Referrals: {len(context.criminal_referrals)}")
        print(f"  Contradictions Found: {len(context.contradictions)}")
        print(f"  Timeline Anomalies: {len(context.timeline_anomalies)}")
        print()
        print("Risk Scores:")
        print(f"  Beneish M-Score: {context.beneish_score:.4f}")
        print(f"  Fraud Probability: {context.fraud_probability:.2%}")
        print(f"  ML Ensemble Score: {context.ml_fraud_scores.get('ensemble_score', 0):.2%}")
        print()
        
        # Generate reports
        print("Generating comprehensive report package...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        company_name = context.company_name.replace(" ", "_").replace(",", "")
        output_dir = Path("output") / f"{company_name}_{year}_FORENSIC_ANALYSIS_{timestamp}"
        
        generator = UnifiedReportGenerator(output_dir)
        report_path = generator.generate_full_report(context)
        
        print(f"✅ Reports generated successfully!")
        print()
        print("Output Files:")
        print(f"  Main Report: {report_path / 'FORENSIC_REPORT.md'}")
        print(f"  Executive Summary: {report_path / 'executive_summary.md'}")
        print(f"  Machine-Readable: {report_path / 'machine_readable/'}")
        print(f"  Evidence Chain: {report_path / 'evidence/chain_of_custody.json'}")
        print()
        print("=" * 80)
        
        return context
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """Main entry point."""
    # Example 1: Analyze Nike 2019
    print("Example 1: Analyzing Nike 2019 SEC Filings\n")
    await analyze_company("NKE", 2019)
    
    # Example 2: Analyze another company
    # await analyze_company("AAPL", 2023)


if __name__ == "__main__":
    # Run the analysis
    asyncio.run(main())
