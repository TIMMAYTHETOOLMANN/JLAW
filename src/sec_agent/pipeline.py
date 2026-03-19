"""
SEC-AGENT Pipeline — Unified Data Flow Orchestrator
======================================================

Connects the SEC-AGENT deployment platform with the JLAW forensic
analysis engine. Orchestrates the complete data flow from raw EDGAR
corpus ingestion through 16-node recursive analysis to report generation.

Unified Data Flow:
    SEC-AGENT raw corpus (2,254+ files, 469MB)
        │
        ├─→ CorpusScanner    → scan raw file tree
        ├─→ XBRLIndexer      → index Company Facts JSON
        ├─→ FilingClassifier  → classify by SEC filing type
        ├─→ CIKValidator      → validate target CIK
        │
        ├─→ JLAW 16-Node Pipeline
        │   └─→ UnifiedForensicOrchestrator (11 phases)
        │
        ├─→ Track A: Tactical Bundles
        │   ├── DOJReferralGenerator
        │   ├── SECBundleGenerator
        │   └── LegislativeBriefGenerator
        │
        └─→ Track B: Master Archival Dossier
            └── MasterReportGenerator
"""

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.sec_agent.filing_classifier import (
    FilingClassifier,
    ClassificationReport,
    FilingCategory,
)
from src.sec_agent.cik_validator import CIKValidator, CIKValidationResult
from src.sec_agent.ingestion.corpus_scanner import CorpusScanner, CorpusManifest
from src.sec_agent.ingestion.xbrl_indexer import XBRLIndexer, XBRLIndex
from src.sec_agent.reports.doj_referral import DOJReferralGenerator
from src.sec_agent.reports.master_report import MasterReportGenerator
from src.sec_agent.reports.sec_bundle import SECBundleGenerator
from src.sec_agent.reports.legislative_brief import LegislativeBriefGenerator

logger = logging.getLogger(__name__)


@dataclass
class PipelineStageResult:
    """Result from a single pipeline stage."""

    stage_name: str
    status: str  # "success", "partial", "skipped", "error"
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0
    output: Optional[Any] = None
    error: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "stage_name": self.stage_name,
            "status": self.status,
            "duration_seconds": round(self.duration_seconds, 2),
            "error": self.error,
            "metrics": self.metrics,
        }


@dataclass
class PipelineResult:
    """Complete pipeline execution result."""

    pipeline_id: str
    cik: str
    company_name: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str = "pending"
    stages: List[PipelineStageResult] = field(default_factory=list)
    total_files_scanned: int = 0
    total_files_classified: int = 0
    total_violations: int = 0
    total_reports_generated: int = 0
    output_dir: Optional[str] = None
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "pipeline_id": self.pipeline_id,
            "cik": self.cik,
            "company_name": self.company_name,
            "started_at": self.started_at.isoformat(),
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "status": self.status,
            "stages": [s.to_dict() for s in self.stages],
            "total_files_scanned": self.total_files_scanned,
            "total_files_classified": self.total_files_classified,
            "total_violations": self.total_violations,
            "total_reports_generated": self.total_reports_generated,
            "output_dir": self.output_dir,
            "error_count": len(self.errors),
        }


