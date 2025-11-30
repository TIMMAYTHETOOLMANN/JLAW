#!/usr/bin/env python3
"""
DOJ Comprehensive Case File Generator
====================================

Executive-level orchestrator that generates complete Department of Justice
case files with federal prosecution standards, evidence integrity, and
comprehensive documentation scaffolding.

This script executes the full DOJ case orchestration workflow:
1. Case initiation with proper federal protocols
2. Comprehensive forensic investigation
3. Evidence transformation to federal standards
4. Prosecutorial decision support
5. Complete case documentation package

Usage:
    python doj_comprehensive_orchestrator.py --target-company "Nike Inc." --target-cik "0000320187"
"""

import asyncio
import argparse
import logging
import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Core imports
from src.forensics.doj_case_orchestrator import (
    DOJCaseOrchestrator, 
    create_doj_case_orchestrator,
    CaseClassification
)
from src.forensics.unified_orchestrator import UnifiedForensicOrchestrator
from src.forensics.immutable_storage import StorageConfig
from src.forensics.config_manager import get_config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'doj_orchestrator_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)

logger = logging.getLogger("DOJOrchestrator")


class DOJCaseExecutor:
    """Executive-level DOJ case file executor."""
    
    def __init__(self):
        self.config = None
        self.doj_orchestrator = None
        self.execution_start = datetime.now(timezone.utc)
        
    async def initialize(self) -> None:
        """Initialize DOJ orchestrator with proper configuration."""
        
        logger.info("🏛️ Initializing Department of Justice Case Orchestrator")
        
        # Load configuration
        try:
            self.config = get_config()
            logger.info("✅ Configuration loaded successfully")
        except Exception as e:
            logger.error(f"❌ Configuration load failed: {e}")
            raise
            
        # Validate required credentials
        if not self.config.config.govinfo.api_key:
            raise ValueError("GovInfo API key required for statute integration")
            
        # Setup storage configuration
        storage_config = StorageConfig(
            base_path=Path("forensic_storage") / "doj_cases",
            encryption_enabled=True,
            compression_enabled=True,
            integrity_checking=True
        )
        
        # Generate audit signing key (in production, this would be from secure storage)
        audit_key = os.urandom(32)
        
        # Create DOJ orchestrator
        try:
            self.doj_orchestrator = await create_doj_case_orchestrator(
                govinfo_api_key=self.config.config.govinfo.api_key,
                storage_config=storage_config,
                audit_signing_key=audit_key,
                prosecution_unit="Securities and Financial Crimes Unit",
                district="U.S. Department of Justice - Main Justice"
            )
            logger.info("✅ DOJ Case Orchestrator initialized")
        except Exception as e:
            logger.error(f"❌ DOJ orchestrator initialization failed: {e}")
            raise
            
    async def execute_comprehensive_case(
        self,
        target_company: str,
        target_cik: str,
        investigation_year: int = 2019,
        case_classification: CaseClassification = CaseClassification.SECURITIES_VIOLATION
    ) -> Path:
        """Execute comprehensive DOJ case file generation."""
        
        logger.info(f"⚖️ Executing comprehensive DOJ case for {target_company} (CIK: {target_cik})")
        
        execution_summary = {
            "target_company": target_company,
            "target_cik": target_cik,
            "investigation_year": investigation_year,
            "case_classification": case_classification.value,
            "execution_start": self.execution_start.isoformat(),
            "phases_completed": []
        }
        
        try:
            # Phase 1: Case Initiation
            logger.info("📋 Phase 1: Federal Case Initiation")
            
            investigation_scope = {
                "start_year": investigation_year,
                "end_year": investigation_year,
                "analysis_depth": "comprehensive",
                "evidence_standards": "federal_prosecution",
                "documentation_level": "doj_complete"
            }
            
            case_file = await self.doj_orchestrator.initiate_federal_case(
                target_company=target_company,
                target_cik=target_cik,
                case_classification=case_classification,
                investigation_scope=investigation_scope
            )
            
            execution_summary["case_number"] = case_file.case_number
            execution_summary["case_title"] = case_file.case_title
            execution_summary["phases_completed"].append("case_initiation")
            
            logger.info(f"✅ Federal case initiated: {case_file.case_number}")
            
            # Phase 2: Comprehensive Investigation
            logger.info("🔍 Phase 2: Comprehensive Forensic Investigation")
            
            case_file = await self.doj_orchestrator.execute_comprehensive_investigation(
                case_number=case_file.case_number,
                target_year=investigation_year
            )
            
            execution_summary["phases_completed"].append("comprehensive_investigation")
            
            # Extract investigation results
            if case_file.forensic_analysis:
                execution_summary["investigation_results"] = {
                    "filings_analyzed": len(case_file.forensic_analysis.filings_analyzed),
                    "violations_detected": len(case_file.forensic_analysis.violations_detected),
                    "risk_score": case_file.forensic_analysis.risk_score,
                    "total_estimated_damages": sum(
                        v.estimated_fine for v in case_file.forensic_analysis.violations_detected
                    )
                }
                
            logger.info(f"✅ Investigation complete - {len(case_file.evidence_catalog)} evidence items cataloged")
            
            # Phase 3: DOJ Case Package Generation
            logger.info("📑 Phase 3: DOJ Case Package Generation")
            
            output_directory = Path("forensic_reports") / "doj_cases"
            output_directory.mkdir(parents=True, exist_ok=True)
            
            package_path = await self.doj_orchestrator.generate_doj_case_package(
                case_number=case_file.case_number,
                output_directory=output_directory
            )
            
            execution_summary["phases_completed"].append("package_generation")
            execution_summary["package_path"] = str(package_path)
            execution_summary["execution_complete"] = datetime.now(timezone.utc).isoformat()
            
            logger.info(f"✅ DOJ case package generated: {package_path}")
            
            # Phase 4: Execution Summary Report
            await self._generate_execution_summary(execution_summary, output_directory)
            
            logger.info("🏛️ DOJ Comprehensive Case File Generation Complete")
            logger.info(f"📦 Package Location: {package_path}")
            logger.info(f"📊 Evidence Items: {len(case_file.evidence_catalog)}")
            
            if case_file.prosecution_memo:
                logger.info(f"⚖️ Prosecution Recommendation: {case_file.prosecution_memo.recommendation.recommendation.value}")
                logger.info(f"📈 Case Strength: {case_file.prosecution_memo.case_strength:.2f}")
                
            return package_path
            
        except Exception as e:
            logger.error(f"❌ DOJ case execution failed: {e}")
            execution_summary["execution_failed"] = datetime.now(timezone.utc).isoformat()
            execution_summary["error"] = str(e)
            await self._generate_execution_summary(execution_summary, Path("forensic_reports") / "doj_cases")
            raise
            
    async def _generate_execution_summary(
        self,
        summary: Dict[str, Any],
        output_directory: Path
    ) -> None:
        """Generate execution summary report."""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_path = output_directory / f"DOJ_EXECUTION_SUMMARY_{timestamp}.json"
        
        # Write JSON summary
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, default=str)
            
        # Write human-readable summary
        readable_path = output_directory / f"DOJ_EXECUTION_REPORT_{timestamp}.txt"
        
        with open(readable_path, 'w', encoding='utf-8') as f:
            f.write(f"""
DEPARTMENT OF JUSTICE
CASE EXECUTION SUMMARY
=====================

Execution Date: {datetime.now().strftime('%B %d, %Y')}
System: JLAW Enhanced Forensics Platform

CASE INFORMATION
===============
Target Company: {summary.get('target_company', 'Unknown')}
SEC CIK: {summary.get('target_cik', 'Unknown')}
Case Number: {summary.get('case_number', 'Not assigned')}
Case Title: {summary.get('case_title', 'Not assigned')}
Classification: {summary.get('case_classification', 'Unknown')}

EXECUTION TIMELINE
=================
Start Time: {summary.get('execution_start', 'Unknown')}
Completion: {summary.get('execution_complete', 'In progress')}

PHASES COMPLETED
===============
""")
            
            for phase in summary.get('phases_completed', []):
                f.write(f"✅ {phase.upper().replace('_', ' ')}\n")
                
            if 'investigation_results' in summary:
                results = summary['investigation_results']
                f.write(f"""

INVESTIGATION RESULTS
====================
Filings Analyzed: {results.get('filings_analyzed', 0)}
Violations Detected: {results.get('violations_detected', 0)}
Risk Score: {results.get('risk_score', 0.0):.2f}
Estimated Damages: ${results.get('total_estimated_damages', 0):,.2f}
""")
                
            if 'package_path' in summary:
                f.write(f"""

DELIVERABLES
===========
DOJ Case Package: {summary['package_path']}
Execution Summary: {summary_path.name}
""")
                
            if 'error' in summary:
                f.write(f"""

EXECUTION ERROR
==============
Error: {summary['error']}
Failed At: {summary.get('execution_failed', 'Unknown')}
""")
                
        logger.info(f"📊 Execution summary generated: {readable_path}")


