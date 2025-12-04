"""
Investigation Orchestrator - Master Workflow Coordinator
=========================================================

Central orchestration system for managing complete forensic investigations.
Coordinates all nine phases of the Enhancement Protocol:

Phase 1: Advanced Document Parsing
Phase 2: Omniscient Intelligence Gathering
Phase 3: Legal Statute Correlation
Phase 4: Temporal Analysis & Timeline Reconstruction
Phase 5: Decision Engine & Prosecution Path Builder
Phase 6: Advanced Contradiction Detection
Phase 7: Comprehensive Reporting Engine
Phase 8: Master Orchestrator (this module)
Phase 9: Deployment & Health Check
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from enum import Enum
import uuid
import json

logger = logging.getLogger(__name__)


class InvestigationPhase(Enum):
    """Investigation phases based on Enhancement Protocol."""
    DOCUMENT_PARSING = "phase_1_document_parsing"
    INTELLIGENCE_GATHERING = "phase_2_intelligence_gathering"
    LEGAL_CORRELATION = "phase_3_legal_correlation"
    TEMPORAL_ANALYSIS = "phase_4_temporal_analysis"
    PROSECUTION_PATH = "phase_5_prosecution_path"
    CONTRADICTION_DETECTION = "phase_6_contradiction_detection"
    REPORTING = "phase_7_reporting"
    ORCHESTRATION = "phase_8_orchestration"
    DEPLOYMENT = "phase_9_deployment"


class InvestigationStatus(Enum):
    """Investigation status states."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class PhaseResult:
    """Result from a single investigation phase."""
    phase: InvestigationPhase
    status: InvestigationStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0
    results: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InvestigationConfig:
    """Configuration for an investigation."""
    target: str
    input_files: List[str] = field(default_factory=list)
    output_dir: str = "./reports"
    
    # Phase-specific options
    enable_ocr: bool = True
    enable_intelligence: bool = True
    enable_legal_analysis: bool = True
    enable_temporal_analysis: bool = True
    enable_contradiction_detection: bool = True
    enable_prosecution_paths: bool = True
    
    # Processing options
    parallel_processing: bool = True
    max_workers: int = 4
    timeout_seconds: int = 3600
    
    # Output options
    generate_pdf: bool = True
    generate_html: bool = True
    generate_json: bool = True
    
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InvestigationResult:
    """Complete investigation result."""
    case_id: str
    target: str
    status: InvestigationStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0
    
    # Phase results
    phase_results: Dict[str, PhaseResult] = field(default_factory=dict)
    
    # Summary data
    summary: Dict[str, Any] = field(default_factory=dict)
    
    # Output files
    output_files: List[str] = field(default_factory=list)
    
    # Errors and warnings
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # Metrics
    metrics: Dict[str, Any] = field(default_factory=dict)


