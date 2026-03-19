"""
Batch Forensic Orchestrator - Multi-Company Analysis
===================================================

Orchestrates multiple simultaneous forensic investigations with:
- Parallel execution with resource limits
- Comparative peer analysis
- Industry-wide pattern detection
- Sector risk scoring
- Cross-company correlation

Architecture:
    BatchForensicOrchestrator
        ├── Parallel Execution (asyncio.gather with semaphore)
        ├── Industry Analyzer (cross-company patterns)
        ├── Peer Comparison Engine
        └── Sector Risk Scorer

Usage:
    from src.core.batch_forensic_orchestrator import BatchForensicOrchestrator
    from datetime import date
    from pathlib import Path
    
    orchestrator = BatchForensicOrchestrator(
        output_dir=Path("./batch_results"),
        max_concurrent=5
    )
    
    cik_list = ["320187", "1045810", "789019"]
    
    result = await orchestrator.execute_batch(
        cik_list=cik_list,
        start_date=date(2019, 1, 1),
        end_date=date(2019, 12, 31),
        industry_analysis=True
    )
    
    print(f"Analyzed: {result.companies_analyzed}")
    print(f"Violations: {result.total_violations}")
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class BatchResult:
    """Result from batch forensic analysis."""
    companies_analyzed: int
    total_violations: int
    reports_generated: int
    company_results: Dict[str, Any] = field(default_factory=dict)
    industry_analysis: Optional[Dict[str, Any]] = None
    peer_comparisons: Optional[Dict[str, Any]] = None
    sector_risks: Optional[Dict[str, Any]] = None
    execution_start: datetime = field(default_factory=datetime.utcnow)
    execution_end: Optional[datetime] = None
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "companies_analyzed": self.companies_analyzed,
            "total_violations": self.total_violations,
            "reports_generated": self.reports_generated,
            "company_results": self.company_results,
            "industry_analysis": self.industry_analysis,
            "peer_comparisons": self.peer_comparisons,
            "sector_risks": self.sector_risks,
            "execution_start": self.execution_start.isoformat(),
            "execution_end": self.execution_end.isoformat() if self.execution_end else None,
            "errors": self.errors
        }


class BatchForensicOrchestrator:
    """
    Orchestrate multiple simultaneous investigations.

    .. deprecated::
        Use :class:`UnifiedForensicOrchestrator` from
        ``src.core.unified_orchestrator`` for single-company analysis.
        Batch functionality should invoke ``UnifiedForensicOrchestrator``
        in a loop.  This class will be removed in a future version.
    
    Features:
    - Parallel execution with resource limits (semaphore)
    - Comparative peer analysis across companies
    - Industry-wide pattern detection
    - Sector risk scoring and heatmaps
    - Cross-company correlation analysis
    
    Example:
        orchestrator = BatchForensicOrchestrator(
            output_dir=Path("./batch_results"),
            max_concurrent=5
        )
        
        result = await orchestrator.execute_batch(
            cik_list=["320187", "1045810", "789019"],
            start_date=date(2019, 1, 1),
            end_date=date(2019, 12, 31),
            industry_analysis=True
        )
    """
    
    def __init__(
        self,
        output_dir: Path,
        max_concurrent: int = 5
    ):
        """
        Initialize batch orchestrator.
        
        Args:
            output_dir: Output directory for batch results
            max_concurrent: Maximum concurrent investigations
        """
        # DEPRECATION WARNING
        import warnings
        warnings.warn(
            "BatchForensicOrchestrator is deprecated. "
            "Use UnifiedForensicOrchestrator from src.core.unified_orchestrator for DOJ-grade compliance. "
            "This class will be removed in a future version.",
            DeprecationWarning,
            stacklevel=2
        )
        
        self.output_dir = output_dir
        self.max_concurrent = max_concurrent
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Semaphore for concurrency control
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def execute_batch(
        self,
        cik_list: List[str],
        start_date: date,
        end_date: date,
        industry_analysis: bool = True
    ) -> BatchResult:
        """
        Execute batch forensic analysis on multiple companies.
        
        Args:
            cik_list: List of CIK numbers to analyze
            start_date: Analysis start date
            end_date: Analysis end date
            industry_analysis: Enable cross-company industry analysis
        
        Returns:
            BatchResult with aggregate findings
        """
        execution_start = datetime.utcnow()
        
        self.logger.info("=" * 80)
        self.logger.info("  BATCH FORENSIC ORCHESTRATOR - STARTING")
        self.logger.info("=" * 80)
        self.logger.info(f"Companies: {len(cik_list)}")
        self.logger.info(f"Max concurrent: {self.max_concurrent}")
        self.logger.info(f"Industry analysis: {industry_analysis}")
        self.logger.info("=" * 80)
        
        # Initialize result
        batch_result = BatchResult(
            companies_analyzed=0,
            total_violations=0,
            reports_generated=0,
            execution_start=execution_start
        )
        
        # Execute investigations in parallel with concurrency limit
        tasks = []
        for cik in cik_list:
            task = self._execute_single_investigation(
                cik=cik,
                start_date=start_date,
                end_date=end_date
            )
            tasks.append(task)
        
        # Gather results
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for cik, result in zip(cik_list, results):
                if isinstance(result, Exception):
                    self.logger.error(f"Error analyzing {cik}: {result}")
                    batch_result.errors.append(f"{cik}: {str(result)}")
                else:
                    batch_result.companies_analyzed += 1
                    batch_result.company_results[cik] = result
                    batch_result.total_violations += result.get("violations", 0)
                    batch_result.reports_generated += 1
            
            # Industry analysis if requested
            if industry_analysis and batch_result.companies_analyzed > 1:
                batch_result.industry_analysis = self._analyze_industry_patterns(
                    batch_result.company_results
                )
                
                batch_result.peer_comparisons = self._compare_peers(
                    batch_result.company_results
                )
                
                batch_result.sector_risks = self._score_sector_risks(
                    batch_result.company_results
                )
            
            batch_result.execution_end = datetime.utcnow()
            
            # Generate batch report
            await self._generate_batch_report(batch_result)
            
            self.logger.info("=" * 80)
            self.logger.info("  BATCH ANALYSIS COMPLETE")
            self.logger.info("=" * 80)
            self.logger.info(f"Companies analyzed: {batch_result.companies_analyzed}")
            self.logger.info(f"Total violations: {batch_result.total_violations}")
            self.logger.info(f"Duration: {(batch_result.execution_end - execution_start).total_seconds():.1f}s")
            self.logger.info("=" * 80)
            
            return batch_result
            
        except Exception as e:
            self.logger.error(f"Batch execution error: {e}", exc_info=True)
            batch_result.execution_end = datetime.utcnow()
            batch_result.errors.append(f"Batch execution: {str(e)}")
            return batch_result
    
    async def _execute_single_investigation(
        self,
        cik: str,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        Execute single company investigation with concurrency control.
        
        Args:
            cik: Company CIK
            start_date: Analysis start date
            end_date: Analysis end date
        
        Returns:
            Investigation result dictionary
        """
        async with self.semaphore:
            try:
                self.logger.info(f"Starting analysis for CIK {cik}")
                
                # Import here to avoid circular dependency
                from src.core.supreme_orchestrator import SupremeOrchestrator
                
                # Execute analysis using SupremeOrchestrator with TRIAGE strategy
                supreme = SupremeOrchestrator()
                result = await supreme.auto_execute(
                    cik=cik,
                    company_name=f"CIK-{cik}",
                    start_date=start_date,
                    end_date=end_date,
                    output_dir=self.output_dir / cik,
                    priority="triage"  # Fast execution for batch mode
                )
                
                self.logger.info(f"Completed analysis for CIK {cik}: {result.total_violations} violations")
                
                return {
                    "cik": cik,
                    "success": result.success,
                    "violations": result.total_violations,
                    "alerts": result.total_alerts,
                    "node_results": result.node_results,
                    "detection_results": result.detection_results
                }
                
            except Exception as e:
                self.logger.error(f"Error analyzing CIK {cik}: {e}")
                raise
    
    def _analyze_industry_patterns(
        self,
        company_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze industry-wide patterns across companies.
        
        Args:
            company_results: Results from all companies
        
        Returns:
            Industry analysis dictionary
        """
        # Placeholder implementation
        self.logger.info("Analyzing industry-wide patterns...")
        
        # Count common violation types
        violation_types = defaultdict(int)
        for result in company_results.values():
            for violation_type in result.get("violation_types", []):
                violation_types[violation_type] += 1
        
        return {
            "common_violations": dict(violation_types),
            "companies_analyzed": len(company_results),
            "pattern_clusters": []
        }
    
    def _compare_peers(
        self,
        company_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare companies as peers.
        
        Args:
            company_results: Results from all companies
        
        Returns:
            Peer comparison dictionary
        """
        # Placeholder implementation
        self.logger.info("Comparing peer companies...")
        
        comparisons = {}
        for cik, result in company_results.items():
            comparisons[cik] = {
                "violations": result.get("violations", 0),
                "alerts": result.get("alerts", 0),
                "relative_risk": "medium"  # Would be calculated
            }
        
        return comparisons
    
    def _score_sector_risks(
        self,
        company_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Score sector-wide risks.
        
        Args:
            company_results: Results from all companies
        
        Returns:
            Sector risk scoring dictionary
        """
        # Placeholder implementation
        self.logger.info("Scoring sector risks...")
        
        total_violations = sum(
            r.get("violations", 0) for r in company_results.values()
        )
        
        return {
            "sector_risk_level": "medium" if total_violations > 10 else "low",
            "total_violations": total_violations,
            "high_risk_companies": []
        }
    
    async def _generate_batch_report(
        self,
        batch_result: BatchResult
    ) -> None:
        """
        Generate batch analysis report.
        
        Args:
            batch_result: Batch analysis result
        """
        # Save JSON report
        report_path = self.output_dir / f"batch_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        import json
        with open(report_path, 'w') as f:
            json.dump(batch_result.to_dict(), f, indent=2, default=str)
        
        self.logger.info(f"Batch report saved: {report_path}")