async def main():
    """Main execution function."""
    
    parser = argparse.ArgumentParser(
        description="DOJ Comprehensive Case File Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--target-company",
        required=True,
        help="Target company name (e.g., 'Nike Inc.')"
    )
    
    parser.add_argument(
        "--target-cik", 
        required=True,
        help="SEC Central Index Key (e.g., '0000320187')"
    )
    
    parser.add_argument(
        "--investigation-year",
        type=int,
        default=2019,
        help="Investigation target year (default: 2019)"
    )
    
    parser.add_argument(
        "--case-classification",
        choices=[c.value for c in CaseClassification],
        default=CaseClassification.SECURITIES_VIOLATION.value,
        help="Case classification type"
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize executor
        executor = DOJCaseExecutor()
        await executor.initialize()
        
        # Execute comprehensive case
        case_classification = CaseClassification(args.case_classification)
        
        package_path = await executor.execute_comprehensive_case(
            target_company=args.target_company,
            target_cik=args.target_cik,
            investigation_year=args.investigation_year,
            case_classification=case_classification
        )
        
        print(f"\n🏛️ DOJ CASE FILE GENERATION COMPLETE")
        print(f"📦 Package: {package_path}")
        print(f"🎯 Target: {args.target_company} (CIK: {args.target_cik})")
        print(f"📅 Year: {args.investigation_year}")
        print(f"⚖️ Classification: {case_classification.value}")
        
    except KeyboardInterrupt:
        logger.info("🛑 Execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
