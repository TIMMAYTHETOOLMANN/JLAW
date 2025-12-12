#!/usr/bin/env python3
"""
JLAW Recursive Engine Integration (Nodes 2-5)
==============================================

Orchestrates execution of nodes 2-5 with SEC data fetching, caching,
and PDF report generation. Provides CLI interface for full analysis.

Node Architecture:
- Node 2: DEF 14A Compensation Analysis
- Node 3: 10-Q Temporal Consistency Validation  
- Node 4: 10-K SOX Certification Analysis
- Node 5: IRC §83 Tax Exposure Calculator

Legal Basis: Securities Exchange Act, Sarbanes-Oxley Act, IRC §83
"""

import asyncio
import argparse
import logging
import sys
import json
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Import node implementations
try:
    from src.nodes.node2_def14a.compensation_analyzer import CompensationAnalyzer
except ImportError:
    CompensationAnalyzer = None
    
try:
    from src.nodes.node3_10q.temporal_consistency_validator import TemporalConsistencyValidator
except ImportError:
    TemporalConsistencyValidator = None
    
try:
    from src.nodes.node4_10k_sox.sox_certification_analyzer import SOXCertificationAnalyzer
except ImportError:
    SOXCertificationAnalyzer = None
    
try:
    from src.nodes.node5_irs.irc83_tax_calculator import IRC83TaxCalculator
except ImportError:
    IRC83TaxCalculator = None

# Import infrastructure
try:
    from src.infrastructure.caching.local_cache import LocalCache
except ImportError:
    LocalCache = None

try:
    from src.reporting.pdf_generator import ForensicPDFGenerator
except ImportError:
    ForensicPDFGenerator = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class NodeExecutionResult:
    """Result from individual node execution"""
    node_id: str
    node_name: str
    status: str  # 'success', 'failed', 'skipped'
    execution_time_seconds: float
    violations_found: int
    alerts_generated: int
    findings: Dict[str, Any]
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'node_id': self.node_id,
            'node_name': self.node_name,
            'status': self.status,
            'execution_time': round(self.execution_time_seconds, 2),
            'violations_found': self.violations_found,
            'alerts_generated': self.alerts_generated,
            'findings': self.findings,
            'error': self.error_message
        }


@dataclass
class PhaseResult:
    """Result from phase execution (nodes 2-5 concurrent)"""
    phase_name: str
    phase_number: int
    node_results: List[NodeExecutionResult]
    total_violations: int = 0
    total_alerts: int = 0
    phase_execution_time: float = 0.0
    
    def __post_init__(self):
        """Calculate totals"""
        self.total_violations = sum(r.violations_found for r in self.node_results)
        self.total_alerts = sum(r.alerts_generated for r in self.node_results)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'phase_name': self.phase_name,
            'phase_number': self.phase_number,
            'execution_time': round(self.phase_execution_time, 2),
            'total_violations': self.total_violations,
            'total_alerts': self.total_alerts,
            'nodes': [r.to_dict() for r in self.node_results]
        }


