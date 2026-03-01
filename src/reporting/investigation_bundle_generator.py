"""
Investigation Bundle Generator
================================

The single entry-point that orchestrates production of the complete
JLAW investigation output bundle.

One call produces ALL of the following:

  NARRATIVE OUTPUTS
  ─────────────────
  investigative_article.md         — WSJ-style investigative article (Markdown)
  investigative_article.html       — Same article as self-contained HTML
  investigative_article.json       — Structured metadata + article body (JSON)
  discrepancy_report.md            — Public-statement vs SEC-filing contradiction ledger (Markdown)
  discrepancy_report.html          — Ditto, as HTML
  discrepancy_report.json          — Ditto, as structured JSON

  MACHINE-READABLE LOGS
  ─────────────────────
  forensic_machine_log.json        — Full provenance-annotated log (all findings)
  forensic_log_manifest.json       — Manifest header only (no entries)
  forensic_ecs_stream.json         — Elastic Common Schema SIEM-ready stream
  forensic_ndjson.log              — One JSON object per line (NDJSON / JSON Lines)

  NETWORK VISUALISATIONS
  ──────────────────────
  financial_network_map.html       — Interactive Plotly financial network map
  financial_network_map.png        — Static PNG for PDF embedding
  financial_network_map.json       — Structured edge/node data (JSON)

  BUNDLE MANIFEST
  ───────────────
  bundle_manifest.json             — Complete inventory of all generated files
                                     with SHA-256 hashes and metadata

Usage::

    from src.reporting.investigation_bundle_generator import InvestigationBundleGenerator

    gen = InvestigationBundleGenerator()
    manifest = gen.generate_bundle(
        company_name="NIKE, Inc.",
        cik="320187",
        analysis_results=analysis_results_dict,
        output_dir=Path("output/NKE_2019/investigation_bundle"),
        analysis_period="FY 2019",
        public_statements=optional_public_statements_list,
        extra_data=optional_extra_data_dict,
    )
    print(f"Bundle generated: {len(manifest['files'])} files")
"""
from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .investigative_article_generator import InvestigativeArticleGenerator
from .public_discrepancy_engine import PublicDiscrepancyEngine
from .machine_log_generator import MachineLogGenerator
from .visualizations.financial_network_map import FinancialNetworkMapper

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# DATA MODELS
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class GeneratedFile:
    """Metadata for a single generated output file."""
    filename: str
    relative_path: str
    absolute_path: str
    file_type: str           # "narrative" | "machine_log" | "visualization" | "manifest"
    format: str              # "json" | "markdown" | "html" | "png" | "ndjson"
    size_bytes: int = 0
    sha256: str = ""
    generated_at: str = ""
    description: str = ""

    def compute_hash(self) -> str:
        """Compute SHA-256 of the file contents."""
        p = Path(self.absolute_path)
        if not p.exists():
            return ""
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        self.sha256 = h
        self.size_bytes = p.stat().st_size
        return h


@dataclass
class BundleManifest:
    """
    Complete inventory of the investigation bundle.

    Includes all generated files with integrity hashes, metadata, and
    a top-level summary of the forensic findings.
    """
    manifest_id: str
    company_name: str
    cik: str
    analysis_period: str
    generated_at: str
    output_dir: str

    # Files
    files: List[GeneratedFile] = field(default_factory=list)

    # Summary metrics (mirrors analysis_results top-level stats)
    total_violations: int = 0
    critical_violations: int = 0
    high_violations: int = 0
    total_penalty_exposure_usd: float = 0.0
    insiders_identified: int = 0

    # Component run status
    components_run: List[str] = field(default_factory=list)
    components_skipped: List[str] = field(default_factory=list)

    # Bundle integrity
    bundle_sha256: str = ""

    def add_file(self, f: GeneratedFile) -> None:
        f.compute_hash()
        self.files.append(f)

    def seal(self) -> str:
        """Compute a SHA-256 over all file hashes (bundle integrity seal)."""
        payload = ",".join(f.sha256 for f in self.files).encode()
        self.bundle_sha256 = hashlib.sha256(payload).hexdigest()
        return self.bundle_sha256

    def to_dict(self) -> Dict[str, Any]:
        return {
            "manifest_id": self.manifest_id,
            "company_name": self.company_name,
            "cik": self.cik,
            "analysis_period": self.analysis_period,
            "generated_at": self.generated_at,
            "output_dir": self.output_dir,
            "summary": {
                "total_violations": self.total_violations,
                "critical_violations": self.critical_violations,
                "high_violations": self.high_violations,
                "total_penalty_exposure_usd": self.total_penalty_exposure_usd,
                "insiders_identified": self.insiders_identified,
                "total_files": len(self.files),
            },
            "components_run": self.components_run,
            "components_skipped": self.components_skipped,
            "integrity": {
                "bundle_sha256": self.bundle_sha256,
                "sealed_at": datetime.utcnow().isoformat() + "Z",
            },
            "files": [
                {
                    "filename": f.filename,
                    "relative_path": f.relative_path,
                    "file_type": f.file_type,
                    "format": f.format,
                    "size_bytes": f.size_bytes,
                    "sha256": f.sha256,
                    "generated_at": f.generated_at,
                    "description": f.description,
                }
                for f in self.files
            ],
        }


