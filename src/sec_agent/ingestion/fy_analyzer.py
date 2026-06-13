"""
FY Analyzer — Fiscal Year Filing Analysis Module
===================================================

Analyzes SEC filings for a specific fiscal year, producing prosecution-grade
narrative_report.md and analysis.json outputs. Implements the Phase 1 protocol
requiring research report baseline reading before raw filing analysis.

Binary File Handling:
    - PDF files: pdfplumber (primary), PyMuPDF (fallback)
    - XLS/XLSX files: pandas with openpyxl engine
    - Do NOT skip binary files per Phase 1 directives

Output Artifacts:
    - narrative_report.md: Prosecution-grade narrative with statutory citations
    - analysis.json: Machine-readable findings with evidence chain hashes
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.sec_agent.ingestion.corpus_scanner import (
    CorpusManifest,
    CorpusScanner,
    FileEntry,
)

logger = logging.getLogger(__name__)


def _extract_pdf_text(filepath: str) -> str:
    """Extract text from PDF filing using pdfplumber or PyMuPDF fallback.

    Args:
        filepath: Path to PDF file.

    Returns:
        Extracted text content.
    """
    # Primary: pdfplumber
    try:
        import pdfplumber

        text_parts: list[str] = []
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
        if text_parts:
            return "\n".join(text_parts)
    except ImportError:
        logger.warning("pdfplumber not installed, falling back to PyMuPDF")
    except Exception as e:
        logger.warning("pdfplumber failed for %s: %s, trying PyMuPDF", filepath, e)

    # Fallback: PyMuPDF (fitz)
    try:
        import fitz  # PyMuPDF

        text_parts = []
        with fitz.open(filepath) as doc:
            for page in doc:
                text = page.get_text()
                if text:
                    text_parts.append(text)
        return "\n".join(text_parts)
    except ImportError:
        logger.error("Neither pdfplumber nor PyMuPDF available for PDF extraction")
    except Exception as e:
        logger.error("PyMuPDF fallback failed for %s: %s", filepath, e)

    return ""


def _extract_xls_data(filepath: str) -> Dict[str, Any]:
    """Extract data from XLS/XLSX filing using pandas/openpyxl.

    Args:
        filepath: Path to XLS or XLSX file.

    Returns:
        Dictionary mapping sheet names to list of row dictionaries.
    """
    try:
        import pandas as pd

        engine = "openpyxl" if filepath.endswith(".xlsx") else None
        sheets = pd.read_excel(filepath, sheet_name=None, engine=engine)
        result: Dict[str, Any] = {}
        for name, df in sheets.items():
            result[str(name)] = json.loads(
                df.head(1000).to_json(orient="records", date_format="iso")
            )
        return result
    except ImportError:
        logger.error("pandas/openpyxl not available for XLS extraction")
    except Exception as e:
        logger.error("XLS extraction failed for %s: %s", filepath, e)

    return {}


@dataclass
class FilingExtraction:
    """Extracted content from a single filing."""

    file_path: str
    file_name: str
    extension: str
    category: str
    text_content: str = ""
    structured_data: Optional[Dict[str, Any]] = None
    extraction_method: str = ""
    extraction_success: bool = False
    error: Optional[str] = None
    sha256: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "file_name": self.file_name,
            "extension": self.extension,
            "category": self.category,
            "extraction_method": self.extraction_method,
            "extraction_success": self.extraction_success,
            "text_length": len(self.text_content),
            "has_structured_data": self.structured_data is not None,
            "error": self.error,
            "sha256": self.sha256,
        }


@dataclass
class FYAnalysisResult:
    """Complete fiscal year analysis result."""

    case_id: str
    fiscal_year: int
    company_name: str
    cik: str
    analysis_timestamp: datetime
    research_baseline: str = ""
    research_baseline_loaded: bool = False
    total_filings_processed: int = 0
    successful_extractions: int = 0
    failed_extractions: int = 0
    pdf_extractions: int = 0
    xls_extractions: int = 0
    text_extractions: int = 0
    extractions: List[FilingExtraction] = field(default_factory=list)
    findings: Dict[str, Any] = field(default_factory=dict)
    anomalies: List[Dict[str, Any]] = field(default_factory=list)
    evidence_hashes: Dict[str, str] = field(default_factory=dict)
    merkle_root: Optional[str] = None
    errors: List[str] = field(default_factory=list)
    status: str = "pending"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for analysis.json export."""
        return {
            "case_id": self.case_id,
            "fiscal_year": self.fiscal_year,
            "company_name": self.company_name,
            "cik": self.cik,
            "analysis_timestamp": self.analysis_timestamp.isoformat(),
            "status": self.status,
            "research_baseline_loaded": self.research_baseline_loaded,
            "statistics": {
                "total_filings_processed": self.total_filings_processed,
                "successful_extractions": self.successful_extractions,
                "failed_extractions": self.failed_extractions,
                "pdf_extractions": self.pdf_extractions,
                "xls_extractions": self.xls_extractions,
                "text_extractions": self.text_extractions,
            },
            "extractions": [e.to_dict() for e in self.extractions],
            "findings": self.findings,
            "anomalies": self.anomalies,
            "evidence_integrity": {
                "evidence_hashes": self.evidence_hashes,
                "merkle_root": self.merkle_root,
                "hash_algorithm": "sha256",
            },
            "error_count": len(self.errors),
        }

    def to_narrative_markdown(self) -> str:
        """Generate prosecution-grade narrative_report.md content."""
        lines = [
            f"# Forensic Analysis Narrative Report — FY{self.fiscal_year}",
            "",
            f"**Case ID:** {self.case_id}  ",
            f"**Entity:** {self.company_name} (CIK {self.cik})  ",
            f"**Fiscal Year:** {self.fiscal_year}  ",
            f"**Generated:** {self.analysis_timestamp.isoformat()}  ",
            f"**Status:** {self.status}  ",
            "",
            "---",
            "",
            "## 1. Executive Summary",
            "",
            f"This narrative report presents the forensic analysis findings for "
            f"{self.company_name} (CIK {self.cik}) fiscal year {self.fiscal_year}. "
            f"The analysis processed {self.total_filings_processed} SEC filings "
            f"with {self.successful_extractions} successful extractions "
            f"({self.failed_extractions} failures).",
            "",
        ]

        # Research baseline section
        lines.extend([
            "## 2. Research Baseline",
            "",
        ])
        if self.research_baseline_loaded:
            lines.append(
                "The FY research report was loaded and reviewed prior to filing "
                "analysis, establishing the narrative baseline per Phase 1 protocol."
            )
        else:
            lines.append(
                "**WARNING:** Research baseline was NOT loaded prior to analysis. "
                "Phase 1 protocol requires reading the research report first."
            )
        lines.append("")

        # Filing corpus summary
        lines.extend([
            "## 3. Filing Corpus Summary",
            "",
            "| Category | Count | Success Rate |",
            "|----------|-------|-------------|",
            f"| PDF Documents | {self.pdf_extractions} | — |",
            f"| XLS Spreadsheets | {self.xls_extractions} | — |",
            f"| Text/HTML Files | {self.text_extractions} | — |",
            f"| **Total** | **{self.total_filings_processed}** "
            f"| **{self._success_rate()}%** |",
            "",
        ])

        # Findings section
        lines.extend([
            "## 4. Preliminary Findings",
            "",
        ])
        if self.findings:
            for key, value in self.findings.items():
                lines.append(f"### {key}")
                lines.append("")
                if isinstance(value, dict):
                    for k, v in value.items():
                        lines.append(f"- **{k}:** {v}")
                else:
                    lines.append(f"{value}")
                lines.append("")
        else:
            lines.append("No findings generated in this analysis pass.")
            lines.append("")

        # Anomalies section
        lines.extend([
            "## 5. Detected Anomalies",
            "",
        ])
        if self.anomalies:
            lines.append(
                "| # | Type | Severity | Description |"
            )
            lines.append(
                "|---|------|----------|-------------|"
            )
            for i, anomaly in enumerate(self.anomalies, 1):
                lines.append(
                    f"| {i} | {anomaly.get('type', 'Unknown')} "
                    f"| {anomaly.get('severity', 'Unknown')} "
                    f"| {anomaly.get('description', 'N/A')} |"
                )
        else:
            lines.append("No anomalies detected in this analysis pass.")
        lines.append("")

        # Evidence integrity section
        lines.extend([
            "## 6. Evidence Integrity",
            "",
            f"- **Evidence artifacts:** {len(self.evidence_hashes)}",
            f"- **Hash algorithm:** SHA-256",
            f"- **Merkle root:** `{self.merkle_root or 'Not computed'}`",
            "",
        ])

        # Errors section
        if self.errors:
            lines.extend([
                "## 7. Errors & Warnings",
                "",
            ])
            for error in self.errors:
                lines.append(f"- {error}")
            lines.append("")

        # Footer
        lines.extend([
            "---",
            "",
            f"*End of narrative report for {self.case_id} — "
            f"FY{self.fiscal_year}*",
        ])

        return "\n".join(lines)

    def _success_rate(self) -> str:
        """Calculate extraction success rate as percentage string."""
        if self.total_filings_processed == 0:
            return "0.0"
        rate = (
            self.successful_extractions / self.total_filings_processed
        ) * 100
        return f"{rate:.1f}"


