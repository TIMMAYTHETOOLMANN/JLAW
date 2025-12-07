#!/usr/bin/env python3
"""
JLAW ULTIMATE FORENSIC ANALYSIS SYSTEM
=======================================
Version: 10.0.0-ULTIMATE
Date: December 2025

Full 13-Phase Deep Forensic Analysis integrating ALL modules from the
UNIFIED_FORENSIC_SYSTEM_README.md specification.

PHASES IMPLEMENTED:
1.  Document Acquisition (SEC EDGAR API)
2.  DocsGPT Document Parsing (Semantic chunking)
3.  Agent-Powered Scraping (OpenAI/Anthropic agents)
4.  Quantitative Forensics (Benford's Law, Beneish M-Score, Altman Z-Score)
5.  Revenue Recognition Analysis (DSO trends, hockey stick patterns)
6.  Financial Flow Analysis (Circular flows, enrichment schemes)
7.  Linguistic Deception Analysis (Hedging, obfuscation, certainty)
8.  Temporal Analysis (Timeline anomalies, filing delays)
9.  Contradiction Detection (Cross-document inconsistencies)
10. ML Fraud Detection (BERT/XGBoost ensemble)
11. Statutory Mapping (15 USC/17 CFR with GovInfo)
12. Dual-Agent Prosecution (OpenAI + Anthropic validation)
13. Report Generation (Full DOJ-grade output stack)
"""

import asyncio
import sys
import os
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load environment
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            f'ultimate_forensic_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log',
            encoding='utf-8'
        )
    ]
)
logger = logging.getLogger(__name__)

# Import all forensic modules
from src.forensics.unified_forensic_pipeline import UnifiedForensicPipeline
from src.forensics.unified_report_generator import UnifiedReportGenerator
from src.forensics.forensic_context import ForensicContext