class SecAgentPipeline:
    """
    Unified SEC-AGENT → JLAW data flow orchestrator.

    Connects the SEC-AGENT EDGAR corpus with the JLAW 16-node
    recursive forensic analysis pipeline and report generators.

    Pipeline Stages:
        1. Corpus Scan         — Discover all raw EDGAR files
        2. XBRL Indexing       — Index Company Facts JSON
        3. CIK Validation      — Validate target company CIK
        4. Filing Classification — Classify files by SEC form type
        5. Pipeline Routing     — Route classified filings to JLAW nodes
        6. Report Generation   — Generate tactical and archival reports

    Args:
        corpus_root: Root directory of raw EDGAR filing corpus.
        xbrl_path: Path to CIK XBRL Company Facts JSON.
        cik: Target company CIK number.
        company_name: Target company name.
        output_dir: Root output directory.
        user_agent: SEC EDGAR API user agent string.
    """

    def __init__(
        self,
        corpus_root: Path,
        xbrl_path: Optional[Path] = None,
        cik: str = "",
        company_name: str = "",
        output_dir: Path = Path("./output/sec_agent"),
        user_agent: Optional[str] = None,
    ) -> None:
        self.corpus_root = Path(corpus_root)
        self.xbrl_path = xbrl_path
        self.cik = cik
        self.company_name = company_name
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.user_agent = user_agent

        # Pipeline components
        self._corpus_scanner = CorpusScanner(corpus_root=self.corpus_root)
        self._xbrl_indexer = XBRLIndexer(source_path=xbrl_path)
        self._cik_validator = CIKValidator(
            user_agent=user_agent,
            xbrl_index_path=xbrl_path,
        )
        self._filing_classifier = FilingClassifier(
            xbrl_index_path=xbrl_path,
            corpus_root=self.corpus_root,
            cik=cik,
            company_name=company_name,
        )

        # Report generators
        self._doj_generator = DOJReferralGenerator(
            output_dir=str(self.output_dir / "doj_referrals")
        )
        self._master_generator = MasterReportGenerator(
            output_dir=str(self.output_dir / "master_report")
        )
        self._sec_generator = SECBundleGenerator(
            output_dir=str(self.output_dir / "sec_bundles")
        )
        self._legislative_generator = LegislativeBriefGenerator(
            output_dir=str(self.output_dir / "legislative_briefs")
        )

        # State
        self._corpus_manifest: Optional[CorpusManifest] = None
        self._xbrl_index: Optional[XBRLIndex] = None
        self._cik_validation: Optional[CIKValidationResult] = None
        self._classification_report: Optional[ClassificationReport] = None

        logger.info(
            "SecAgentPipeline initialized: corpus=%s, cik=%s, company=%s",
            self.corpus_root,
            cik,
            company_name,
        )

    async def execute(
        self,
        skip_stages: Optional[List[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        fiscal_year: Optional[int] = None,
    ) -> PipelineResult:
        """
        Execute the complete SEC-AGENT → JLAW pipeline.

        Args:
            skip_stages: List of stage names to skip.
            start_date: Analysis start date filter.
            end_date: Analysis end date filter.
            fiscal_year: Specific fiscal year to analyze.

        Returns:
            PipelineResult with complete execution results.
        """
        pipeline_id = f"pipeline-{int(time.time())}"
        skip = set(skip_stages or [])

        result = PipelineResult(
            pipeline_id=pipeline_id,
            cik=self.cik,
            company_name=self.company_name,
            started_at=datetime.utcnow(),
            output_dir=str(self.output_dir),
        )

        # ── Stage 1: Corpus Scan ────────────────────────────────────────
        stage1 = await self._execute_stage(
            "corpus_scan",
            self._stage_corpus_scan,
            skip="corpus_scan" in skip,
        )
        result.stages.append(stage1)
        if stage1.status == "success" and stage1.output:
            result.total_files_scanned = stage1.output.total_files

        # ── Stage 2: XBRL Indexing ──────────────────────────────────────
        stage2 = await self._execute_stage(
            "xbrl_indexing",
            self._stage_xbrl_indexing,
            skip="xbrl_indexing" in skip,
        )
        result.stages.append(stage2)

        # ── Stage 3: CIK Validation ────────────────────────────────────
        stage3 = await self._execute_stage(
            "cik_validation",
            self._stage_cik_validation,
            skip="cik_validation" in skip,
        )
        result.stages.append(stage3)

        # ── Stage 4: Filing Classification ──────────────────────────────
        stage4 = await self._execute_stage(
            "filing_classification",
            self._stage_filing_classification,
            skip="filing_classification" in skip,
        )
        result.stages.append(stage4)
        if stage4.status == "success" and stage4.output:
            result.total_files_classified = stage4.output.classified_files

        # ── Stage 5: Pipeline Routing ───────────────────────────────────
        stage5 = await self._execute_stage(
            "pipeline_routing",
            lambda: self._stage_pipeline_routing(start_date, end_date),
            skip="pipeline_routing" in skip,
        )
        result.stages.append(stage5)

        # ── Finalize ────────────────────────────────────────────────────
        result.completed_at = datetime.utcnow()

        # Determine overall status
        error_stages = [s for s in result.stages if s.status == "error"]
        if error_stages:
            result.status = "partial" if len(error_stages) < len(result.stages) else "error"
            result.errors = [s.error for s in error_stages if s.error]
        else:
            result.status = "success"

        # Export pipeline result
        result_path = self.output_dir / f"{pipeline_id}_result.json"
        with open(result_path, "w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, indent=2, default=str)

        logger.info(
            "Pipeline %s completed: status=%s, %d files scanned, %d classified",
            pipeline_id,
            result.status,
            result.total_files_scanned,
            result.total_files_classified,
        )

        return result

    def get_classification_report(self) -> Optional[ClassificationReport]:
        """Get the filing classification report from the last pipeline run."""
        return self._classification_report

    def get_corpus_manifest(self) -> Optional[CorpusManifest]:
        """Get the corpus manifest from the last pipeline run."""
        return self._corpus_manifest

    def get_xbrl_index(self) -> Optional[XBRLIndex]:
        """Get the XBRL index from the last pipeline run."""
        return self._xbrl_index

    def get_node_routing(self) -> Dict[int, int]:
        """Get the node routing map (node_id → filing count)."""
        if self._classification_report:
            return self._classification_report.node_input_counts
        return {}

    # ── Pipeline stages ─────────────────────────────────────────────────

    async def _execute_stage(
        self,
        stage_name: str,
        stage_fn,
        skip: bool = False,
    ) -> PipelineStageResult:
        """Execute a single pipeline stage with timing and error handling."""
        stage = PipelineStageResult(
            stage_name=stage_name,
            status="pending",
            started_at=datetime.utcnow(),
        )

        if skip:
            stage.status = "skipped"
            stage.completed_at = datetime.utcnow()
            logger.info("Stage '%s' skipped", stage_name)
            return stage

        start = time.time()
        try:
            result = stage_fn()
            # Handle both sync and async
            if hasattr(result, "__await__"):
                result = await result

            stage.output = result
            stage.status = "success"
            logger.info("Stage '%s' completed successfully", stage_name)

        except Exception as e:
            stage.status = "error"
            stage.error = str(e)
            logger.error("Stage '%s' failed: %s", stage_name, e, exc_info=True)

        stage.duration_seconds = time.time() - start
        stage.completed_at = datetime.utcnow()
        return stage

    def _stage_corpus_scan(self) -> CorpusManifest:
        """Stage 1: Scan the raw EDGAR corpus directory."""
        manifest = self._corpus_scanner.scan()
        self._corpus_manifest = manifest

        # Export manifest
        manifest_path = self.output_dir / "corpus_manifest.json"
        self._corpus_scanner.export_manifest(manifest, manifest_path)

        return manifest

    def _stage_xbrl_indexing(self) -> Optional[XBRLIndex]:
        """Stage 2: Index XBRL Company Facts JSON."""
        if not self.xbrl_path or not self.xbrl_path.exists():
            logger.warning("No XBRL path configured, skipping indexing")
            return None

        index = self._xbrl_indexer.index()
        self._xbrl_index = index

        # Export index
        index_path = self.output_dir / "xbrl_index.json"
        self._xbrl_indexer.export_index(index, index_path)

        return index

    async def _stage_cik_validation(self) -> CIKValidationResult:
        """Stage 3: Validate target company CIK."""
        result = await self._cik_validator.validate(self.cik)
        self._cik_validation = result

        if not result.is_valid:
            logger.warning("CIK validation failed: %s", result.errors)

        return result

    def _stage_filing_classification(self) -> ClassificationReport:
        """Stage 4: Classify all corpus files by SEC filing type."""
        report = self._filing_classifier.classify_corpus()
        self._classification_report = report

        # Export classification report
        report_path = self.output_dir / "classification_report.json"
        self._filing_classifier.export_report(report, report_path)

        return report

    def _stage_pipeline_routing(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """Stage 5: Route classified filings to JLAW pipeline nodes."""
        if not self._classification_report:
            return {"error": "No classification report available"}

        routing = {}
        for node_id in range(1, 17):
            node_filings = self._filing_classifier.get_filings_for_node(
                self._classification_report, node_id
            )

            # Apply date filter
            if start_date or end_date:
                filtered = []
                for f in node_filings:
                    if f.filing_date:
                        if start_date and f.filing_date < start_date:
                            continue
                        if end_date and f.filing_date > end_date:
                            continue
                    filtered.append(f)
                node_filings = filtered

            routing[f"node_{node_id}"] = {
                "filing_count": len(node_filings),
                "categories": list({
                    f.category.value for f in node_filings
                }),
            }

        # Convert to SECFiling objects for JLAW pipeline
        sec_filings = self._filing_classifier.to_sec_filings(
            self._classification_report.classifications
        )

        routing["total_sec_filings"] = len(sec_filings)
        routing["node_summary"] = self._classification_report.node_input_counts

        return routing