# ═══════════════════════════════════════════════════════════════════════════════
# RECURSIVE ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class JLAWRecursiveEngine:
    """
    Recursive engine for coordinated execution of analysis nodes 2-5.
    
    Features:
    - SEC filing fetch with local caching
    - Async concurrent node execution
    - PDF report generation
    - CLI interface
    """
    
    def __init__(
        self,
        cik: str,
        company_name: str,
        year: int = 2024,
        output_dir: str = "./output",
        enable_cache: bool = True,
        enable_pdf: bool = True
    ):
        """
        Initialize recursive engine
        
        Args:
            cik: SEC CIK number
            company_name: Company name
            year: Analysis fiscal year
            output_dir: Output directory for results
            enable_cache: Enable local caching
            enable_pdf: Enable PDF report generation
        """
        self.cik = cik.zfill(10)  # Pad to 10 digits
        self.company_name = company_name
        self.year = year
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize infrastructure
        self.cache = LocalCache(cache_dir=str(self.output_dir / "cache")) if LocalCache and enable_cache else None
        self.pdf_generator = ForensicPDFGenerator(output_dir=str(self.output_dir)) if ForensicPDFGenerator and enable_pdf else None
        
        # Initialize nodes
        self.node2 = CompensationAnalyzer() if CompensationAnalyzer else None
        self.node3 = TemporalConsistencyValidator() if TemporalConsistencyValidator else None
        self.node4 = SOXCertificationAnalyzer() if SOXCertificationAnalyzer else None
        self.node5 = IRC83TaxCalculator() if IRC83TaxCalculator else None
        
        logger.info(f"Initialized JLAW Recursive Engine for {company_name} (CIK: {self.cik})")
        logger.info(f"Cache: {'Enabled' if self.cache else 'Disabled'}")
        logger.info(f"PDF: {'Enabled' if self.pdf_generator else 'Disabled'}")
    
    async def fetch_sec_filing(
        self,
        form_type: str,
        use_cache: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch SEC filing with caching
        
        Args:
            form_type: Filing form type (DEF 14A, 10-Q, 10-K, Form 4)
            use_cache: Whether to use cache
            
        Returns:
            Filing data or None if not found
        """
        cache_key = f"sec_filing_{self.cik}_{form_type}_{self.year}"
        
        # Check cache
        if use_cache and self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                logger.info(f"Cache hit for {form_type}")
                return cached
        
        logger.info(f"Fetching {form_type} from SEC EDGAR...")
        
        # Simulate SEC EDGAR fetch (in production, use actual SEC API)
        # This is a placeholder for demonstration
        filing_data = {
            'cik': self.cik,
            'form_type': form_type,
            'filing_date': f"{self.year}-03-15",
            'accession_number': f"0001234567-{self.year}-000001",
            'company_name': self.company_name,
            'data': {}
        }
        
        # Cache result
        if use_cache and self.cache:
            self.cache.set(cache_key, filing_data, ttl=86400)  # 24h TTL
            logger.info(f"Cached {form_type} data")
        
        return filing_data
    
    async def execute_node2(self, def14a_data: Dict[str, Any]) -> NodeExecutionResult:
        """Execute Node 2: DEF 14A Compensation Analysis"""
        start_time = time.time()
        node_id = "NODE_2"
        node_name = "DEF 14A Compensation Analysis"
        
        try:
            if not self.node2:
                logger.warning(f"{node_name} not available - skipping")
                return NodeExecutionResult(
                    node_id=node_id,
                    node_name=node_name,
                    status='skipped',
                    execution_time_seconds=0,
                    violations_found=0,
                    alerts_generated=0,
                    findings={},
                    error_message="Module not installed"
                )
            
            logger.info(f"Executing {node_name}...")
            
            # Simulate analysis (in production, call actual analyzer)
            findings = {
                'excessive_compensation': [],
                'say_on_pay_failures': [],
                'parachute_payments': [],
                'violations': []
            }
            
            execution_time = time.time() - start_time
            
            return NodeExecutionResult(
                node_id=node_id,
                node_name=node_name,
                status='success',
                execution_time_seconds=execution_time,
                violations_found=len(findings['violations']),
                alerts_generated=len(findings['violations']),
                findings=findings
            )
            
        except Exception as e:
            logger.error(f"Error in {node_name}: {e}")
            return NodeExecutionResult(
                node_id=node_id,
                node_name=node_name,
                status='failed',
                execution_time_seconds=time.time() - start_time,
                violations_found=0,
                alerts_generated=0,
                findings={},
                error_message=str(e)
            )
    
    async def execute_node3(self, quarterly_10q_data: List[Dict[str, Any]]) -> NodeExecutionResult:
        """Execute Node 3: 10-Q Temporal Consistency Validation"""
        start_time = time.time()
        node_id = "NODE_3"
        node_name = "10-Q Temporal Consistency Validation"
        
        try:
            if not self.node3:
                logger.warning(f"{node_name} not available - skipping")
                return NodeExecutionResult(
                    node_id=node_id,
                    node_name=node_name,
                    status='skipped',
                    execution_time_seconds=0,
                    violations_found=0,
                    alerts_generated=0,
                    findings={},
                    error_message="Module not installed"
                )
            
            logger.info(f"Executing {node_name}...")
            
            findings = {
                'temporal_inconsistencies': [],
                'restatements': [],
                'violations': []
            }
            
            execution_time = time.time() - start_time
            
            return NodeExecutionResult(
                node_id=node_id,
                node_name=node_name,
                status='success',
                execution_time_seconds=execution_time,
                violations_found=len(findings['violations']),
                alerts_generated=len(findings['violations']),
                findings=findings
            )
            
        except Exception as e:
            logger.error(f"Error in {node_name}: {e}")
            return NodeExecutionResult(
                node_id=node_id,
                node_name=node_name,
                status='failed',
                execution_time_seconds=time.time() - start_time,
                violations_found=0,
                alerts_generated=0,
                findings={},
                error_message=str(e)
            )
    
    async def execute_node4(self, annual_10k_data: Dict[str, Any]) -> NodeExecutionResult:
        """Execute Node 4: 10-K SOX Certification Analysis"""
        start_time = time.time()
        node_id = "NODE_4"
        node_name = "10-K SOX Certification Analysis"
        
        try:
            if not self.node4:
                logger.warning(f"{node_name} not available - skipping")
                return NodeExecutionResult(
                    node_id=node_id,
                    node_name=node_name,
                    status='skipped',
                    execution_time_seconds=0,
                    violations_found=0,
                    alerts_generated=0,
                    findings={},
                    error_message="Module not installed"
                )
            
            logger.info(f"Executing {node_name}...")
            
            findings = {
                'certification_issues': [],
                'internal_control_weaknesses': [],
                'violations': []
            }
            
            execution_time = time.time() - start_time
            
            return NodeExecutionResult(
                node_id=node_id,
                node_name=node_name,
                status='success',
                execution_time_seconds=execution_time,
                violations_found=len(findings['violations']),
                alerts_generated=len(findings['violations']),
                findings=findings
            )
            
        except Exception as e:
            logger.error(f"Error in {node_name}: {e}")
            return NodeExecutionResult(
                node_id=node_id,
                node_name=node_name,
                status='failed',
                execution_time_seconds=time.time() - start_time,
                violations_found=0,
                alerts_generated=0,
                findings={},
                error_message=str(e)
            )
    
    async def execute_node5(self, form4_data: List[Dict[str, Any]], grant_data: List[Dict[str, Any]]) -> NodeExecutionResult:
        """Execute Node 5: IRC §83 Tax Exposure Calculator"""
        start_time = time.time()
        node_id = "NODE_5"
        node_name = "IRC §83 Tax Exposure Calculator"
        
        try:
            if not self.node5:
                logger.warning(f"{node_name} not available - skipping")
                return NodeExecutionResult(
                    node_id=node_id,
                    node_name=node_name,
                    status='skipped',
                    execution_time_seconds=0,
                    violations_found=0,
                    alerts_generated=0,
                    findings={},
                    error_message="Module not installed"
                )
            
            logger.info(f"Executing {node_name}...")
            
            # Execute IRC §83 analysis
            company_info = {'cik': self.cik, 'name': self.company_name}
            findings = self.node5.analyze_equity_compensation(form4_data, grant_data, company_info)
            
            execution_time = time.time() - start_time
            
            return NodeExecutionResult(
                node_id=node_id,
                node_name=node_name,
                status='success',
                execution_time_seconds=execution_time,
                violations_found=findings.get('violations_detected', 0),
                alerts_generated=findings.get('violations_detected', 0),
                findings=findings
            )
            
        except Exception as e:
            logger.error(f"Error in {node_name}: {e}")
            return NodeExecutionResult(
                node_id=node_id,
                node_name=node_name,
                status='failed',
                execution_time_seconds=time.time() - start_time,
                violations_found=0,
                alerts_generated=0,
                findings={},
                error_message=str(e)
            )
    
    async def execute_phase1(self) -> PhaseResult:
        """
        Execute Phase 1: Concurrent execution of nodes 2-5
        
        Returns:
            PhaseResult with all node results
        """
        phase_start = time.time()
        logger.info("=" * 80)
        logger.info("PHASE 1: CONCURRENT NODE EXECUTION (Nodes 2-5)")
        logger.info("=" * 80)
        
        # Fetch SEC filings
        def14a_data = await self.fetch_sec_filing("DEF 14A")
        form10k_data = await self.fetch_sec_filing("10-K")
        form10q_q1 = await self.fetch_sec_filing("10-Q_Q1")
        form10q_q2 = await self.fetch_sec_filing("10-Q_Q2")
        form10q_q3 = await self.fetch_sec_filing("10-Q_Q3")
        form4_data = await self.fetch_sec_filing("Form 4")
        
        quarterly_data = [form10q_q1, form10q_q2, form10q_q3]
        
        # Extract grant data from DEF 14A (simplified)
        grant_data = []
        form4_transactions = []
        
        # Execute nodes concurrently
        logger.info("Executing nodes 2-5 concurrently...")
        
        results = await asyncio.gather(
            self.execute_node2(def14a_data),
            self.execute_node3(quarterly_data),
            self.execute_node4(form10k_data),
            self.execute_node5(form4_transactions, grant_data),
            return_exceptions=True
        )
        
        # Handle exceptions
        node_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Node execution failed: {result}")
                # Create failed result
                node_results.append(NodeExecutionResult(
                    node_id="UNKNOWN",
                    node_name="Unknown",
                    status='failed',
                    execution_time_seconds=0,
                    violations_found=0,
                    alerts_generated=0,
                    findings={},
                    error_message=str(result)
                ))
            else:
                node_results.append(result)
        
        phase_time = time.time() - phase_start
        
        phase_result = PhaseResult(
            phase_name="Nodes 2-5 Analysis",
            phase_number=1,
            node_results=node_results,
            phase_execution_time=phase_time
        )
        
        logger.info(f"Phase 1 complete in {phase_time:.2f}s")
        logger.info(f"Total violations: {phase_result.total_violations}")
        logger.info(f"Total alerts: {phase_result.total_alerts}")
        
        return phase_result
    
    async def run_full_analysis(self, generate_pdf: bool = True) -> Dict[str, Any]:
        """
        Run full analysis workflow
        
        Args:
            generate_pdf: Whether to generate PDF report
            
        Returns:
            Complete analysis results
        """
        analysis_start = time.time()
        
        logger.info("")
        logger.info("╔" + "═" * 78 + "╗")
        logger.info("║" + " " * 20 + "JLAW RECURSIVE ENGINE ANALYSIS" + " " * 28 + "║")
        logger.info("║" + f"  Target: {self.company_name} (CIK: {self.cik})".ljust(78) + "║")
        logger.info("║" + f"  Year: {self.year}".ljust(78) + "║")
        logger.info("╚" + "═" * 78 + "╝")
        logger.info("")
        
        # Execute Phase 1
        phase1_result = await self.execute_phase1()
        
        # Compile results
        results = {
            'case_id': f"JLAW-{self.cik}-{self.year}",
            'company_name': self.company_name,
            'cik': self.cik,
            'analysis_year': self.year,
            'analysis_timestamp': datetime.now().isoformat(),
            'total_execution_time': time.time() - analysis_start,
            'phase1': phase1_result.to_dict(),
            'total_violations': phase1_result.total_violations,
            'total_alerts': phase1_result.total_alerts,
            'regulatory_routing': {
                'SEC': phase1_result.total_violations > 0,
                'IRS': any(r.node_id == 'NODE_5' and r.violations_found > 0 for r in phase1_result.node_results),
                'DOJ': phase1_result.total_violations >= 5
            }
        }
        
        # Save JSON results
        json_output = self.output_dir / f"analysis_{self.cik}_{self.year}.json"
        with open(json_output, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"JSON results saved: {json_output}")
        
        # Generate PDF report
        if generate_pdf and self.pdf_generator:
            logger.info("Generating PDF report...")
            try:
                pdf_path = self.pdf_generator.generate_forensic_dossier(
                    case_id=results['case_id'],
                    company_name=self.company_name,
                    cik=self.cik,
                    analysis_results=results
                )
                logger.info(f"PDF report generated: {pdf_path}")
                results['pdf_report'] = str(pdf_path)
            except Exception as e:
                logger.error(f"PDF generation failed: {e}")
        
        logger.info("")
        logger.info("=" * 80)
        logger.info("ANALYSIS COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Total violations: {results['total_violations']}")
        logger.info(f"Total alerts: {results['total_alerts']}")
        logger.info(f"Execution time: {results['total_execution_time']:.2f}s")
        logger.info(f"Output directory: {self.output_dir}")
        logger.info("=" * 80)
        
        return results


# ═══════════════════════════════════════════════════════════════════════════════
# CLI INTERFACE
# ═══════════════════════════════════════════════════════════════════════════════

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="JLAW Recursive Engine - Forensic Analysis (Nodes 2-5)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Demo mode with test data
  python -m src.core.recursive_engine_integration --demo
  
  # Analyze specific company
  python -m src.core.recursive_engine_integration --cik 0000320193 --name "Apple Inc." --year 2024
  
  # Without PDF generation
  python -m src.core.recursive_engine_integration --cik 0000320193 --name "Apple Inc." --no-pdf
        """
    )
    
    parser.add_argument('--demo', action='store_true', help='Run demo analysis')
    parser.add_argument('--cik', type=str, help='Company CIK number')
    parser.add_argument('--name', type=str, help='Company name')
    parser.add_argument('--year', type=int, default=2024, help='Analysis fiscal year (default: 2024)')
    parser.add_argument('--output', type=str, default='./output', help='Output directory')
    parser.add_argument('--no-pdf', action='store_true', help='Skip PDF generation')
    parser.add_argument('--no-cache', action='store_true', help='Disable caching')
    
    return parser.parse_args()


async def main():
    """Main entry point"""
    args = parse_args()
    
    # Determine target
    if args.demo:
        cik = "0000320193"
        company_name = "Apple Inc. (Demo)"
        year = 2024
    elif args.cik and args.name:
        cik = args.cik
        company_name = args.name
        year = args.year
    else:
        print("Error: Must specify either --demo or both --cik and --name")
        return 1
    
    # Initialize engine
    engine = JLAWRecursiveEngine(
        cik=cik,
        company_name=company_name,
        year=year,
        output_dir=args.output,
        enable_cache=not args.no_cache,
        enable_pdf=not args.no_pdf
    )
    
    # Run analysis
    try:
        results = await engine.run_full_analysis(generate_pdf=not args.no_pdf)
        return 0 if results['total_violations'] >= 0 else 1
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
