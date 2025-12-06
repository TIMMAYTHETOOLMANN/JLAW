ight now. 
JLAW FORENSIC SYSTEM - NIKE 2019 ENHANCED PRODUCTION RUN
=========================================================
Fresh production analysis using the complete enhanced forensic platform.

Target: Nike Inc. (CIK: 0000320187) - All 2019 SEC Filings
System: All 9 Enhancement Phases Enabled
Mode: Live Web Scraping + API Integration

This script performs a FRESH analysis with:
- Live SEC EDGAR web scraping
- Complete Form 4 insider transaction analysis
- 10-K/10-Q periodic report analysis
- All forensic enhancement modules active
- Dual-agent validation (if available)
- Comprehensive statutory mapping
- Full evidence chain documentation
"""

import asyncio
import json
import sys
import logging
from datetime import datetime, timezone
from pathlib import Path

# Ensure proper path
sys.path.insert(0, str(Path(__file__).parent))

from src.forensics import (
    ForensicOrchestrator,
    StorageConfig,
    get_system_status,
    ForensicCase,
    InvestigationStatus
)
from src.forensics.config_manager import ConfigurationManager


class NikeEnhancedProductionRun:
    """
    Enhanced production run for Nike 2019 SEC filing analysis.
    Leverages all system enhancements and generates comprehensive forensic output.
    """
    
    # Target parameters
    CIK = "0000320187"
    COMPANY_NAME = "Nike Inc."
    YEAR = 2019
    FILING_TYPES = ["10-K", "10-Q", "4"]
    
    # Benchmark targets from prior analysis
    BENCHMARK_TOTAL_VIOLATIONS = 54
    BENCHMARK_LATE_FORM4 = 29
    BENCHMARK_ZERO_DOLLAR = 19
    BENCHMARK_FILINGS = 89
    
    def __init__(self):
        self.timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        self.run_id = f"NIKE_2019_ENHANCED_{self.timestamp}"
        self.output_dir = Path("forensic_reports") / "nike_2019_enhanced" / self.run_id
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self._setup_logging()
        
        # Results storage
        self.results = {
            "run_id": self.run_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "target": {
                "cik": self.CIK,
                "company": self.COMPANY_NAME,
                "year": self.YEAR,
                "filing_types": self.FILING_TYPES
            },
            "system_status": {},
            "filings": {},
            "violations": {},
            "analysis": {},
            "benchmark_comparison": {}
        }
    
    def _setup_logging(self):
        """Configure comprehensive logging."""
        log_file = self.output_dir / f"production_run_{self.timestamp}.log"
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # File handler
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
        
        self.logger = logging.getLogger("NikeEnhancedProduction")
        self.log_file = log_file
    
    async def run(self):
        """Execute the enhanced production analysis."""
        self.logger.info("=" * 100)
        self.logger.info("JLAW FORENSIC SYSTEM - NIKE 2019 ENHANCED PRODUCTION RUN")
        self.logger.info("=" * 100)
        self.logger.info(f"Run ID: {self.run_id}")
        self.logger.info(f"Target: {self.COMPANY_NAME} (CIK: {self.CIK})")
        self.logger.info(f"Period: {self.YEAR}")
        self.logger.info(f"Output: {self.output_dir}")
        self.logger.info("=" * 100)
        
        start_time = datetime.now(timezone.utc)
        
        try:
            # Phase 0: System validation
            await self._phase0_system_validation()
            
            # Phase 1: Initialize orchestrator
            orchestrator = await self._phase1_initialize_system()
            
            # Phase 2: Initiate investigation
            case_id = await self._phase2_initiate_investigation(orchestrator)
            
            # Phase 3: Run full investigation with all enhancements
            report = await self._phase3_full_investigation(orchestrator, case_id)
            
            # Phase 4: Generate enhanced outputs
            await self._phase4_generate_outputs(report)
            
            # Phase 5: Benchmark comparison
            await self._phase5_benchmark_comparison()
            
            # Finalize
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            self.results["duration_seconds"] = duration
            self.results["status"] = "SUCCESS"
            
            self.logger.info("")
            self.logger.info("=" * 100)
            self.logger.info("PRODUCTION RUN COMPLETE")
            self.logger.info("=" * 100)
            self.logger.info(f"Duration: {duration:.2f} seconds")
            self.logger.info(f"Output Directory: {self.output_dir}")
            
            # Save final results
            self._save_results()
            
            return True
            
        except Exception as e:
            self.logger.error(f"PRODUCTION RUN FAILED: {e}", exc_info=True)
            self.results["status"] = "FAILED"
            self.results["error"] = str(e)
            self._save_results()
            return False
    
    async def _phase0_system_validation(self):
        """Validate all system components are operational."""
        self.logger.info("")
        self.logger.info("-" * 100)
        self.logger.info("PHASE 0: SYSTEM VALIDATION")
        self.logger.info("-" * 100)
        
        # Get system status
        status = get_system_status()
        self.results["system_status"] = status
        
        self.logger.info(f"System Version: {status['version']}")
        self.logger.info(f"All Phases Operational: {status['all_phases_operational']}")
        
        for phase, available in status['phases'].items():
            marker = "+" if available else "X"
            self.logger.info(f"  [{marker}] {phase}")
        
        if not status['all_phases_operational']:
            self.logger.warning("Some phases are not fully operational - proceeding with available modules")
    
    async def _phase1_initialize_system(self) -> ForensicOrchestrator:
        """Initialize the forensic orchestrator with all modules."""
        self.logger.info("")
        self.logger.info("-" * 100)
        self.logger.info("PHASE 1: SYSTEM INITIALIZATION")
        self.logger.info("-" * 100)
        
        # Load configuration
        config_mgr = ConfigurationManager()
        config = config_mgr.config
        
        self.logger.info(f"Configuration loaded")
        self.logger.info(f"  SEC User-Agent: {config.sec.user_agent}")
        self.logger.info(f"  Storage Provider: {config.storage_provider}")
        self.logger.info(f"  AI Provider: {config.ai_provider.provider}")
        
        # Create storage config
        storage_config = StorageConfig(
            provider=config.storage_provider,
            retention_days=365,
            compliance_mode=True,
            redundancy_level=2,
            compression=True
        )
        
        # Initialize orchestrator
        orchestrator = ForensicOrchestrator(
            govinfo_api_key=config.govinfo.api_key or "DEMO_KEY",
            storage_config=storage_config,
            audit_signing_key=f"nike_2019_enhanced_{self.timestamp}".encode(),
            user_agent=config.sec.user_agent or "NITS Recon Unit contact@nits-secops.org"
        )
        
        self.logger.info("Forensic Orchestrator initialized successfully")
        
        # Log available analyzers
        if hasattr(orchestrator, 'openai_analyzer') and orchestrator.openai_analyzer:
            self.logger.info("  [+] OpenAI Analyzer: AVAILABLE")
        else:
            self.logger.info("  [-] OpenAI Analyzer: NOT AVAILABLE")
            
        if hasattr(orchestrator, 'anthropic_analyzer') and orchestrator.anthropic_analyzer:
            self.logger.info("  [+] Anthropic Analyzer: AVAILABLE")
        else:
            self.logger.info("  [-] Anthropic Analyzer: NOT AVAILABLE")
            
        if hasattr(orchestrator, 'dual_agent_coordinator') and orchestrator.dual_agent_coordinator:
            self.logger.info("  [+] Dual-Agent Coordinator: AVAILABLE")
        else:
            self.logger.info("  [-] Dual-Agent Coordinator: NOT AVAILABLE")
        
        return orchestrator
    
    async def _phase2_initiate_investigation(self, orchestrator: ForensicOrchestrator) -> str:
        """Initiate the forensic investigation case."""
        self.logger.info("")
        self.logger.info("-" * 100)
        self.logger.info("PHASE 2: INVESTIGATION INITIATION")
        self.logger.info("-" * 100)
        
        case_id = await orchestrator.initiate_investigation(
            cik=self.CIK,
            company_name=self.COMPANY_NAME,
            investigator="JLAW_NEXUS_ENHANCED",
            case_notes=f"Nike 2019 Enhanced Production Run - Fresh analysis with all enhancement modules - Run ID: {self.run_id}"
        )
        
        self.logger.info(f"Investigation initiated: {case_id}")
        self.results["case_id"] = case_id
        
        return case_id
    
    async def _phase3_full_investigation(self, orchestrator: ForensicOrchestrator, case_id: str) -> dict:
        """Execute the full forensic investigation."""
        self.logger.info("")
        self.logger.info("-" * 100)
        self.logger.info("PHASE 3: FULL INVESTIGATION EXECUTION")
        self.logger.info("-" * 100)
        self.logger.info("This phase will:")
        self.logger.info("  - Collect all SEC filings from 2019")
        self.logger.info("  - Analyze Form 4s for insider violations")
        self.logger.info("  - Analyze 10-K/10-Q for disclosure issues")
        self.logger.info("  - Apply all forensic enhancement modules")
        self.logger.info("  - Generate comprehensive violation mapping")
        self.logger.info("")
        self.logger.info("Estimated runtime: 5-15 minutes (with SEC rate limiting)")
        self.logger.info("")
        
        # Use STANDARD investigation - more reliable without external AI dependencies
        # This uses the built-in manual analyzer + Holy Grail Universal Extractor
        self.logger.info("Using STANDARD investigation workflow with enhanced forensic modules...")
        self.logger.info("  - Manual SEC Analyzer: Active")
        self.logger.info("  - Holy Grail Universal Extractor: Active")
        self.logger.info("  - Form 4 Insider Trading Analyzer: Active")
        self.logger.info("  - Forensic Statutory Mapper: Active")
        self.logger.info("  - Advanced Statute Integrator: Active")
        self.logger.info("")
        
        report = await orchestrator.run_full_investigation(
            case_id=case_id,
            filing_types=self.FILING_TYPES,
            years=1  # Just 2019
        )
        
        # Store results
        self.results["investigation_report"] = report
        
        return report
    
    async def _phase4_generate_outputs(self, report: dict):
        """Generate comprehensive output files."""
        self.logger.info("")
        self.logger.info("-" * 100)
        self.logger.info("PHASE 4: OUTPUT GENERATION")
        self.logger.info("-" * 100)
        
        # Extract key metrics
        summary = report.get("summary", {})
        
        self.results["analysis"] = {
            "filings_collected": summary.get("filings_collected", 0),
            "filings_analyzed": summary.get("filings_analyzed", 0),
            "violations_detected": summary.get("violations_detected", 0),
            "criminal_violations": summary.get("criminal_violations", 0),
            "risk_score": summary.get("risk_score", 0),
            "evidence_stored": summary.get("evidence_stored", 0)
        }
        
        self.logger.info(f"Filings Collected: {self.results['analysis']['filings_collected']}")
        self.logger.info(f"Filings Analyzed: {self.results['analysis']['filings_analyzed']}")
        self.logger.info(f"Violations Detected: {self.results['analysis']['violations_detected']}")
        self.logger.info(f"Risk Score: {self.results['analysis']['risk_score']:.1%}" if isinstance(self.results['analysis']['risk_score'], float) else f"Risk Score: {self.results['analysis']['risk_score']}")
        
        # Try to generate PDF report if reporting module available
        try:
            from src.forensics.reporting import ProsecutionReportGenerator
            self.logger.info("Generating prosecution report...")
            generator = ProsecutionReportGenerator()
            generator.generate(str(self.output_dir), report)
            self.logger.info("  Prosecution report generated")
        except Exception as e:
            self.logger.warning(f"  Report generation skipped: {e}")
    
    async def _phase5_benchmark_comparison(self):
        """Compare results against benchmark targets."""
        self.logger.info("")
        self.logger.info("-" * 100)
        self.logger.info("PHASE 5: BENCHMARK COMPARISON")
        self.logger.info("-" * 100)
        
        analysis = self.results.get("analysis", {})
        
        violations = analysis.get("violations_detected", 0)
        filings = analysis.get("filings_collected", 0)
        
        # Calculate benchmark status
        violation_pct = (violations / self.BENCHMARK_TOTAL_VIOLATIONS * 100) if self.BENCHMARK_TOTAL_VIOLATIONS > 0 else 0
        filing_pct = (filings / self.BENCHMARK_FILINGS * 100) if self.BENCHMARK_FILINGS > 0 else 0
        
        self.results["benchmark_comparison"] = {
            "violations": {
                "target": self.BENCHMARK_TOTAL_VIOLATIONS,
                "actual": violations,
                "percent": violation_pct,
                "status": "PASS" if violations >= self.BENCHMARK_TOTAL_VIOLATIONS else "BELOW_TARGET"
            },
            "filings": {
                "target": self.BENCHMARK_FILINGS,
                "actual": filings,
                "percent": filing_pct,
                "status": "PASS" if filings >= self.BENCHMARK_FILINGS else "BELOW_TARGET"
            }
        }
        
        self.logger.info("")
        self.logger.info("BENCHMARK COMPARISON:")
        self.logger.info(f"  Violations: {violations}/{self.BENCHMARK_TOTAL_VIOLATIONS} ({violation_pct:.1f}%)")
        self.logger.info(f"  Filings:    {filings}/{self.BENCHMARK_FILINGS} ({filing_pct:.1f}%)")
        self.logger.info("")
        
        if violations >= self.BENCHMARK_TOTAL_VIOLATIONS:
            self.logger.info("  [PASS] Violation target MET or EXCEEDED")
        else:
            self.logger.info("  [BELOW] Violation target not met")
    
    def _save_results(self):
        """Save all results to output files."""
        # Save JSON results
        results_file = self.output_dir / f"results_{self.timestamp}.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        self.logger.info(f"Results saved to: {results_file}")
        
        # Generate summary text report
        summary_file = self.output_dir / f"summary_{self.timestamp}.txt"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("=" * 100 + "\n")
            f.write("JLAW FORENSIC SYSTEM - NIKE 2019 ENHANCED PRODUCTION RUN\n")
            f.write("=" * 100 + "\n\n")
            f.write(f"Run ID: {self.run_id}\n")
            f.write(f"Timestamp: {self.results['timestamp']}\n")
            f.write(f"Status: {self.results.get('status', 'UNKNOWN')}\n")
            f.write(f"Duration: {self.results.get('duration_seconds', 0):.2f} seconds\n\n")
            
            f.write("-" * 100 + "\n")
            f.write("TARGET\n")
            f.write("-" * 100 + "\n")
            f.write(f"Company: {self.COMPANY_NAME}\n")
            f.write(f"CIK: {self.CIK}\n")
            f.write(f"Year: {self.YEAR}\n")
            f.write(f"Filing Types: {', '.join(self.FILING_TYPES)}\n\n")
            
            analysis = self.results.get("analysis", {})
            f.write("-" * 100 + "\n")
            f.write("RESULTS\n")
            f.write("-" * 100 + "\n")
            f.write(f"Filings Collected: {analysis.get('filings_collected', 0)}\n")
            f.write(f"Filings Analyzed: {analysis.get('filings_analyzed', 0)}\n")
            f.write(f"Violations Detected: {analysis.get('violations_detected', 0)}\n")
            f.write(f"Criminal Violations: {analysis.get('criminal_violations', 0)}\n")
            f.write(f"Risk Score: {analysis.get('risk_score', 0)}\n\n")
            
            benchmark = self.results.get("benchmark_comparison", {})
            f.write("-" * 100 + "\n")
            f.write("BENCHMARK COMPARISON\n")
            f.write("-" * 100 + "\n")
            for metric, data in benchmark.items():
                if isinstance(data, dict):
                    f.write(f"{metric.upper()}: {data.get('actual', 0)}/{data.get('target', 0)} - {data.get('status', 'UNKNOWN')}\n")
            f.write("\n")
            f.write("=" * 100 + "\n")
        
        self.logger.info(f"Summary saved to: {summary_file}")


async def main():
    """Main entry point."""
    print("\n" + "=" * 100)
    print("JLAW FORENSIC SYSTEM - NIKE 2019 ENHANCED PRODUCTION RUN")
    print("=" * 100)
    print(f"\nStarting fresh production analysis at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nThis will execute:")
    print("  - Live SEC EDGAR web scraping")
    print("  - All 9 enhancement phases")
    print("  - Complete Form 4 + 10-K/10-Q analysis")
    print("  - Comprehensive forensic reporting")
    print("\n" + "=" * 100 + "\n")
    
    runner = NikeEnhancedProductionRun()
    success = await runner.run()
    
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

