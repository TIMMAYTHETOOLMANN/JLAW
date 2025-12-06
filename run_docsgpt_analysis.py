"""
JARVIS NEXUS - DocsGPT Integration Quick Start
==============================================

This script provides a quick start guide and automated setup for the
DocsGPT integration with JLAW SEC Forensic System.

Usage:
    python run_docsgpt_analysis.py --setup          # Initial setup
    python run_docsgpt_analysis.py --validate       # Validate configuration
    python run_docsgpt_analysis.py --demo          # Run demo analysis
    python run_docsgpt_analysis.py --file <path>   # Analyze specific file
"""

import os
import sys
from pathlib import Path
import argparse
import logging

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_integration():
    """Run initial setup and validation."""
    logger.info("="*80)
    logger.info("JARVIS NEXUS - DocsGPT Integration Setup")
    logger.info("="*80)
    
    try:
        from src.forensics.docsgpt.init_integration import initialize_docsgpt_integration
        
        logger.info("\nRunning integration validation and setup...")
        results = initialize_docsgpt_integration(validate_only=False)
        
        if results['overall_status'] == 'PASS':
            logger.info("\n✅ Setup completed successfully!")
            logger.info("\nNext steps:")
            logger.info("1. Run validation: python run_docsgpt_analysis.py --validate")
            logger.info("2. Try demo: python run_docsgpt_analysis.py --demo")
            logger.info("3. Analyze a document: python run_docsgpt_analysis.py --file <path>")
            return True
        else:
            logger.warning("\n⚠️  Setup completed with warnings. Review the output above.")
            return False
            
    except Exception as e:
        logger.error(f"❌ Setup failed: {e}", exc_info=True)
        return False


def validate_configuration():
    """Validate the integration configuration."""
    logger.info("="*80)
    logger.info("JARVIS NEXUS - Configuration Validation")
    logger.info("="*80)
    
    try:
        from src.forensics.docsgpt.init_integration import print_integration_status
        
        print_integration_status()
        return True
        
    except Exception as e:
        logger.error(f"❌ Validation failed: {e}", exc_info=True)
        return False


def run_demo_analysis():
    """Run a demonstration analysis on sample data."""
    logger.info("="*80)
    logger.info("JARVIS NEXUS - Demo Analysis")
    logger.info("="*80)
    
    try:
        from src.forensics.docsgpt.document_analysis_orchestrator import (
            DocumentAnalysisOrchestrator,
            AnalysisRequest
        )
        
        # Create a demo text file for analysis
        demo_file = project_root / "forensic_storage" / "demo_analysis.txt"
        demo_file.parent.mkdir(parents=True, exist_ok=True)
        
        demo_content = """
        ITEM 1A. RISK FACTORS
        
        Our business is subject to various risks, including:
        
        1. Market Risk: We are exposed to significant market fluctuations.
           Revenue declined by 15% in the most recent quarter.
        
        2. Credit Risk: Customer defaults may impact our financial position.
           Bad debt expense increased from $2M to $5M year-over-year.
        
        3. Operational Risk: Supply chain disruptions affect production.
        
        ITEM 7. MANAGEMENT'S DISCUSSION AND ANALYSIS
        
        Revenue Performance:
        - Q4 2023: $150M (strong performance)
        - Q1 2024: $140M (slight decline)
        - Q2 2024: $128M (significant decline)
        
        The Company has implemented cost reduction measures to improve margins.
        We expect revenue growth to resume in Q3 2024 based on new contracts.
        
        ITEM 8. FINANCIAL STATEMENTS
        
        Balance Sheet Highlights:
        - Total Assets: $500M
        - Total Liabilities: $450M
        - Stockholders' Equity: $50M
        
        Note: The Company restated prior year financials due to accounting errors.
        """
        
        with open(demo_file, 'w') as f:
            f.write(demo_content)
        
        logger.info(f"\n📄 Created demo document: {demo_file}")
        logger.info("\nAnalyzing demo document...\n")
        
        # Create analysis request
        request = AnalysisRequest(
            document_path=str(demo_file),
            cik="0000000000",  # Demo CIK
            filing_type="10-K",
            extract_contradictions=True,
            extract_fraud_indicators=True,
            generate_report=True
        )
        
        # Run analysis
        orchestrator = DocumentAnalysisOrchestrator()
        result = orchestrator.analyze_document(request)
        
        # Display results
        logger.info("\n" + "="*80)
        logger.info("ANALYSIS RESULTS")
        logger.info("="*80)
        logger.info(f"Status: {result.status}")
        logger.info(f"Risk Score: {result.overall_risk_score:.2f}/100")
        logger.info(f"Fraud Indicators: {len(result.fraud_indicators)}")
        logger.info(f"Contradictions: {len(result.contradictions)}")
        logger.info(f"Document Chunks: {len(result.chunks)}")
        
        if result.fraud_indicators:
            logger.info("\nFraud Indicators Found:")
            for ind in result.fraud_indicators:
                logger.info(f"  - {ind.get('type')}: {ind.get('score'):.2f}")
        
        if result.contradictions:
            logger.info("\nContradictions Found:")
            for contra in result.contradictions[:5]:  # Show first 5
                logger.info(f"  - {contra}")
        
        # Save results
        output_file = project_root / "output" / "demo_analysis_results.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        import json
        with open(output_file, 'w') as f:
            json.dump(result.__dict__, f, indent=2, default=str)
        
        logger.info(f"\n💾 Full results saved to: {output_file}")
        logger.info("\n✅ Demo analysis completed successfully!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Demo analysis failed: {e}", exc_info=True)
        return False


