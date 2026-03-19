"""
Master Report Generator — Archival Prosecution Dossier
========================================================

Wires to JLAW's production-grade ProsecutorialDossierGenerator (1,749 LOC)
and ForensicDossierGenerator (785 LOC) for generating the master archival
dossier — a 500+ page courtroom-ready compilation.

Architecture:
    Track B: Master Archival Dossier
        → ProsecutorialDossierGenerator (7-section DOJ/SEC dossier)
        → ForensicDossierGenerator (visual PDF with charts)
        → Unified master document with cross-references

Source Integration:
    JLAW prosecutorial_dossier_generator.py (1,749 LOC) → 7-section dossier
    JLAW forensic_dossier.py (785 LOC) → Visual forensic PDF
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.reporting.prosecutorial_dossier_generator import (
    ProsecutorialDossierGenerator,
    ProsecutorialDossier,
)
from src.reporting.forensic_dossier import ForensicDossierGenerator
from src.reporting.investigation_bundle_generator import (
    InvestigationBundleGenerator,
    BundleManifest,
)

logger = logging.getLogger(__name__)


@dataclass
class MasterReportOutput:
    """Output from master report generation."""

    report_id: str
    case_id: str
    company_name: str
    cik: str
    generated_at: datetime
    prosecutorial_dossier: Optional[ProsecutorialDossier] = None
    forensic_dossier_path: Optional[Path] = None
    investigation_bundle: Optional[BundleManifest] = None
    output_paths: Dict[str, Path] = field(default_factory=dict)
    total_violations: int = 0
    total_pages_estimated: int = 0
    status: str = "generated"
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "report_id": self.report_id,
            "case_id": self.case_id,
            "company_name": self.company_name,
            "cik": self.cik,
            "generated_at": self.generated_at.isoformat(),
            "output_paths": {k: str(v) for k, v in self.output_paths.items()},
            "total_violations": self.total_violations,
            "total_pages_estimated": self.total_pages_estimated,
            "forensic_dossier_path": (
                str(self.forensic_dossier_path)
                if self.forensic_dossier_path
                else None
            ),
            "status": self.status,
            "error_count": len(self.errors),
        }


class MasterReportGenerator:
    """
    Generate the master archival prosecution dossier.

    Orchestrates JLAW's ProsecutorialDossierGenerator (7-section DOJ/SEC
    submission-ready dossier) and ForensicDossierGenerator (visual PDF
    with charts and evidence) into a unified master document.

    Also integrates the InvestigationBundleGenerator for complete
    evidence bundle packaging.

    Args:
        output_dir: Root output directory.
        bates_prefix: Bates stamping prefix (e.g., "JLAW-NKE").
        dossier_type: Dossier type classification.
        include_visual_dossier: Whether to generate visual PDF dossier.
        include_investigation_bundle: Whether to generate investigation bundle.
    """

    def __init__(
        self,
        output_dir: str = "./output/master_report",
        bates_prefix: Optional[str] = None,
        dossier_type: str = "DOJ_GRADE",
        include_visual_dossier: bool = True,
        include_investigation_bundle: bool = True,
    ) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.bates_prefix = bates_prefix
        self.dossier_type = dossier_type
        self.include_visual_dossier = include_visual_dossier
        self.include_investigation_bundle = include_investigation_bundle

        # Wire to JLAW production generators
        self._prosecutorial_gen = ProsecutorialDossierGenerator(
            output_dir=self.output_dir,
            bates_prefix=bates_prefix,
            dossier_type=dossier_type,
        )
        self._forensic_gen = ForensicDossierGenerator(
            output_dir=str(self.output_dir)
        )
        self._bundle_gen = InvestigationBundleGenerator()

        logger.info(
            "MasterReportGenerator initialized: output=%s, type=%s",
            self.output_dir,
            dossier_type,
        )

    async def generate_master_report(
        self,
        case_id: str,
        company_name: str,
        cik: str,
        node_results: Dict[str, Any],
        detection_results: Dict[str, Any],
        actor_profiles: Optional[List] = None,
        interrogation_packages: Optional[Dict] = None,
        statutory_bindings: Optional[List] = None,
        recursive_analysis: Optional[Any] = None,
        analysis_results: Optional[Dict[str, Any]] = None,
        output_formats: Optional[List[str]] = None,
        merkle_root: Optional[str] = None,
        analysis_period: str = "",
        public_statements: Optional[List[Dict]] = None,
        extra_data: Optional[Dict] = None,
    ) -> MasterReportOutput:
        """
        Generate the complete master archival dossier.

        Produces:
            1. Prosecutorial dossier (7-section DOJ/SEC submission)
            2. Visual forensic dossier (PDF with charts)
            3. Investigation bundle (complete evidence package)

        Args:
            case_id: Unique case identifier.
            company_name: Target company name.
            cik: Target company CIK.
            node_results: Results from JLAW's 16-node recursive pipeline.
            detection_results: Results from 23 detection patterns.
            actor_profiles: Extracted actor profiles (optional).
            interrogation_packages: Interrogation packages (optional).
            statutory_bindings: Statutory binding mappings (optional).
            recursive_analysis: Recursive analysis result (optional).
            analysis_results: Combined analysis results dict (optional).
            output_formats: Output format list (default: ["json", "markdown"]).
            merkle_root: Evidence chain Merkle root hash (optional).
            analysis_period: Analysis period string (e.g., "FY2019").
            public_statements: Public statement data for discrepancy analysis.
            extra_data: Additional data for bundle generation.

        Returns:
            MasterReportOutput with all generated files and metadata.
        """
        report_id = f"MASTER-{case_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        output = MasterReportOutput(
            report_id=report_id,
            case_id=case_id,
            company_name=company_name,
            cik=cik,
            generated_at=datetime.utcnow(),
        )

        # ── Component 1: Prosecutorial Dossier ──────────────────────────
        try:
            prosecutorial_dossier = await self._prosecutorial_gen.generate_dossier(
                case_id=case_id,
                company_name=company_name,
                cik=cik,
                node_results=node_results,
                detection_results=detection_results,
                actor_profiles=actor_profiles or [],
                interrogation_packages=interrogation_packages or {},
                statutory_bindings=statutory_bindings or [],
                recursive_analysis=recursive_analysis,
                output_formats=output_formats,
                merkle_root=merkle_root,
            )
            output.prosecutorial_dossier = prosecutorial_dossier
            output.total_violations = prosecutorial_dossier.total_violations
            logger.info(
                "Prosecutorial dossier generated: %d violations",
                prosecutorial_dossier.total_violations,
            )
        except Exception as e:
            logger.error("Prosecutorial dossier generation failed: %s", e)
            output.errors.append(f"Prosecutorial dossier: {e}")

        # ── Component 2: Visual Forensic Dossier ────────────────────────
        if self.include_visual_dossier and analysis_results:
            try:
                combined_results = {
                    **(analysis_results or {}),
                    "node_results": node_results,
                    "detection_results": detection_results,
                    "company_name": company_name,
                    "cik": cik,
                }
                forensic_path = self._forensic_gen.generate_dossier(
                    case_id=case_id,
                    company_name=company_name,
                    cik=cik,
                    analysis_results=combined_results,
                    output_format="pdf",
                    include_charts=True,
                )
                output.forensic_dossier_path = forensic_path
                output.output_paths["forensic_dossier_pdf"] = forensic_path
                logger.info("Visual forensic dossier generated: %s", forensic_path)
            except Exception as e:
                logger.error("Visual forensic dossier generation failed: %s", e)
                output.errors.append(f"Visual forensic dossier: {e}")

        # ── Component 3: Investigation Bundle ───────────────────────────
        if self.include_investigation_bundle:
            try:
                combined_for_bundle = {
                    **(analysis_results or {}),
                    "node_results": node_results,
                    "detection_results": detection_results,
                }
                bundle_manifest = self._bundle_gen.generate_bundle(
                    company_name=company_name,
                    cik=cik,
                    analysis_results=combined_for_bundle,
                    output_dir=self.output_dir / "bundle",
                    analysis_period=analysis_period,
                    public_statements=public_statements,
                    extra_data=extra_data,
                )
                output.investigation_bundle = bundle_manifest
                logger.info(
                    "Investigation bundle generated: %d files",
                    len(bundle_manifest.files),
                )
            except Exception as e:
                logger.error("Investigation bundle generation failed: %s", e)
                output.errors.append(f"Investigation bundle: {e}")

        # ── Estimate total pages ────────────────────────────────────────
        output.total_pages_estimated = self._estimate_pages(output)
        output.status = "success" if not output.errors else "partial"

        # ── Export manifest ─────────────────────────────────────────────
        manifest_path = self.output_dir / f"{report_id}_manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(output.to_dict(), f, indent=2, default=str)
        output.output_paths["manifest"] = manifest_path

        logger.info(
            "Master report generated: %s (%d violations, ~%d pages, %d errors)",
            report_id,
            output.total_violations,
            output.total_pages_estimated,
            len(output.errors),
        )

        return output

    @staticmethod
    def _estimate_pages(output: MasterReportOutput) -> int:
        """Estimate total page count for the master dossier."""
        pages = 0

        # Prosecutorial dossier: ~3 pages per violation + 20 pages overhead
        if output.prosecutorial_dossier:
            pages += output.total_violations * 3 + 20

        # Forensic dossier: ~50 pages for visual PDF
        if output.forensic_dossier_path:
            pages += 50

        # Investigation bundle: ~5 pages per component
        if output.investigation_bundle:
            pages += len(output.investigation_bundle.files) * 5

        return max(pages, 100)  # Minimum 100 pages