class UltimateForensicAnalyzer:
    """
    Ultimate forensic analyzer that executes the complete 13-phase pipeline
    using ALL available forensic modules.
    """
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    async def analyze(
        self,
        ticker: str = None,
        cik: str = None,
        year: int = None,
        start_date: str = None,
        end_date: str = None,
        verbose: bool = False
    ):
        """
        Execute the complete 13-phase forensic analysis pipeline.
        
        Args:
            ticker: Company ticker symbol (e.g., 'NKE')
            cik: Company CIK number (e.g., '0000320187')
            year: Analysis year (e.g., 2019)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            verbose: Enable verbose logging
        """
        
        if verbose:
            logging.getLogger().setLevel(logging.DEBUG)
            
        # Validate inputs
        if not ticker and not cik:
            raise ValueError("Must provide either --ticker or --cik")
            
        if not year and not (start_date and end_date):
            raise ValueError("Must provide --year or both --start-date and --end-date")
            
        # Set date range
        if year:
            start_date = f"{year}-01-01"
            end_date = f"{year}-12-31"
            
        logger.info("=" * 100)
        logger.info("🔬 JLAW ULTIMATE FORENSIC ANALYSIS SYSTEM v10.0")
        logger.info("=" * 100)
        logger.info(f"Target: {ticker or cik}")
        logger.info(f"Period: {start_date} to {end_date}")
        logger.info(f"Output: {self.output_dir}")
        logger.info("=" * 100)
        
        # Initialize the unified forensic pipeline
        logger.info("\n🚀 Initializing Unified Forensic Pipeline...")
        pipeline = UnifiedForensicPipeline()
        
        # Execute the complete 13-phase analysis
        logger.info("\n📊 Executing 13-Phase Forensic Analysis Pipeline...\n")
        
        try:
            context = await pipeline.execute(
                ticker=ticker,
                cik=cik,
                start_date=start_date,
                end_date=end_date
            )
            
            # Generate comprehensive report
            logger.info("\n📝 Generating Comprehensive Report Package...\n")
            report_generator = UnifiedReportGenerator()
            report_path = report_generator.generate_report(
                context=context,
                output_dir=self.output_dir
            )
            
            # Display summary
            self._display_summary(context, report_path)
            
            return context
            
        except Exception as e:
            logger.error(f"❌ Analysis failed: {e}", exc_info=True)
            raise
            
    def _display_summary(self, context: ForensicContext, report_path: Path):
        """Display analysis summary."""
        logger.info("\n" + "=" * 100)
        logger.info("✅ ANALYSIS COMPLETE")
        logger.info("=" * 100)
        
        logger.info(f"\n📊 SUMMARY STATISTICS:")
        logger.info(f"   Company: {context.company_name}")
        logger.info(f"   CIK: {context.cik}")
        logger.info(f"   Period: {context.analysis_period_start} to {context.analysis_period_end}")
        logger.info(f"   Filings Analyzed: {len(context.filings)}")
        logger.info(f"   Violations Found: {len(context.violations)}")
        
        # Violations by type
        if context.violations:
            violation_types = {}
            for v in context.violations:
                vtype = v.violation_type
                violation_types[vtype] = violation_types.get(vtype, 0) + 1
                
            logger.info(f"\n📋 VIOLATIONS BY TYPE:")
            for vtype, count in sorted(violation_types.items(), key=lambda x: -x[1]):
                logger.info(f"   {vtype}: {count}")
                
            # Violations by severity
            violation_severity = {}
            for v in context.violations:
                severity = v.severity
                violation_severity[severity] = violation_severity.get(severity, 0) + 1
                
            logger.info(f"\n⚠️  VIOLATIONS BY SEVERITY:")
            for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
                count = violation_severity.get(severity, 0)
                if count > 0:
                    logger.info(f"   {severity}: {count}")
                    
            # Criminal referrals
            criminal_referrals = sum(1 for v in context.violations if v.criminal_referral)
            if criminal_referrals > 0:
                logger.info(f"\n⚖️  CRIMINAL REFERRALS: {criminal_referrals}")
                
            # Estimated damages
            total_damages = sum(v.estimated_damages for v in context.violations)
            logger.info(f"\n💰 ESTIMATED DAMAGES: ${total_damages:,.2f}")
            
        # Analysis metrics
        logger.info(f"\n🔍 ANALYSIS DEPTH:")
        logger.info(f"   Parsed Documents: {len(context.parsed_documents)}")
        logger.info(f"   Document Chunks: {len(context.chunks)}")
        logger.info(f"   Timeline Anomalies: {len(context.timeline_anomalies)}")
        logger.info(f"   Contradictions: {len(context.contradictions)}")
        
        # Quantitative scores
        if context.fraud_probability > 0:
            logger.info(f"\n📈 QUANTITATIVE FORENSICS:")
            logger.info(f"   Fraud Probability: {context.fraud_probability:.2%}")
            if context.beneish_score:
                logger.info(f"   Beneish M-Score: {context.beneish_score:.2f}")
            if context.altman_z_score:
                logger.info(f"   Altman Z-Score: {context.altman_z_score:.2f}")
                
        # ML scores
        if context.ml_fraud_scores:
            logger.info(f"\n🤖 ML FRAUD DETECTION:")
            if 'ensemble_score' in context.ml_fraud_scores:
                logger.info(f"   Ensemble Score: {context.ml_fraud_scores['ensemble_score']:.2%}")
            if 'bert_score' in context.ml_fraud_scores:
                logger.info(f"   BERT Score: {context.ml_fraud_scores['bert_score']:.2%}")
            if 'xgboost_score' in context.ml_fraud_scores:
                logger.info(f"   XGBoost Score: {context.ml_fraud_scores['xgboost_score']:.2%}")
                
        # Linguistic analysis
        if context.deception_metrics:
            logger.info(f"\n🗣️  LINGUISTIC DECEPTION:")
            for key, value in context.deception_metrics.items():
                if isinstance(value, (int, float)):
                    logger.info(f"   {key.replace('_', ' ').title()}: {value:.2f}")
                    
        # Output files
        logger.info(f"\n📁 OUTPUT FILES:")
        logger.info(f"   Report Directory: {report_path.parent}")
        logger.info(f"   Main Report: {report_path}")
        logger.info(f"   Machine-Readable: {report_path.parent / 'machine_readable'}")
        logger.info(f"   Evidence: {report_path.parent / 'evidence'}")
        logger.info(f"   Appendices: {report_path.parent / 'appendices'}")
        
        logger.info("\n" + "=" * 100)
        logger.info(f"🎯 Analysis completed successfully at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 100 + "\n")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="JLAW Ultimate Forensic Analysis System - Complete 13-Phase Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze Nike 2019 with full 13-phase pipeline
  python jlaw_ultimate_forensic.py --ticker NKE --year 2019
  
  # Analyze by CIK with verbose logging
  python jlaw_ultimate_forensic.py --cik 0000320187 --year 2019 --verbose
  
  # Custom date range
  python jlaw_ultimate_forensic.py --ticker NKE --start-date 2019-01-01 --end-date 2019-12-31

13-PHASE PIPELINE:
  Phase 1:  Document Acquisition (SEC EDGAR API)
  Phase 2:  DocsGPT Document Parsing (Semantic chunking)
  Phase 3:  Agent-Powered Scraping (OpenAI/Anthropic agents)
  Phase 4:  Quantitative Forensics (Benford, Beneish, Altman)
  Phase 5:  Revenue Recognition (DSO trends, hockey stick)
  Phase 6:  Financial Flow Analysis (Circular flows, schemes)
  Phase 7:  Linguistic Deception (Hedging, obfuscation)
  Phase 8:  Temporal Analysis (Timeline anomalies, delays)
  Phase 9:  Contradiction Detection (Cross-doc inconsistencies)
  Phase 10: ML Fraud Detection (BERT/XGBoost ensemble)
  Phase 11: Statutory Mapping (15 USC/17 CFR + GovInfo)
  Phase 12: Dual-Agent Prosecution (OpenAI + Anthropic)
  Phase 13: Report Generation (DOJ-grade output)
        """
    )
    
    parser.add_argument('--ticker', type=str, help='Company ticker symbol (e.g., NKE)')
    parser.add_argument('--cik', type=str, help='Company CIK number (e.g., 0000320187)')
    parser.add_argument('--year', type=int, help='Analysis year (e.g., 2019)')
    parser.add_argument('--start-date', type=str, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, help='End date (YYYY-MM-DD)')
    parser.add_argument('--output-dir', type=str, default='output', help='Output directory (default: output/)')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    return parser.parse_args()


async def main():
    """Main entry point."""
    args = parse_args()
    
    try:
        analyzer = UltimateForensicAnalyzer(output_dir=args.output_dir)
        
        await analyzer.analyze(
            ticker=args.ticker,
            cik=args.cik,
            year=args.year,
            start_date=args.start_date,
            end_date=args.end_date,
            verbose=args.verbose
        )
        
        print("\n✅ Ultimate forensic analysis completed successfully!")
        sys.exit(0)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Analysis interrupted by user")
        sys.exit(130)
        
    except Exception as e:
        print(f"\n\n❌ Analysis failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