def analyze_file(file_path: str, cik: str = None, filing_type: str = None):
    """Analyze a specific file."""
    logger.info("="*80)
    logger.info(f"JARVIS NEXUS - Analyzing: {Path(file_path).name}")
    logger.info("="*80)
    
    try:
        from src.forensics.docsgpt.document_analysis_orchestrator import (
            DocumentAnalysisOrchestrator,
            AnalysisRequest
        )
        
        # Validate file exists
        if not Path(file_path).exists():
            logger.error(f"❌ File not found: {file_path}")
            return False
        
        # Create analysis request
        request = AnalysisRequest(
            document_path=file_path,
            cik=cik,
            filing_type=filing_type,
            extract_contradictions=True,
            extract_fraud_indicators=True,
            extract_financial_metrics=True,
            cross_reference_filings=bool(cik),
            generate_report=True,
            store_evidence=True
        )
        
        # Run analysis
        orchestrator = DocumentAnalysisOrchestrator()
        result = orchestrator.analyze_document(request)
        
        # Display results
        logger.info("\n" + "="*80)
        logger.info("ANALYSIS RESULTS")
        logger.info("="*80)
        logger.info(f"Document ID: {result.doc_id}")
        logger.info(f"Status: {result.status}")
        logger.info(f"Overall Risk Score: {result.overall_risk_score:.2f}/100")
        logger.info(f"Timestamp: {result.analysis_timestamp}")
        
        logger.info("\nAnalysis Summary:")
        logger.info(f"  - Document Chunks: {len(result.chunks)}")
        logger.info(f"  - Fraud Indicators: {len(result.fraud_indicators)}")
        logger.info(f"  - Contradictions: {len(result.contradictions)}")
        logger.info(f"  - Cross References: {len(result.cross_references)}")
        logger.info(f"  - Evidence Stored: {len(result.evidence_ids)} items")
        
        if result.fraud_indicators:
            logger.info("\n🚨 Fraud Indicators:")
            for ind in result.fraud_indicators:
                severity = ind.get('severity', 'unknown')
                logger.info(f"  [{severity.upper()}] {ind.get('type')}: {ind.get('score', 0):.2f}")
        
        if result.contradictions:
            logger.info("\n⚠️  Contradictions Detected:")
            for i, contra in enumerate(result.contradictions[:10], 1):
                logger.info(f"  {i}. {contra}")
        
        # Save results
        output_dir = project_root / "forensic_reports" / "docsgpt_analysis"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / f"{result.doc_id}_analysis.json"
        
        import json
        with open(output_file, 'w') as f:
            json.dump(result.__dict__, f, indent=2, default=str)
        
        logger.info(f"\n💾 Complete results saved to: {output_file}")
        logger.info("\n✅ Analysis completed successfully!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ File analysis failed: {e}", exc_info=True)
        return False


def analyze_sec_filing(cik: str, filing_type: str, year: int = None):
    """Download and analyze a SEC filing."""
    logger.info("="*80)
    logger.info(f"JARVIS NEXUS - SEC Filing Analysis")
    logger.info(f"CIK: {cik} | Type: {filing_type}")
    logger.info("="*80)
    
    try:
        from src.forensics.sec_edgar_api import SECEdgarAPI
        
        # Initialize SEC API
        api = SECEdgarAPI()
        
        # Fetch filing
        logger.info(f"\n📥 Downloading {filing_type} for CIK {cik}...")
        filing = api.get_latest_filing(cik, filing_type)
        
        if not filing:
            logger.error(f"❌ Could not retrieve filing")
            return False
        
        # Download filing content
        filing_path = project_root / "forensic_storage" / "temp" / f"{cik}_{filing_type}.html"
        filing_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save filing content
        with open(filing_path, 'w', encoding='utf-8') as f:
            f.write(filing.get('content', ''))
        
        logger.info(f"✓ Filing downloaded: {filing_path}")
        
        # Analyze the filing
        return analyze_file(str(filing_path), cik=cik, filing_type=filing_type)
        
    except Exception as e:
        logger.error(f"❌ SEC filing analysis failed: {e}", exc_info=True)
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="JARVIS NEXUS - DocsGPT Integration Analysis System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Initial setup
  python run_docsgpt_analysis.py --setup
  
  # Validate configuration
  python run_docsgpt_analysis.py --validate
  
  # Run demo
  python run_docsgpt_analysis.py --demo
  
  # Analyze local file
  python run_docsgpt_analysis.py --file path/to/document.pdf --cik 0001318605
  
  # Analyze SEC filing
  python run_docsgpt_analysis.py --sec-filing --cik 0001318605 --type 10-K
        """
    )
    
    parser.add_argument('--setup', action='store_true',
                       help='Run initial setup and validation')
    parser.add_argument('--validate', action='store_true',
                       help='Validate integration configuration')
    parser.add_argument('--demo', action='store_true',
                       help='Run demo analysis on sample data')
    parser.add_argument('--file', type=str,
                       help='Path to file to analyze')
    parser.add_argument('--sec-filing', action='store_true',
                       help='Download and analyze SEC filing')
    parser.add_argument('--cik', type=str,
                       help='Company CIK number')
    parser.add_argument('--type', type=str,
                       help='SEC filing type (10-K, 10-Q, 8-K, etc.)')
    parser.add_argument('--year', type=int,
                       help='Filing year (optional)')
    
    args = parser.parse_args()
    
    # Execute requested action
    if args.setup:
        success = setup_integration()
    elif args.validate:
        success = validate_configuration()
    elif args.demo:
        success = run_demo_analysis()
    elif args.file:
        success = analyze_file(args.file, cik=args.cik, filing_type=args.type)
    elif args.sec_filing:
        if not args.cik or not args.type:
            logger.error("❌ --cik and --type are required for SEC filing analysis")
            success = False
        else:
            success = analyze_sec_filing(args.cik, args.type, args.year)
    else:
        parser.print_help()
        success = False
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

