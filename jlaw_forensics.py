"""
JLAW Comprehensive Forensic Analysis System
============================================

Command-line interface for comprehensive SEC forensic analysis
Uses ForensicOrchestrator with all enhancement modules

Usage:
    python jlaw_forensics.py --company "Nike Inc." --cik 0000320187 --start-date 2019-01-01 --end-date 2019-12-31
"""

import asyncio
import logging
import sys
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# Import the comprehensive forensic orchestration system
from src.forensics.forensic_orchestrator import ForensicOrchestrator, InvestigationStatus
from src.forensics.config_manager import ConfigurationManager
from src.forensics.immutable_storage import StorageConfig

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'jlaw_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ComprehensiveForensicCLI:
    """
    Command-line interface for comprehensive forensic analysis
    Leverages ForensicOrchestrator with all 9 enhancement protocol phases
    """
    
    def __init__(self, company_name: str, cik: str, start_date: str, end_date: str):
        self.company_name = company_name
        self.cik = cik.strip().zfill(10)
        self.start_date = start_date
        self.end_date = end_date
        
        # Initialize configuration
        self.config_mgr = ConfigurationManager()
        self.config = self.config_mgr.config
        
        # Get API keys from config
        govinfo_api_key = self.config.govinfo.api_key if hasattr(self.config, 'govinfo') else 'DEMO_KEY'
        
        # Initialize storage config
        storage_provider = getattr(self.config, 'storage_provider', 'LOCAL')
        storage_config = StorageConfig(provider=storage_provider)
        
        # Initialize ForensicOrchestrator
        self.orchestrator = ForensicOrchestrator(
            govinfo_api_key=govinfo_api_key,
            storage_config=storage_config,
            audit_signing_key=b"jlaw_forensics_cli_2025",
            user_agent=f"JLAW-Forensics-CLI/{company_name}"
        )
    
    async def run_analysis(self) -> Dict[str, Any]:
        """Execute comprehensive forensic analysis"""
        
        print("="*120)
        print(f"JLAW COMPREHENSIVE FORENSIC ANALYSIS SYSTEM")
        print("="*120)
        print(f"Company: {self.company_name}")
        print(f"CIK: {self.cik}")
        print(f"Analysis Period: {self.start_date} to {self.end_date}")
        print("="*120)
        print()
        
        start_time = datetime.now()
        
        try:
            # Create forensic case
            print("[PHASE 1] Creating forensic case...")
            case = await self.orchestrator.create_case(
                target=self.company_name,
                case_type="comprehensive_sec_analysis",
                metadata={
                    'cik': self.cik,
                    'start_date': self.start_date,
                    'end_date': self.end_date,
                    'initiated_by': 'JLAW_CLI',
                    'analysis_mode': 'comprehensive'
                }
            )
            print(f"[OK] Case created: {case.case_id}")
            print()
            
            # Run comprehensive investigation
            print("[PHASE 2-8] Executing comprehensive multi-phase investigation...")
            print()
            print("Enhancement Protocol Phases:")
            print("  [1] Advanced Document Parsing")
            print("  [2] Omniscient Intelligence Gathering")
            print("  [3] Legal Statute Correlation")
            print("  [4] Temporal Analysis & Timeline Reconstruction")
            print("  [5] Decision Engine & Prosecution Path Builder")
            print("  [6] Advanced Contradiction Detection")
            print("  [7] Comprehensive Reporting Engine")
            print("  [8] Master Orchestration")
            print("  [9] Health Check & Validation")
            print()
            print("This will take 10-20 minutes depending on filing count...")
            print()
            
            # Run investigation
            result = await self.orchestrator.run_investigation(
                case_id=case.case_id,
                filing_types=None,  # ALL filing types
                start_year=int(self.start_date[:4]),
                end_year=int(self.end_date[:4])
            )
            
            duration = (datetime.now() - start_time).total_seconds()
            
            # Display results
            print()
            print("="*120)
            print(f"ANALYSIS COMPLETE")
            print("="*120)
            print(f"Duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")
            print(f"Case ID: {case.case_id}")
            print()
            
            # Get case details
            case_details = await self.orchestrator.get_case(case.case_id)
            if case_details:
                print("Results:")
                print(f"  Status: {case_details.status.value}")
                print(f"  Filings Analyzed: {case_details.metadata.get('filings_analyzed', 'N/A')}")
                print(f"  Violations Found: {case_details.metadata.get('violations_found', 'N/A')}")
                
                report_path = case_details.metadata.get('report_path')
                if report_path:
                    print(f"  Report: {report_path}")
                
                evidence_path = case_details.metadata.get('evidence_path')
                if evidence_path:
                    print(f"  Evidence: {evidence_path}")
            
            print()
            print("="*120)
            
            return {
                'status': 'SUCCESS',
                'case_id': case.case_id,
                'duration_seconds': duration,
                'result': result
            }
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}", exc_info=True)
            print()
            print(f"[ERROR] Analysis failed: {e}")
            print()
            return {
                'status': 'FAILED',
                'error': str(e)
            }


async def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="JLAW Comprehensive Forensic Analysis System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze Nike 2019 filings
  python jlaw_forensics.py --company "Nike Inc." --cik 0000320187 --start-date 2019-01-01 --end-date 2019-12-31
  
  # Analyze Apple 2020 Q1
  python jlaw_forensics.py --company "Apple Inc." --cik 0000320193 --start-date 2020-01-01 --end-date 2020-03-31
        """
    )
    
    parser.add_argument('--company', required=True, help='Company name (e.g., "Nike Inc.")')
    parser.add_argument('--cik', required=True, help='Company CIK number (e.g., 0000320187)')
    parser.add_argument('--start-date', required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', required=True, help='End date (YYYY-MM-DD)')
    
    args = parser.parse_args()
    
    # Run analysis
    cli = ComprehensiveForensicCLI(
        company_name=args.company,
        cik=args.cik,
        start_date=args.start_date,
        end_date=args.end_date
    )
    
    result = await cli.run_analysis()
    
    sys.exit(0 if result['status'] == 'SUCCESS' else 1)


if __name__ == "__main__":
    asyncio.run(main())