class InvestigationOrchestrator:
    """
    Master Investigation Orchestrator
    
    Coordinates all phases of a forensic investigation according to
    the Enhancement Protocol specification.
    
    Example usage:
        orchestrator = InvestigationOrchestrator()
        config = InvestigationConfig(
            target="Company XYZ",
            input_files=["evidence1.pdf", "evidence2.xlsx"]
        )
        result = await orchestrator.run_investigation(config)
    """
    
    def __init__(
        self,
        output_dir: Optional[Path] = None,
        enable_parallel: bool = True,
        max_concurrent_phases: int = 4
    ):
        """
        Initialize the Investigation Orchestrator.
        
        Args:
            output_dir: Directory for output files
            enable_parallel: Enable parallel phase execution
            max_concurrent_phases: Maximum concurrent phase executions
        """
        self.output_dir = output_dir or Path("./forensic_output")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.enable_parallel = enable_parallel
        self.max_concurrent_phases = max_concurrent_phases
        
        self._active_investigations: Dict[str, InvestigationResult] = {}
        self._phase_handlers: Dict[InvestigationPhase, Callable[..., Any]] = {}
        
        # Initialize phase handlers
        self._register_default_handlers()
        
        logger.info("InvestigationOrchestrator initialized")
    
    def _register_default_handlers(self) -> None:
        """Register default phase handlers."""
        self._phase_handlers = {
            InvestigationPhase.DOCUMENT_PARSING: self._run_document_parsing,
            InvestigationPhase.INTELLIGENCE_GATHERING: self._run_intelligence_gathering,
            InvestigationPhase.LEGAL_CORRELATION: self._run_legal_correlation,
            InvestigationPhase.TEMPORAL_ANALYSIS: self._run_temporal_analysis,
            InvestigationPhase.PROSECUTION_PATH: self._run_prosecution_path,
            InvestigationPhase.CONTRADICTION_DETECTION: self._run_contradiction_detection,
            InvestigationPhase.REPORTING: self._run_reporting,
        }
    
    async def run_investigation(
        self,
        config: InvestigationConfig
    ) -> InvestigationResult:
        """
        Run a complete forensic investigation.
        
        Args:
            config: Investigation configuration
            
        Returns:
            Complete investigation result
        """
        case_id = f"CASE-{uuid.uuid4().hex[:8].upper()}"
        started_at = datetime.now()
        
        logger.info(f"Starting investigation {case_id} for target: {config.target}")
        
        result = InvestigationResult(
            case_id=case_id,
            target=config.target,
            status=InvestigationStatus.IN_PROGRESS,
            started_at=started_at
        )
        
        self._active_investigations[case_id] = result
        
        try:
            # Define phase execution order
            phases = self._get_phase_order(config)
            
            # Execute phases
            if self.enable_parallel and config.parallel_processing:
                await self._run_phases_parallel(result, config, phases)
            else:
                await self._run_phases_sequential(result, config, phases)
            
            # Aggregate results
            result.summary = self._aggregate_results(result)
            
            # Generate outputs
            if config.generate_pdf or config.generate_html or config.generate_json:
                await self._generate_outputs(result, config)
            
            result.status = InvestigationStatus.COMPLETED
            result.completed_at = datetime.now()
            result.duration_seconds = (
                result.completed_at - result.started_at
            ).total_seconds()
            
            logger.info(
                f"Investigation {case_id} completed in {result.duration_seconds:.2f}s"
            )
            
        except Exception as e:
            result.status = InvestigationStatus.FAILED
            result.errors.append(str(e))
            logger.error(f"Investigation {case_id} failed: {e}")
            raise
        
        finally:
            self._active_investigations.pop(case_id, None)
        
        return result
    
    def _get_phase_order(self, config: InvestigationConfig) -> List[InvestigationPhase]:
        """Get ordered list of phases to execute."""
        phases = []
        
        # Always start with document parsing
        phases.append(InvestigationPhase.DOCUMENT_PARSING)
        
        # Add optional phases based on config
        if config.enable_intelligence:
            phases.append(InvestigationPhase.INTELLIGENCE_GATHERING)
        
        if config.enable_legal_analysis:
            phases.append(InvestigationPhase.LEGAL_CORRELATION)
        
        if config.enable_temporal_analysis:
            phases.append(InvestigationPhase.TEMPORAL_ANALYSIS)
        
        if config.enable_prosecution_paths:
            phases.append(InvestigationPhase.PROSECUTION_PATH)
        
        if config.enable_contradiction_detection:
            phases.append(InvestigationPhase.CONTRADICTION_DETECTION)
        
        # Always end with reporting
        phases.append(InvestigationPhase.REPORTING)
        
        return phases
    
    async def _run_phases_sequential(
        self,
        result: InvestigationResult,
        config: InvestigationConfig,
        phases: List[InvestigationPhase]
    ) -> None:
        """Run phases sequentially."""
        for phase in phases:
            await self._run_phase(result, config, phase)
    
    async def _run_phases_parallel(
        self,
        result: InvestigationResult,
        config: InvestigationConfig,
        phases: List[InvestigationPhase]
    ) -> None:
        """Run phases with parallelism where possible."""
        # Group phases by dependencies
        # Phases 1-2 can run in parallel
        # Phase 3 depends on 1
        # Phase 4 depends on 1
        # Phase 5 depends on 3, 4
        # Phase 6 depends on 1, 4
        # Phase 7 depends on all
        
        # Execute Phase 1 and 2 in parallel
        phase_1_2 = [p for p in phases if p in [
            InvestigationPhase.DOCUMENT_PARSING,
            InvestigationPhase.INTELLIGENCE_GATHERING
        ]]
        if phase_1_2:
            await asyncio.gather(*[
                self._run_phase(result, config, p) for p in phase_1_2
            ])
        
        # Execute Phase 3 and 4 in parallel
        phase_3_4 = [p for p in phases if p in [
            InvestigationPhase.LEGAL_CORRELATION,
            InvestigationPhase.TEMPORAL_ANALYSIS
        ]]
        if phase_3_4:
            await asyncio.gather(*[
                self._run_phase(result, config, p) for p in phase_3_4
            ])
        
        # Execute Phase 5 and 6 in parallel
        phase_5_6 = [p for p in phases if p in [
            InvestigationPhase.PROSECUTION_PATH,
            InvestigationPhase.CONTRADICTION_DETECTION
        ]]
        if phase_5_6:
            await asyncio.gather(*[
                self._run_phase(result, config, p) for p in phase_5_6
            ])
        
        # Execute Phase 7 (reporting) last
        if InvestigationPhase.REPORTING in phases:
            await self._run_phase(result, config, InvestigationPhase.REPORTING)
    
    async def _run_phase(
        self,
        result: InvestigationResult,
        config: InvestigationConfig,
        phase: InvestigationPhase
    ) -> PhaseResult:
        """Run a single investigation phase."""
        started_at = datetime.now()
        
        phase_result = PhaseResult(
            phase=phase,
            status=InvestigationStatus.IN_PROGRESS,
            started_at=started_at
        )
        
        logger.info(f"Starting phase: {phase.value}")
        
        try:
            handler = self._phase_handlers.get(phase)
            if handler:
                phase_result.results = await handler(result, config)
            
            phase_result.status = InvestigationStatus.COMPLETED
            
        except Exception as e:
            phase_result.status = InvestigationStatus.FAILED
            phase_result.errors.append(str(e))
            logger.error(f"Phase {phase.value} failed: {e}")
        
        finally:
            phase_result.completed_at = datetime.now()
            phase_result.duration_seconds = (
                phase_result.completed_at - phase_result.started_at
            ).total_seconds()
            result.phase_results[phase.value] = phase_result
            
            logger.info(
                f"Phase {phase.value} completed in {phase_result.duration_seconds:.2f}s"
            )
        
        return phase_result
    
    async def _run_document_parsing(
        self,
        result: InvestigationResult,
        config: InvestigationConfig
    ) -> Dict[str, Any]:
        """Execute Phase 1: Document Parsing."""
        logger.info("Executing Phase 1: Document Parsing")
        
        documents_processed = 0
        entities_extracted = 0
        tables_extracted = 0
        
        for input_file in config.input_files:
            try:
                # In a full implementation, this would use:
                # - UniversalDocumentProcessor
                # - OCRCascade
                # - ForensicTableExtractor
                # - FinancialParser
                documents_processed += 1
                entities_extracted += 10  # Placeholder
                tables_extracted += 2  # Placeholder
                
            except Exception as e:
                logger.warning(f"Failed to process {input_file}: {e}")
        
        return {
            "documents_processed": documents_processed,
            "entities_extracted": entities_extracted,
            "tables_extracted": tables_extracted,
            "processing_time_ms": 100 * documents_processed
        }
    
    async def _run_intelligence_gathering(
        self,
        result: InvestigationResult,
        config: InvestigationConfig
    ) -> Dict[str, Any]:
        """Execute Phase 2: Intelligence Gathering."""
        logger.info("Executing Phase 2: Intelligence Gathering")
        
        # In a full implementation, this would use:
        # - OmniscientIntelligenceGatherer
        # - SEC EDGAR Integration
        # - Social Media Intelligence
        # - Financial Data APIs
        
        return {
            "sec_filings_retrieved": 5,
            "news_articles_collected": 20,
            "social_media_posts_analyzed": 100,
            "financial_data_points": 500
        }
    
    async def _run_legal_correlation(
        self,
        result: InvestigationResult,
        config: InvestigationConfig
    ) -> Dict[str, Any]:
        """Execute Phase 3: Legal Statute Correlation."""
        logger.info("Executing Phase 3: Legal Statute Correlation")
        
        # In a full implementation, this would use:
        # - LegalStatuteCorrelationEngine
        # - GovInfo API Integration
        # - Neo4j Graph Database
        # - ViolationDetector
        
        return {
            "statutes_analyzed": 15,
            "potential_violations": 3,
            "usc_citations": ["15 USC 78j", "18 USC 1348"],
            "cfr_citations": ["17 CFR 240.10b-5"]
        }
    
    async def _run_temporal_analysis(
        self,
        result: InvestigationResult,
        config: InvestigationConfig
    ) -> Dict[str, Any]:
        """Execute Phase 4: Temporal Analysis."""
        logger.info("Executing Phase 4: Temporal Analysis")
        
        # In a full implementation, this would use:
        # - ForensicTimelineReconstructor
        # - TemporalParser
        # - EventCorrelator
        # - TemporalAnomalyDetector
        
        return {
            "events_extracted": 50,
            "timeline_entries": 45,
            "temporal_contradictions": 2,
            "causal_chains_identified": 3
        }
    
    async def _run_prosecution_path(
        self,
        result: InvestigationResult,
        config: InvestigationConfig
    ) -> Dict[str, Any]:
        """Execute Phase 5: Prosecution Path Building."""
        logger.info("Executing Phase 5: Prosecution Path Building")
        
        # In a full implementation, this would use:
        # - ProsecutionPathBuilder
        # - ForensicEvidenceEvaluator
        # - DecisionTree
        
        return {
            "prosecution_paths_generated": 3,
            "recommended_path": "DOJ Criminal Referral",
            "success_probability": 0.72,
            "estimated_timeline_months": 18
        }
    
    async def _run_contradiction_detection(
        self,
        result: InvestigationResult,
        config: InvestigationConfig
    ) -> Dict[str, Any]:
        """Execute Phase 6: Contradiction Detection."""
        logger.info("Executing Phase 6: Contradiction Detection")
        
        # In a full implementation, this would use:
        # - OmniscientContradictionDetector
        # - DeBERTa NLI Model
        # - ContradictionNetwork
        
        return {
            "statements_analyzed": 200,
            "contradictions_detected": 5,
            "high_severity_contradictions": 2,
            "contradiction_networks": 1
        }
    
    async def _run_reporting(
        self,
        result: InvestigationResult,
        config: InvestigationConfig
    ) -> Dict[str, Any]:
        """Execute Phase 7: Reporting."""
        logger.info("Executing Phase 7: Reporting")
        
        # In a full implementation, this would use:
        # - ProsecutionReportGenerator
        # - VisualizationEngine
        # - RegulatoryFormGenerator
        # - HTMLDashboardGenerator
        
        return {
            "reports_generated": 3,
            "report_types": ["pdf", "html", "json"],
            "visualizations_created": 5
        }
    
    def _aggregate_results(self, result: InvestigationResult) -> Dict[str, Any]:
        """Aggregate results from all phases into summary."""
        summary: Dict[str, Any] = {
            "overall": {
                "phases_completed": len([
                    p for p in result.phase_results.values()
                    if p.status == InvestigationStatus.COMPLETED
                ]),
                "phases_failed": len([
                    p for p in result.phase_results.values()
                    if p.status == InvestigationStatus.FAILED
                ]),
                "total_duration_seconds": result.duration_seconds,
                "case_strength": "strong",  # Would be calculated
                "conviction_probability": 0.72  # Would be calculated
            },
            "phases": {}
        }
        
        for phase_name, phase_result in result.phase_results.items():
            summary["phases"][phase_name] = {
                "status": phase_result.status.value,
                "duration_seconds": phase_result.duration_seconds,
                "results": phase_result.results
            }
        
        return summary
    
    async def _generate_outputs(
        self,
        result: InvestigationResult,
        config: InvestigationConfig
    ) -> None:
        """Generate output files."""
        output_dir = Path(config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if config.generate_json:
            json_path = output_dir / f"investigation_{result.case_id}_{timestamp}.json"
            with open(json_path, 'w') as f:
                json.dump({
                    "case_id": result.case_id,
                    "target": result.target,
                    "status": result.status.value,
                    "summary": result.summary,
                    "phases": {
                        k: {
                            "status": v.status.value,
                            "results": v.results
                        }
                        for k, v in result.phase_results.items()
                    }
                }, f, indent=2, default=str)
            result.output_files.append(str(json_path))
            logger.info(f"Generated JSON report: {json_path}")
    
    async def get_investigation_status(self, case_id: str) -> Optional[InvestigationResult]:
        """Get status of an active investigation."""
        return self._active_investigations.get(case_id)
    
    async def cancel_investigation(self, case_id: str) -> bool:
        """Cancel an active investigation."""
        if case_id in self._active_investigations:
            self._active_investigations[case_id].status = InvestigationStatus.CANCELLED
            logger.info(f"Investigation {case_id} cancelled")
            return True
        return False