# ═══════════════════════════════════════════════════════════════════════════
# BUNDLE GENERATOR
# ═══════════════════════════════════════════════════════════════════════════


class InvestigationBundleGenerator:
    """
    Orchestrates all JLAW output generators into a single investigation bundle.

    This is the recommended entry-point for producing the full output suite
    after a forensic analysis run.

    Usage::

        gen = InvestigationBundleGenerator()
        manifest = gen.generate_bundle(
            company_name="NIKE, Inc.",
            cik="320187",
            analysis_results=analysis_results_dict,
            output_dir=Path("output/NKE_2019/investigation_bundle"),
            analysis_period="FY 2019",
        )
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self._article_gen = InvestigativeArticleGenerator()
        self._discrepancy_gen = PublicDiscrepancyEngine()
        self._machine_log_gen = MachineLogGenerator()
        self._network_mapper = FinancialNetworkMapper()

    # ── public API ──────────────────────────────────────────────────────────

    def generate_bundle(
        self,
        company_name: str,
        cik: str,
        analysis_results: Dict[str, Any],
        output_dir: Path,
        analysis_period: str = "",
        public_statements: Optional[List[Dict[str, Any]]] = None,
        extra_data: Optional[Dict[str, Any]] = None,
        skip_visualizations: bool = False,
    ) -> BundleManifest:
        """
        Generate the complete investigation bundle.

        Args:
            company_name: Company display name.
            cik: SEC CIK number.
            analysis_results: Full forensic analysis results dict from the pipeline.
            output_dir: Directory where all output files will be written.
            analysis_period: Human-readable period label (e.g. "FY 2019").
            public_statements: Optional pre-collected public statements to cross-reference.
            extra_data: Optional supplementary data (enhanced results, FSL, etc.).
            skip_visualizations: If True, skip network visualisation generation
                                  (useful for CI/CD environments without display).

        Returns:
            BundleManifest with complete file inventory and integrity hashes.
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        now_iso = datetime.utcnow().isoformat() + "Z"
        manifest_id = hashlib.sha256(
            f"{cik}{company_name}{now_iso}".encode()
        ).hexdigest()[:16].upper()

        manifest = BundleManifest(
            manifest_id=manifest_id,
            company_name=company_name,
            cik=cik,
            analysis_period=analysis_period or "N/A",
            generated_at=now_iso,
            output_dir=str(output_dir),
        )

        # Populate top-level stats
        violations = analysis_results.get("violations", [])
        manifest.total_violations = analysis_results.get(
            "total_violations", len(violations)
        )
        manifest.critical_violations = analysis_results.get("critical_alerts", 0)
        manifest.high_violations = analysis_results.get("high_alerts", 0)
        manifest.total_penalty_exposure_usd = sum(
            v.get("estimated_penalty", 0) for v in violations
        )
        manifest.insiders_identified = len(
            {v.get("reporting_owner") or v.get("actor") for v in violations} - {"", None}
        )

        self.logger.info(
            "Starting investigation bundle generation for %s (CIK %s)",
            company_name,
            cik,
        )

        # ── PHASE 1: Discrepancy Analysis ────────────────────────────────
        discrepancy_report = self._run_discrepancy_analysis(
            company_name, cik, analysis_results, analysis_period,
            public_statements, manifest, output_dir
        )

        # ── PHASE 2: Investigative Article ───────────────────────────────
        self._run_article_generation(
            company_name, cik, analysis_results, analysis_period,
            discrepancy_report, manifest, output_dir
        )

        # ── PHASE 3: Machine-Readable Logs ───────────────────────────────
        self._run_machine_log_generation(
            company_name, cik, analysis_results, analysis_period,
            extra_data, manifest, output_dir
        )

        # ── PHASE 4: Network Visualisations ──────────────────────────────
        if not skip_visualizations:
            self._run_network_visualisation(
                company_name, cik, analysis_results, analysis_period,
                manifest, output_dir
            )
        else:
            manifest.components_skipped.append("financial_network_visualisation")
            self.logger.info("Skipping network visualisation (skip_visualizations=True)")

        # ── PHASE 5: Write Bundle Manifest ───────────────────────────────
        manifest.seal()
        manifest_path = output_dir / "bundle_manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as fh:
            json.dump(manifest.to_dict(), fh, indent=2, default=str)

        self.logger.info(
            "Investigation bundle complete: %d files → %s",
            len(manifest.files),
            output_dir,
        )
        return manifest

    # ── phase runners ────────────────────────────────────────────────────────

    def _run_discrepancy_analysis(
        self,
        company_name: str,
        cik: str,
        analysis_results: Dict[str, Any],
        analysis_period: str,
        public_statements: Optional[List[Dict[str, Any]]],
        manifest: BundleManifest,
        output_dir: Path,
    ) -> Any:
        """Run public discrepancy analysis and export all formats."""
        component = "public_discrepancy_analysis"
        try:
            report = self._discrepancy_gen.analyze(
                company_name=company_name,
                cik=cik,
                analysis_results=analysis_results,
                public_statements=public_statements,
                analysis_period=analysis_period,
            )

            for fmt, method, file_type, description in [
                (
                    "json",
                    lambda p: self._discrepancy_gen.export_json(report, p),
                    "narrative",
                    "Structured discrepancy ledger — public statements vs SEC filings (JSON)",
                ),
                (
                    "md",
                    lambda p: self._discrepancy_gen.export_markdown(report, p),
                    "narrative",
                    "Public statement vs SEC filing contradiction ledger (Markdown)",
                ),
                (
                    "html",
                    lambda p: self._discrepancy_gen.export_html(report, p),
                    "narrative",
                    "Interactive discrepancy report with severity colour-coding (HTML)",
                ),
            ]:
                path = output_dir / f"discrepancy_report.{fmt}"
                try:
                    method(path)
                    manifest.add_file(
                        GeneratedFile(
                            filename=path.name,
                            relative_path=str(path.relative_to(output_dir)),
                            absolute_path=str(path),
                            file_type=file_type,
                            format=fmt,
                            generated_at=datetime.utcnow().isoformat() + "Z",
                            description=description,
                        )
                    )
                except Exception as e:
                    self.logger.warning("Discrepancy %s export failed: %s", fmt, e)

            manifest.components_run.append(component)
            return report

        except Exception as e:
            self.logger.error("Discrepancy analysis failed: %s", e)
            manifest.components_skipped.append(component)
            return None

    def _run_article_generation(
        self,
        company_name: str,
        cik: str,
        analysis_results: Dict[str, Any],
        analysis_period: str,
        discrepancy_report: Any,
        manifest: BundleManifest,
        output_dir: Path,
    ) -> None:
        """Run investigative article generation and export all formats."""
        component = "investigative_article_generation"
        try:
            article = self._article_gen.generate(
                company_name=company_name,
                cik=cik,
                analysis_results=analysis_results,
                analysis_period=analysis_period,
                discrepancy_report=discrepancy_report,
            )

            for fmt, method, file_type, description in [
                (
                    "md",
                    lambda p: self._article_gen.export_markdown(article, p),
                    "narrative",
                    "Wall Street Journal-style investigative article (Markdown)",
                ),
                (
                    "html",
                    lambda p: self._article_gen.export_html(article, p),
                    "narrative",
                    "Fully-styled self-contained investigative article (HTML)",
                ),
                (
                    "json",
                    lambda p: self._article_gen.export_json(article, p),
                    "narrative",
                    "Structured article content with evidence register (JSON)",
                ),
            ]:
                path = output_dir / f"investigative_article.{fmt}"
                try:
                    method(path)
                    manifest.add_file(
                        GeneratedFile(
                            filename=path.name,
                            relative_path=str(path.relative_to(output_dir)),
                            absolute_path=str(path),
                            file_type=file_type,
                            format=fmt,
                            generated_at=datetime.utcnow().isoformat() + "Z",
                            description=description,
                        )
                    )
                except Exception as e:
                    self.logger.warning("Article %s export failed: %s", fmt, e)

            manifest.components_run.append(component)

        except Exception as e:
            self.logger.error("Article generation failed: %s", e)
            manifest.components_skipped.append(component)

    def _run_machine_log_generation(
        self,
        company_name: str,
        cik: str,
        analysis_results: Dict[str, Any],
        analysis_period: str,
        extra_data: Optional[Dict[str, Any]],
        manifest: BundleManifest,
        output_dir: Path,
    ) -> None:
        """Run machine log generation and export all formats."""
        component = "machine_log_generation"
        try:
            log = self._machine_log_gen.generate(
                company_name=company_name,
                cik=cik,
                analysis_results=analysis_results,
                analysis_period=analysis_period,
                extra_data=extra_data,
            )

            for filename, method, fmt, file_type, description in [
                (
                    "forensic_machine_log.json",
                    lambda p: self._machine_log_gen.export_full_log(log, p),
                    "json",
                    "machine_log",
                    "Full provenance-annotated forensic log (all findings)",
                ),
                (
                    "forensic_log_manifest.json",
                    lambda p: self._machine_log_gen.export_manifest(log, p),
                    "json",
                    "machine_log",
                    "Log manifest header with integrity seal (no entries)",
                ),
                (
                    "forensic_ecs_stream.json",
                    lambda p: self._machine_log_gen.export_ecs_stream(log, p),
                    "json",
                    "machine_log",
                    "Elastic Common Schema stream for SIEM ingestion",
                ),
                (
                    "forensic_ndjson.log",
                    lambda p: self._machine_log_gen.export_ndjson(log, p),
                    "ndjson",
                    "machine_log",
                    "NDJSON / JSON Lines format (one entry per line)",
                ),
            ]:
                path = output_dir / filename
                try:
                    method(path)
                    manifest.add_file(
                        GeneratedFile(
                            filename=path.name,
                            relative_path=str(path.relative_to(output_dir)),
                            absolute_path=str(path),
                            file_type=file_type,
                            format=fmt,
                            generated_at=datetime.utcnow().isoformat() + "Z",
                            description=description,
                        )
                    )
                except Exception as e:
                    self.logger.warning("Machine log %s export failed: %s", filename, e)

            manifest.components_run.append(component)

        except Exception as e:
            self.logger.error("Machine log generation failed: %s", e)
            manifest.components_skipped.append(component)

    def _run_network_visualisation(
        self,
        company_name: str,
        cik: str,
        analysis_results: Dict[str, Any],
        analysis_period: str,
        manifest: BundleManifest,
        output_dir: Path,
    ) -> None:
        """Run financial network mapping and export all formats."""
        component = "financial_network_visualisation"
        try:
            net = self._network_mapper.build_network(
                company_name=company_name,
                cik=cik,
                analysis_results=analysis_results,
                analysis_period=analysis_period,
            )

            # JSON (always)
            json_path = output_dir / "financial_network_map.json"
            try:
                self._network_mapper.export_json(net, json_path)
                manifest.add_file(
                    GeneratedFile(
                        filename=json_path.name,
                        relative_path=str(json_path.relative_to(output_dir)),
                        absolute_path=str(json_path),
                        file_type="visualization",
                        format="json",
                        generated_at=datetime.utcnow().isoformat() + "Z",
                        description="Financial network edge/node graph data (JSON)",
                    )
                )
            except Exception as e:
                self.logger.warning("Network JSON export failed: %s", e)

            # Interactive HTML
            html_path = output_dir / "financial_network_map.html"
            try:
                result = self._network_mapper.export_interactive_html(net, html_path)
                if result:
                    manifest.add_file(
                        GeneratedFile(
                            filename=html_path.name,
                            relative_path=str(html_path.relative_to(output_dir)),
                            absolute_path=str(html_path),
                            file_type="visualization",
                            format="html",
                            generated_at=datetime.utcnow().isoformat() + "Z",
                            description=(
                                "Interactive Plotly financial relationship network map (HTML)"
                            ),
                        )
                    )
            except Exception as e:
                self.logger.warning("Network HTML export failed: %s", e)

            # Static PNG
            png_path = output_dir / "financial_network_map.png"
            try:
                result = self._network_mapper.export_static_png(net, png_path)
                if result:
                    manifest.add_file(
                        GeneratedFile(
                            filename=png_path.name,
                            relative_path=str(png_path.relative_to(output_dir)),
                            absolute_path=str(png_path),
                            file_type="visualization",
                            format="png",
                            generated_at=datetime.utcnow().isoformat() + "Z",
                            description=(
                                "Static financial network map for PDF embedding (PNG)"
                            ),
                        )
                    )
            except Exception as e:
                self.logger.warning("Network PNG export failed: %s", e)

            manifest.components_run.append(component)

        except Exception as e:
            self.logger.error("Network visualisation failed: %s", e)
            manifest.components_skipped.append(component)

    # ── convenience method ───────────────────────────────────────────────────

    @staticmethod
    def load_analysis_results(path: Path) -> Dict[str, Any]:
        """
        Load analysis results from a JSON file (e.g. bundle/analysis_results.json).

        Args:
            path: Path to the analysis_results.json file.

        Returns:
            Parsed dict.
        """
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
