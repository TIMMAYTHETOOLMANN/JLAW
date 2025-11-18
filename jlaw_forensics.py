"""
JLAW Forensic System - Main Entry Point
Zero-tolerance forensic analysis for SEC filings with surgical precision.
"""

import asyncio
import os
import sys
from typing import Dict, Any, Optional, List
import argparse
import json
import logging
from datetime import datetime, timezone

from src.forensics import (
    ForensicOrchestrator,
    AdvancedFraudDetector,
    StorageConfig,
    InvestigationStatus
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'forensic_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class JLAWForensicSystem:
    """
    Main system controller for JLAW forensic analysis.
    Implements complete zero-tolerance architecture.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize JLAW system with configuration."""
        self.config = self._load_config(config_path)
        self.orchestrator = None
        self.fraud_detector = None
        self._initialize_components()
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load system configuration."""
        default_config = {
            "storage_provider": os.getenv("STORAGE_PROVIDER", "LOCAL"),
            "govinfo_api_key": os.getenv("GOVINFO_API_KEY", "DEMO_KEY"),
            "sec_user_agent": os.getenv("SEC_USER_AGENT", "JLAW forensics@jlaw.com"),
            "audit_signing_key": os.getenv("AUDIT_SIGNING_KEY", b"default_signing_key"),
            "aws_region": os.getenv("AWS_REGION", "us-east-1"),
            "forensic_s3_bucket": os.getenv("FORENSIC_S3_BUCKET", "jlaw-forensic-evidence"),
            "retention_days": int(os.getenv("RETENTION_DAYS", "2555")),
            "rate_limits": {
                "sec_edgar": 7,  # Effective rate for medium volume
                "govinfo": 1000  # Per hour
            },
            "ml_models": {
                "enable_bert": True,
                "enable_isolation_forest": True,
                "ensemble_weights": {
                    "han": 0.4,
                    "isolation_forest": 0.3,
                    "random_forest": 0.3
                }
            },
            "forensic_thresholds": {
                "high_risk": 0.7,
                "critical_risk": 0.85,
                "auto_escalate": 0.8
            }
        }
        
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        
        return default_config
    
    def _initialize_components(self):
        """Initialize all forensic components."""
        logger.info("Initializing JLAW Forensic System...")
        
        # Initialize storage config
        storage_config = StorageConfig(
            provider=self.config["storage_provider"],
            retention_days=self.config["retention_days"],
            compliance_mode=True,
            redundancy_level=3,
            compression=True
        )
        
        # Initialize orchestrator
        self.orchestrator = ForensicOrchestrator(
            govinfo_api_key=self.config["govinfo_api_key"],
            storage_config=storage_config,
            audit_signing_key=self.config["audit_signing_key"].encode() 
                if isinstance(self.config["audit_signing_key"], str) 
                else self.config["audit_signing_key"]
        )
        
        # Initialize ML fraud detector
        self.fraud_detector = AdvancedFraudDetector()
        
        logger.info("JLAW system initialized successfully")
        logger.info(f"Storage provider: {self.config['storage_provider']}")
        logger.info(f"Retention period: {self.config['retention_days']} days")
    
    async def investigate_company(
        self,
        cik: str,
        company_name: str,
        years_back: int = 3,
        filing_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Launch full forensic investigation of company.
        
        Args:
            cik: Company CIK
            company_name: Company name
            years_back: Years of history to analyze
            filing_types: Specific filing types to analyze
            
        Returns:
            Investigation results
        """
        logger.info(f"Starting investigation: {company_name} (CIK: {cik})")
        
        if not filing_types:
            filing_types = ["10-K", "10-Q"]
        
        # Initiate investigation
        case_id = await self.orchestrator.initiate_investigation(
            cik=cik,
            company_name=company_name,
            investigator="JLAW_CLI",
            case_notes=f"Automated investigation: {years_back} years analysis"
        )
        
        logger.info(f"Investigation initiated: Case ID {case_id}")
        
        # Run full investigation
        try:
            report = await self.orchestrator.run_full_investigation(
                case_id=case_id,
                filing_types=filing_types,
                years=years_back
            )
            
            logger.info(f"Investigation complete: {case_id}")
            
            # Add summary statistics
            report["cli_summary"] = {
                "case_id": case_id,
                "company": company_name,
                "cik": cik,
                "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
                "years_analyzed": years_back,
                "filing_types": filing_types
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Investigation failed: {e}", exc_info=True)
            await self.orchestrator.emergency_halt(
                case_id=case_id,
                reason=f"Investigation error: {str(e)}"
            )
            raise
    
    async def analyze_single_filing(
        self,
        cik: str,
        accession: str,
        filing_type: str = "10-K"
    ) -> Dict[str, Any]:
        """
        Analyze single filing for fraud indicators.
        
        Args:
            cik: Company CIK
            accession: SEC accession number
            filing_type: Type of filing
            
        Returns:
            Analysis results
        """
        logger.info(f"Analyzing filing: {accession}")
        
        # SEC analysis
        filing_analysis = await self.orchestrator.sec_analyzer.analyze_filing(
            cik, accession, filing_type
        )
        
        # ML fraud detection
        fraud_prediction = await self.fraud_detector.detect_fraud({
            "cik": cik,
            "accession": accession,
            "filing_type": filing_type,
            "financials": {},  # Would be populated from filing
            "mda": "",  # Would be extracted from filing
            "delay_days": filing_analysis.delay_days
        })
        
        # Statute mapping
        violations = await self.orchestrator.statute_mapper.map_violations({
            "red_flags": filing_analysis.red_flags,
            "fraud_indicators": filing_analysis.fraud_indicators,
            "revenue_anomalies": filing_analysis.revenue_anomalies
        })
        
        results = {
            "filing": {
                "cik": cik,
                "accession": accession,
                "type": filing_type
            },
            "forensic_analysis": {
                "risk_score": filing_analysis.fraud_indicators.get("overall_risk", 0),
                "red_flags": len(filing_analysis.red_flags),
                "delay_days": filing_analysis.delay_days,
                "benford_suspicious": filing_analysis.benford_analysis.get("suspicious", False),
                "revenue_anomalies": len(filing_analysis.revenue_anomalies)
            },
            "ml_prediction": {
                "fraud_probability": fraud_prediction.probability,
                "confidence": fraud_prediction.confidence,
                "red_flag_sentences": fraud_prediction.red_flag_sentences,
                "top_features": dict(list(fraud_prediction.features_importance.items())[:5])
            },
            "legal_violations": [
                {
                    "statute": f"{v.title} USC {v.section}",
                    "severity": v.severity,
                    "description": v.description,
                    "confidence": v.detection_confidence
                }
                for v in violations
            ],
            "summary": {
                "combined_risk": (
                    filing_analysis.fraud_indicators.get("overall_risk", 0) * 0.4 +
                    fraud_prediction.probability * 0.6
                ),
                "criminal_violations": sum(1 for v in violations if v.severity == "CRIMINAL"),
                "high_risk": filing_analysis.fraud_indicators.get("overall_risk", 0) > 0.7
            }
        }
        
        logger.info(
            f"Analysis complete - Traditional Risk: {results['forensic_analysis']['risk_score']:.2%}, "
            f"ML Prediction: {fraud_prediction.probability:.2%}"
        )
        
        return results
    
    async def verify_system_integrity(self) -> Dict[str, Any]:
        """
        Verify complete system integrity.
        
        Returns:
            Integrity verification results
        """
        logger.info("Running system integrity verification...")
        
        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "components": {}
        }
        
        # Verify hash chains
        chains_to_verify = [
            ("master", self.orchestrator.master_chain),
            ("sec_forensics", self.orchestrator.sec_analyzer.hash_chain),
            ("statute_mapping", self.orchestrator.statute_mapper.hash_chain),
            ("ml_detector", self.fraud_detector.hash_chain),
            ("storage", self.orchestrator.storage.hash_chain)
        ]
        
        for name, chain in chains_to_verify:
            is_valid = await chain.verify_chain()
            results["components"][name] = {
                "valid": is_valid,
                "blocks": len(chain.blocks),
                "last_hash": chain.blocks[-1].current_hash if chain.blocks else None
            }
            
            if not is_valid:
                logger.critical(f"INTEGRITY VIOLATION: {name} chain compromised!")
        
        # Verify audit log
        audit_valid = await self.orchestrator.audit_log.verify()
        results["components"]["audit_log"] = {
            "valid": audit_valid,
            "entries": len(self.orchestrator.audit_log.entries)
        }
        
        # Verify stored evidence
        storage_results = await self.orchestrator.storage.verify_all_evidence()
        results["components"]["storage_verification"] = storage_results
        
        # Overall system status
        all_valid = all(
            comp.get("valid", False) 
            for comp in results["components"].values()
            if isinstance(comp, dict) and "valid" in comp
        )
        
        results["system_integrity"] = "VALID" if all_valid else "COMPROMISED"
        
        if not all_valid:
            logger.critical("SYSTEM INTEGRITY COMPROMISED - HALT OPERATIONS")
            await self.orchestrator.audit_log.append(
                event="INTEGRITY_VIOLATION",
                actor="SYSTEM",
                action="VERIFY",
                target="FULL_SYSTEM",
                result="FAILED",
                details=results
            )
        
        logger.info(f"Integrity verification complete: {results['system_integrity']}")
        
        return results
    
    async def get_case_status(self, case_id: str) -> Dict[str, Any]:
        """Get current status of investigation case."""
        status = await self.orchestrator.get_case_status(case_id)
        return status

async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="JLAW Forensic System - Zero-tolerance SEC filing analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Investigate a company
  python jlaw_forensics.py investigate --cik 0001318605 --name "Tesla Inc" --years 3
  
  # Analyze single filing
  python jlaw_forensics.py analyze --cik 0001318605 --accession 0001564590-24-000123
  
  # Verify system integrity
  python jlaw_forensics.py verify
  
  # Monitor system continuously
  python jlaw_forensics.py monitor
"""
    )
    
    parser.add_argument(
        "command",
        choices=["investigate", "analyze", "verify", "monitor", "status"],
        help="Command to execute"
    )
    
    parser.add_argument("--cik", help="Company CIK")
    parser.add_argument("--name", help="Company name")
    parser.add_argument("--accession", help="SEC accession number")
    parser.add_argument("--case-id", help="Investigation case ID")
    parser.add_argument("--years", type=int, default=3, help="Years to analyze (default: 3)")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--output", help="Output file for results (JSON)")
    
    args = parser.parse_args()
    
    # Initialize system
    try:
        system = JLAWForensicSystem(args.config)
    except Exception as e:
        logger.critical(f"Failed to initialize system: {e}", exc_info=True)
        sys.exit(1)
    
    try:
        results = None
        
        if args.command == "investigate":
            if not args.cik or not args.name:
                parser.error("investigate requires --cik and --name")
            
            results = await system.investigate_company(
                args.cik,
                args.name,
                args.years
            )
            
            # Print summary
            print("\n" + "="*80)
            print(f"INVESTIGATION COMPLETE: {args.name}")
            print("="*80)
            print(f"Risk Score: {results['summary']['risk_score']:.1%}")
            print(f"Criminal Violations: {results['summary']['criminal_violations']}")
            print(f"Filings Analyzed: {results['summary']['filings_analyzed']}")
            print(f"Evidence Stored: {results['summary']['evidence_stored']}")
            print("="*80 + "\n")
        
        elif args.command == "analyze":
            if not args.cik or not args.accession:
                parser.error("analyze requires --cik and --accession")
            
            results = await system.analyze_single_filing(
                args.cik,
                args.accession
            )
            
            # Print summary
            print("\n" + "="*80)
            print(f"FILING ANALYSIS: {args.accession}")
            print("="*80)
            print(f"Traditional Risk: {results['forensic_analysis']['risk_score']:.1%}")
            print(f"ML Prediction: {results['ml_prediction']['fraud_probability']:.1%}")
            print(f"Combined Risk: {results['summary']['combined_risk']:.1%}")
            print(f"Criminal Violations: {results['summary']['criminal_violations']}")
            print("="*80 + "\n")
        
        elif args.command == "status":
            if not args.case_id:
                parser.error("status requires --case-id")
            
            results = await system.get_case_status(args.case_id)
            
            print("\n" + "="*80)
            print(f"CASE STATUS: {args.case_id}")
            print("="*80)
            print(f"Status: {results['status']}")
            print(f"Filings Analyzed: {results['progress']['filings_analyzed']}")
            print(f"Violations Found: {results['progress']['violations_found']}")
            print(f"Current Risk: {results['progress']['current_risk_score']:.1%}")
            print(f"Running Time: {results['timeline']['running_time']:.1f} hours")
            print("="*80 + "\n")
        
        elif args.command == "verify":
            results = await system.verify_system_integrity()
            
            print("\n" + "="*80)
            print("SYSTEM INTEGRITY VERIFICATION")
            print("="*80)
            
            for name, comp in results["components"].items():
                if isinstance(comp, dict) and "valid" in comp:
                    status = "✅ VALID" if comp["valid"] else "❌ INVALID"
                    print(f"{name}: {status}")
                    if "blocks" in comp:
                        print(f"  Blocks: {comp['blocks']}")
            
            print(f"\nOverall Status: {results['system_integrity']}")
            print("="*80 + "\n")
            
            if results["system_integrity"] != "VALID":
                logger.critical("SYSTEM INTEGRITY COMPROMISED")
                sys.exit(1)
        
        elif args.command == "monitor":
            logger.info("Starting continuous monitoring mode...")
            logger.info("Press Ctrl+C to stop")
            
            # Continuous monitoring loop
            iteration = 0
            while True:
                iteration += 1
                logger.info(f"Monitoring iteration {iteration}")
                
                # Verify integrity every hour
                results = await system.verify_system_integrity()
                
                if results["system_integrity"] != "VALID":
                    logger.critical("Integrity violation detected - halting")
                    break
                
                logger.info(f"System integrity: {results['system_integrity']} - Next check in 1 hour")
                await asyncio.sleep(3600)
        
        # Save results to file if requested
        if results and args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            logger.info(f"Results saved to {args.output}")
        
        # Print JSON if no special formatting
        if results and args.command not in ["investigate", "analyze", "verify", "status"]:
            print(json.dumps(results, indent=2))
    
    except KeyboardInterrupt:
        logger.info("System shutdown requested")
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