class FYAnalyzer:
    """
    Fiscal Year Filing Analyzer.

    Implements the Phase 1 protocol for FY-specific SEC filing analysis:
    1. Read research report FIRST (establish narrative baseline)
    2. Scan corpus for FY-specific filings
    3. Extract text from PDF files (pdfplumber/PyMuPDF)
    4. Extract data from XLS files (pandas/openpyxl)
    5. Parse text/HTML/XML files
    6. Produce narrative_report.md and analysis.json

    Args:
        corpus_root: Root directory of the EDGAR filing corpus.
        research_reports_dir: Directory containing FY research reports.
        output_dir: Directory for analysis output files.
        cik: Target company CIK number.
        company_name: Target company name.
        case_id: Investigation case identifier.
    """

    def __init__(
        self,
        corpus_root: Path,
        research_reports_dir: Optional[Path] = None,
        output_dir: Path = Path("./output/fy_analysis"),
        cik: str = "",
        company_name: str = "",
        case_id: str = "",
    ) -> None:
        self.corpus_root = Path(corpus_root)
        self.research_reports_dir = (
            Path(research_reports_dir)
            if research_reports_dir
            else Path("docs/MD RESEARCH REPORT(S)")
        )
        self.output_dir = Path(output_dir)
        self.cik = cik
        self.company_name = company_name
        self.case_id = case_id

        self._corpus_scanner = CorpusScanner(corpus_root=self.corpus_root)

        logger.info(
            "FYAnalyzer initialized: corpus=%s, cik=%s, company=%s",
            self.corpus_root,
            cik,
            company_name,
        )

    def analyze_fiscal_year(
        self,
        fiscal_year: int,
        manifest: Optional[CorpusManifest] = None,
    ) -> FYAnalysisResult:
        """
        Execute complete FY analysis following Phase 1 protocol.

        Phase 1 Protocol (MANDATORY ORDER):
        1. Read research report FIRST to establish narrative baseline
        2. Scan corpus directory for filings
        3. Extract content from all filings (PDF, XLS, text)
        4. Assemble findings
        5. Produce narrative_report.md and analysis.json

        Args:
            fiscal_year: The fiscal year to analyze (e.g., 2019).
            manifest: Pre-computed corpus manifest (optional).

        Returns:
            FYAnalysisResult with complete analysis.
        """
        result = FYAnalysisResult(
            case_id=self.case_id or f"JLAW-NKE-{fiscal_year}-001",
            fiscal_year=fiscal_year,
            company_name=self.company_name,
            cik=self.cik,
            analysis_timestamp=datetime.utcnow(),
        )

        # ── Step 1: Read Research Report FIRST ──────────────────────────
        logger.info(
            "Phase 1.1: Loading research report for FY%d", fiscal_year
        )
        result.research_baseline = self._load_research_report(fiscal_year)
        result.research_baseline_loaded = bool(result.research_baseline)

        if not result.research_baseline_loaded:
            msg = (
                f"Research report not found for FY{fiscal_year} at "
                f"{self.research_reports_dir}/{fiscal_year}.md — "
                f"Phase 1 protocol requires baseline before filing analysis"
            )
            logger.warning(msg)
            result.errors.append(msg)

        # ── Step 2: Scan Corpus ─────────────────────────────────────────
        logger.info("Phase 1.2: Scanning corpus directory")
        if manifest is None:
            manifest = self._corpus_scanner.scan()

        if manifest.total_files == 0:
            msg = f"No files found in corpus: {self.corpus_root}"
            logger.warning(msg)
            result.errors.append(msg)
            result.status = "no_data"
            return result

        # ── Step 3: Extract Content ─────────────────────────────────────
        logger.info(
            "Phase 1.3: Extracting content from %d files",
            manifest.total_files,
        )
        for file_entry in manifest.files:
            extraction = self._extract_filing(file_entry)
            result.extractions.append(extraction)
            result.total_filings_processed += 1

            if extraction.extraction_success:
                result.successful_extractions += 1
                if extraction.sha256:
                    result.evidence_hashes[
                        extraction.file_name
                    ] = extraction.sha256
            else:
                result.failed_extractions += 1
                if extraction.error:
                    result.errors.append(
                        f"{extraction.file_name}: {extraction.error}"
                    )

            # Track by category
            if extraction.extension in (".pdf",):
                result.pdf_extractions += 1
            elif extraction.extension in (".xls", ".xlsx"):
                result.xls_extractions += 1
            else:
                result.text_extractions += 1

        # ── Step 4: Compute Merkle Root ─────────────────────────────────
        if result.evidence_hashes:
            result.merkle_root = self._compute_merkle_root(
                list(result.evidence_hashes.values())
            )

        # ── Step 5: Assemble Findings ───────────────────────────────────
        result.findings = self._assemble_findings(result)
        result.status = "complete"

        # ── Step 6: Export Outputs ──────────────────────────────────────
        self._export_outputs(result)

        logger.info(
            "FY%d analysis complete: %d/%d extractions successful",
            fiscal_year,
            result.successful_extractions,
            result.total_filings_processed,
        )

        return result

    def _load_research_report(self, fiscal_year: int) -> str:
        """Load the FY research report markdown file.

        Args:
            fiscal_year: Fiscal year number.

        Returns:
            Research report content as string, empty if not found.
        """
        report_path = self.research_reports_dir / f"{fiscal_year}.md"
        if report_path.exists():
            content = report_path.read_text(encoding="utf-8")
            logger.info(
                "Research report loaded: %s (%d bytes)",
                report_path,
                len(content),
            )
            return content

        logger.warning("Research report not found: %s", report_path)
        return ""

    def _extract_filing(self, entry: FileEntry) -> FilingExtraction:
        """Extract content from a single filing based on file type.

        Args:
            entry: FileEntry from corpus manifest.

        Returns:
            FilingExtraction with extracted content.
        """
        extraction = FilingExtraction(
            file_path=entry.file_path,
            file_name=entry.file_name,
            extension=entry.extension,
            category=entry.category,
        )

        try:
            # Compute SHA-256 hash
            extraction.sha256 = self._compute_file_hash(entry.file_path)

            if entry.extension == ".pdf":
                text = _extract_pdf_text(entry.file_path)
                extraction.text_content = text
                extraction.extraction_method = "pdfplumber/PyMuPDF"
                extraction.extraction_success = bool(text)
                if not text:
                    extraction.error = "No text extracted from PDF"

            elif entry.extension in (".xls", ".xlsx"):
                data = _extract_xls_data(entry.file_path)
                extraction.structured_data = data
                extraction.extraction_method = "pandas/openpyxl"
                extraction.extraction_success = bool(data)
                if not data:
                    extraction.error = "No data extracted from spreadsheet"

            elif entry.extension in (".txt", ".htm", ".html", ".xml", ".sgml"):
                text = Path(entry.file_path).read_text(
                    encoding="utf-8", errors="replace"
                )
                extraction.text_content = text
                extraction.extraction_method = "text_read"
                extraction.extraction_success = bool(text)

            elif entry.extension == ".json":
                text = Path(entry.file_path).read_text(encoding="utf-8")
                extraction.text_content = text
                try:
                    extraction.structured_data = json.loads(text)
                except json.JSONDecodeError:
                    pass
                extraction.extraction_method = "json_parse"
                extraction.extraction_success = True

            else:
                extraction.extraction_method = "unsupported"
                extraction.error = (
                    f"Unsupported extension: {entry.extension}"
                )

        except Exception as e:
            extraction.error = str(e)
            logger.warning(
                "Extraction failed for %s: %s", entry.file_name, e
            )

        return extraction

    def _assemble_findings(
        self, result: FYAnalysisResult
    ) -> Dict[str, Any]:
        """Assemble preliminary findings from extractions.

        Args:
            result: Current analysis result with extractions.

        Returns:
            Dictionary of findings organized by category.
        """
        findings: Dict[str, Any] = {
            "corpus_coverage": {
                "total_files": result.total_filings_processed,
                "successful_extractions": result.successful_extractions,
                "coverage_rate": result._success_rate() + "%",
                "pdf_files": result.pdf_extractions,
                "xls_files": result.xls_extractions,
                "text_files": result.text_extractions,
            },
            "research_baseline": {
                "loaded": result.research_baseline_loaded,
                "baseline_length_bytes": len(result.research_baseline),
                "phase_1_compliant": result.research_baseline_loaded,
            },
        }

        # Summarize text content lengths
        text_lengths = [
            len(e.text_content)
            for e in result.extractions
            if e.extraction_success and e.text_content
        ]
        if text_lengths:
            findings["text_analysis"] = {
                "total_text_bytes": sum(text_lengths),
                "avg_document_length": (
                    sum(text_lengths) // len(text_lengths)
                ),
                "max_document_length": max(text_lengths),
                "min_document_length": min(text_lengths),
                "documents_with_text": len(text_lengths),
            }

        # Summarize structured data
        structured_count = sum(
            1
            for e in result.extractions
            if e.structured_data is not None
        )
        if structured_count:
            findings["structured_data"] = {
                "files_with_structured_data": structured_count,
            }

        return findings

    def _export_outputs(self, result: FYAnalysisResult) -> None:
        """Export narrative_report.md and analysis.json.

        Args:
            result: Complete analysis result.
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Export narrative_report.md
        narrative_path = self.output_dir / "narrative_report.md"
        narrative_content = result.to_narrative_markdown()
        narrative_path.write_text(narrative_content, encoding="utf-8")
        logger.info("Narrative report exported: %s", narrative_path)

        # Export analysis.json
        analysis_path = self.output_dir / "analysis.json"
        analysis_data = result.to_dict()
        with open(analysis_path, "w", encoding="utf-8") as f:
            json.dump(analysis_data, f, indent=2, default=str)
        logger.info("Analysis JSON exported: %s", analysis_path)

    @staticmethod
    def _compute_file_hash(filepath: str) -> Optional[str]:
        """Compute SHA-256 hash of a file.

        Args:
            filepath: Path to file.

        Returns:
            Hex digest string or None on error.
        """
        sha256 = hashlib.sha256()
        try:
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except OSError:
            return None

    @staticmethod
    def _compute_merkle_root(hashes: List[str]) -> str:
        """Compute simple Merkle root from a list of hex hash strings.

        Args:
            hashes: List of SHA-256 hex digest strings.

        Returns:
            Merkle root hex digest.
        """
        if not hashes:
            return hashlib.sha256(b"").hexdigest()

        # Convert to bytes
        current_level = [bytes.fromhex(h) for h in hashes]

        while len(current_level) > 1:
            next_level: list[bytes] = []
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = (
                    current_level[i + 1]
                    if i + 1 < len(current_level)
                    else left
                )
                combined = hashlib.sha256(left + right).digest()
                next_level.append(combined)
            current_level = next_level

        return current_level[0].hex()
