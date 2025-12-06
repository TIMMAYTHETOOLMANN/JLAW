#!/usr/bin/env python3
"""
JLAW Unified Forensic Analysis System
======================================

Single-command entry point for comprehensive SEC filing forensic analysis.

Usage:
    python jlaw_forensic.py --cik 0000320187 --year 2019
    python jlaw_forensic.py --ticker NKE --year 2019
    python jlaw_forensic.py --ticker NKE --start-date 2019-01-01 --end-date 2019-12-31

Features:
- 13-phase linear forensic pipeline
- Context-reinforcing analysis
- DocsGPT document parsing
- Dual-agent AI analysis (OpenAI + Anthropic)
- Quantitative fraud detection
- Financial flow analysis
- Revenue recognition analysis
- Linguistic deception detection
- Temporal anomaly analysis
- Contradiction detection
- ML-powered fraud scoring
- Statutory mapping with GovInfo
- DOJ-grade report generation
"""

import asyncio
import argparse
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.forensics.unified_forensic_pipeline import UnifiedForensicPipeline
from src.forensics.unified_report_generator import UnifiedReportGenerator


def setup_logging(verbose: bool = False):
    """Configure logging for the forensic analysis."""
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(f'jlaw_forensic_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        ]
    )


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='JLAW Unified Forensic Analysis System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze Nike 2019 by CIK
  python jlaw_forensic.py --cik 0000320187 --year 2019
  
  # Analyze Nike 2019 by ticker
  python jlaw_forensic.py --ticker NKE --year 2019
  
  # Analyze custom date range
  python jlaw_forensic.py --ticker NKE --start-date 2019-01-01 --end-date 2019-12-31
  
  # Verbose output
  python jlaw_forensic.py --ticker NKE --year 2019 --verbose
        """
    )
    
    # Company identification (required, one of these)
    company_group = parser.add_mutually_exclusive_group(required=True)
    company_group.add_argument(
        '--cik',
        type=str,
        help='Company CIK number (e.g., 0000320187 for Nike)'
    )
    company_group.add_argument(
        '--ticker',
        type=str,
        help='Company ticker symbol (e.g., NKE for Nike)'
    )
    
    # Time period (required)
    time_group = parser.add_mutually_exclusive_group(required=True)
    time_group.add_argument(
        '--year',
        type=int,
        help='Analysis year (e.g., 2019)'
    )
    time_group.add_argument(
        '--date-range',
        nargs=2,
        metavar=('START', 'END'),
        help='Custom date range (e.g., 2019-01-01 2019-12-31)'
    )
    
    # Alternative date specification
    parser.add_argument(
        '--start-date',
        type=str,
        help='Start date in YYYY-MM-DD format'
    )
    parser.add_argument(
        '--end-date',
        type=str,
        help='End date in YYYY-MM-DD format'
    )
    
    # Output configuration
    parser.add_argument(
        '--output-dir',
        type=str,
        default='output',
        help='Base directory for report output (default: output/)'
    )
    
    # Execution options
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging output'
    )
    
    parser.add_argument(
        '--no-report',
        action='store_true',
        help='Skip report generation (for testing pipeline only)'
    )
    
    return parser.parse_args()


async def main():
    """Main execution entry point."""
    # Parse arguments
    args = parse_arguments()
    
    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 100)
    logger.info("🔬 JLAW UNIFIED FORENSIC ANALYSIS SYSTEM")
    logger.info("=" * 100)
    logger.info(f"Version: 1.0.0")
    logger.info(f"Analysis Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("")
    
    # Resolve time period
    start_date = None
    end_date = None
    year = None
    
    if args.year:
        year = args.year
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"
    elif args.date_range:
        start_date, end_date = args.date_range
    elif args.start_date and args.end_date:
        start_date = args.start_date
        end_date = args.end_date
    else:
        logger.error("Must specify either --year or date range")
        sys.exit(1)
    
    # Log analysis parameters
    logger.info("📋 ANALYSIS PARAMETERS")
    logger.info("-" * 100)
    if args.cik:
        logger.info(f"   CIK: {args.cik}")
    if args.ticker:
        logger.info(f"   Ticker: {args.ticker}")
    logger.info(f"   Period: {start_date} to {end_date}")
    logger.info(f"   Output Directory: {args.output_dir}")
    logger.info("")
    
    try:
        # Initialize pipeline
        logger.info("🔧 Initializing forensic pipeline...")
        pipeline = UnifiedForensicPipeline()
        
        # Execute pipeline
        logger.info("🚀 Executing 13-phase forensic analysis...")
        logger.info("")
        
        context = await pipeline.execute(
            cik=args.cik,
            ticker=args.ticker,
            year=year,
            start_date=start_date,
            end_date=end_date
        )
        
        # Generate reports (Phase 13)
        if not args.no_report:
            # Create output directory structure
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            company_name = context.company_name.replace(" ", "_").replace(",", "")
            year_str = start_date[:4]
            
            output_dir = Path(args.output_dir) / f"{company_name}_{year_str}_FORENSIC_ANALYSIS_{timestamp}"
            
            logger.info("")
            logger.info("=" * 100)
            logger.info("📝 GENERATING COMPREHENSIVE REPORT PACKAGE")
            logger.info("=" * 100)
            
            generator = UnifiedReportGenerator(output_dir)
            report_path = generator.generate_full_report(context)
            
            logger.info("")
            logger.info("=" * 100)
            logger.info("✅ FORENSIC ANALYSIS COMPLETE")
            logger.info("=" * 100)
            logger.info("")
            logger.info("📊 ANALYSIS SUMMARY")
            logger.info("-" * 100)
            logger.info(f"   Company: {context.company_name}")
            logger.info(f"   CIK: {context.cik}")
            logger.info(f"   Period: {context.analysis_period_start} to {context.analysis_period_end}")
            logger.info(f"   Filings Analyzed: {len(context.filings)}")
            logger.info(f"   Violations Identified: {len(context.violations)}")
            logger.info(f"   Criminal Referrals: {len(context.criminal_referrals)}")
            logger.info(f"   Estimated Total Damages: ${sum(v.estimated_damages for v in context.violations):,.2f}")
            logger.info("")
            logger.info("📁 OUTPUT FILES")
            logger.info("-" * 100)
            logger.info(f"   Report Directory: {report_path}")
            logger.info(f"   Main Report: {report_path / 'FORENSIC_REPORT.md'}")
            logger.info(f"   Executive Summary: {report_path / 'executive_summary.md'}")
            logger.info(f"   Machine-Readable: {report_path / 'machine_readable/'}")
            logger.info(f"   Evidence: {report_path / 'evidence/'}")
            logger.info(f"   Appendices: {report_path / 'appendices/'}")
            logger.info("")
            logger.info("=" * 100)
            logger.info(f"🎯 Analysis completed successfully at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("=" * 100)
        else:
            logger.info("")
            logger.info("⚠️  Report generation skipped (--no-report flag)")
        
        return 0
        
    except KeyboardInterrupt:
        logger.warning("\n\n⚠️  Analysis interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"\n\n❌ FATAL ERROR: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
