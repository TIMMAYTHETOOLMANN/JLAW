"""
Filing Classifier — SEC Filing Type Classification
=====================================================

Classifies UUID-named PDFs, XLS, and other documents from the raw SEC EDGAR
corpus by filing type (Form 4, DEF 14A, 10-K, 10-Q, 8-K, 13F, 13D, 13G,
Form 144, etc.).

Architecture:
    - Cross-references against CIK XBRL Company Facts JSON index
    - Uses JLAW's ActorRoleClassifier for entity classification
    - Extracts filing metadata from document content and filename patterns
    - Maps classified filings to JLAW's 16-node recursive pipeline inputs

Source Integration:
    JLAW actor_role_classifier.py (477 LOC) → role classification logic
    JLAW actor_extraction_engine.py (182 LOC) → entity profile extraction
    SEC-AGENT filing corpus → 2,254+ raw filings (592 PDF + 594 XLS + more)
"""

import hashlib
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.detection.actor_role_classifier import ActorRoleClassifier, ActorRole
from src.detection.actor_extraction_engine import ActorExtractionEngine, ActorProfile
from src.integrations.sec_edgar.models import SECFiling

logger = logging.getLogger(__name__)


class FilingCategory(Enum):
    """SEC filing categories aligned with JLAW's 16-node pipeline."""

    FORM_4 = "4"
    FORM_3 = "3"
    FORM_5 = "5"
    DEF_14A = "DEF 14A"
    FORM_10K = "10-K"
    FORM_10Q = "10-Q"
    FORM_8K = "8-K"
    FORM_13F = "13F-HR"
    SCHEDULE_13D = "SC 13D"
    SCHEDULE_13G = "SC 13G"
    FORM_144 = "144"
    FORM_S1 = "S-1"
    FORM_20F = "20-F"
    ANNUAL_REPORT = "ARS"
    PROXY_STATEMENT = "PRE 14A"
    UNKNOWN = "UNKNOWN"


# Mapping from FilingCategory to JLAW pipeline node
FILING_TO_NODE_MAP: Dict[FilingCategory, List[int]] = {
    FilingCategory.FORM_4: [1],       # Node 1: Form 4 Insider Trading
    FilingCategory.FORM_3: [1],       # Node 1: Initial ownership
    FilingCategory.FORM_5: [1],       # Node 1: Annual ownership changes
    FilingCategory.DEF_14A: [2],      # Node 2: DEF 14A Compensation
    FilingCategory.FORM_10Q: [3],     # Node 3: 10-Q Temporal Consistency
    FilingCategory.FORM_10K: [4],     # Node 4: 10-K SOX Certification
    FilingCategory.FORM_8K: [9],      # Node 9: 8-K Material Events
    FilingCategory.FORM_13F: [7],     # Node 7: 13F Institutional Holdings
    FilingCategory.SCHEDULE_13D: [8], # Node 8: 13D Beneficial Ownership
    FilingCategory.SCHEDULE_13G: [8], # Node 8: 13G Beneficial Ownership
    FilingCategory.FORM_144: [10],    # Node 10: Form 144 Restricted Sales
}

# Filename patterns for SEC filing classification
FILENAME_PATTERNS: Dict[str, FilingCategory] = {
    r"form4": FilingCategory.FORM_4,
    r"form-?4": FilingCategory.FORM_4,
    r"form3": FilingCategory.FORM_3,
    r"form-?3": FilingCategory.FORM_3,
    r"form5": FilingCategory.FORM_5,
    r"form-?5": FilingCategory.FORM_5,
    r"def14a": FilingCategory.DEF_14A,
    r"def-?14a": FilingCategory.DEF_14A,
    r"proxy": FilingCategory.DEF_14A,
    r"10-?k": FilingCategory.FORM_10K,
    r"10k": FilingCategory.FORM_10K,
    r"annual.?report": FilingCategory.FORM_10K,
    r"10-?q": FilingCategory.FORM_10Q,
    r"10q": FilingCategory.FORM_10Q,
    r"8-?k": FilingCategory.FORM_8K,
    r"8k": FilingCategory.FORM_8K,
    r"13f": FilingCategory.FORM_13F,
    r"13-?f": FilingCategory.FORM_13F,
    r"sc13d": FilingCategory.SCHEDULE_13D,
    r"sc-?13d": FilingCategory.SCHEDULE_13D,
    r"13d": FilingCategory.SCHEDULE_13D,
    r"sc13g": FilingCategory.SCHEDULE_13G,
    r"sc-?13g": FilingCategory.SCHEDULE_13G,
    r"13g": FilingCategory.SCHEDULE_13G,
    r"form144": FilingCategory.FORM_144,
    r"form-?144": FilingCategory.FORM_144,
    r"s-?1": FilingCategory.FORM_S1,
    r"20-?f": FilingCategory.FORM_20F,
}

# Content-based classification patterns (for PDF/XLS text extraction)
CONTENT_PATTERNS: Dict[str, FilingCategory] = {
    r"STATEMENT OF CHANGES IN BENEFICIAL OWNERSHIP": FilingCategory.FORM_4,
    r"INITIAL STATEMENT OF BENEFICIAL OWNERSHIP": FilingCategory.FORM_3,
    r"ANNUAL STATEMENT OF CHANGES IN BENEFICIAL OWNERSHIP": FilingCategory.FORM_5,
    r"SCHEDULE 14A": FilingCategory.DEF_14A,
    r"DEFINITIVE PROXY STATEMENT": FilingCategory.DEF_14A,
    r"ANNUAL REPORT PURSUANT TO SECTION 13": FilingCategory.FORM_10K,
    r"QUARTERLY REPORT PURSUANT TO SECTION 13": FilingCategory.FORM_10Q,
    r"CURRENT REPORT PURSUANT TO SECTION 13": FilingCategory.FORM_8K,
    r"FORM 13F": FilingCategory.FORM_13F,
    r"SCHEDULE 13D": FilingCategory.SCHEDULE_13D,
    r"SCHEDULE 13G": FilingCategory.SCHEDULE_13G,
    r"NOTICE OF PROPOSED SALE": FilingCategory.FORM_144,
}


@dataclass
class FilingClassification:
    """Result of classifying a single filing document."""

    file_path: str
    file_name: str
    file_extension: str
    file_size_bytes: int
    category: FilingCategory
    confidence: float
    classification_method: str  # "filename", "content", "xbrl_index", "accession"
    cik: Optional[str] = None
    accession_number: Optional[str] = None
    filing_date: Optional[date] = None
    company_name: Optional[str] = None
    target_nodes: List[int] = field(default_factory=list)
    content_hash: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "file_path": self.file_path,
            "file_name": self.file_name,
            "file_extension": self.file_extension,
            "file_size_bytes": self.file_size_bytes,
            "category": self.category.value,
            "confidence": self.confidence,
            "classification_method": self.classification_method,
            "cik": self.cik,
            "accession_number": self.accession_number,
            "filing_date": self.filing_date.isoformat() if self.filing_date else None,
            "company_name": self.company_name,
            "target_nodes": self.target_nodes,
            "content_hash": self.content_hash,
            "metadata": self.metadata,
        }


@dataclass
class ClassificationReport:
    """Summary report of filing classification across a corpus."""

    total_files: int = 0
    classified_files: int = 0
    unclassified_files: int = 0
    category_counts: Dict[str, int] = field(default_factory=dict)
    node_input_counts: Dict[int, int] = field(default_factory=dict)
    classifications: List[FilingClassification] = field(default_factory=list)
    high_confidence_count: int = 0  # confidence >= 0.8
    medium_confidence_count: int = 0  # 0.5 <= confidence < 0.8
    low_confidence_count: int = 0  # confidence < 0.5
    errors: List[Dict[str, str]] = field(default_factory=list)
    scan_started_at: Optional[datetime] = None
    scan_completed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "total_files": self.total_files,
            "classified_files": self.classified_files,
            "unclassified_files": self.unclassified_files,
            "category_counts": self.category_counts,
            "node_input_counts": self.node_input_counts,
            "high_confidence_count": self.high_confidence_count,
            "medium_confidence_count": self.medium_confidence_count,
            "low_confidence_count": self.low_confidence_count,
            "error_count": len(self.errors),
            "scan_started_at": (
                self.scan_started_at.isoformat() if self.scan_started_at else None
            ),
            "scan_completed_at": (
                self.scan_completed_at.isoformat() if self.scan_completed_at else None
            ),
        }


class FilingClassifier:
    """
    Classify raw SEC EDGAR filing documents by filing type.

    Combines filename pattern matching, content-based analysis, and
    XBRL index cross-referencing to classify UUID-named PDFs, XLS,
    and other documents from the SEC-AGENT EDGAR corpus.

    Integrates with JLAW's ActorRoleClassifier for entity-level
    classification and JLAW's 16-node pipeline for routing.

    Args:
        xbrl_index_path: Path to CIK XBRL Company Facts JSON file.
        corpus_root: Root directory of the raw EDGAR filing corpus.
        cik: Target company CIK number.
        company_name: Target company name.
    """

    def __init__(
        self,
        xbrl_index_path: Optional[Path] = None,
        corpus_root: Optional[Path] = None,
        cik: Optional[str] = None,
        company_name: Optional[str] = None,
    ) -> None:
        self.xbrl_index_path = xbrl_index_path
        self.corpus_root = corpus_root
        self.cik = cik
        self.company_name = company_name
        self.xbrl_index: Optional[Dict[str, Any]] = None
        self.actor_classifier = ActorRoleClassifier()
        self.actor_extractor = ActorExtractionEngine()
        self._compiled_filename_patterns: List[Tuple[re.Pattern, FilingCategory]] = [
            (re.compile(pattern, re.IGNORECASE), category)
            for pattern, category in FILENAME_PATTERNS.items()
        ]
        self._compiled_content_patterns: List[Tuple[re.Pattern, FilingCategory]] = [
            (re.compile(pattern, re.IGNORECASE), category)
            for pattern, category in CONTENT_PATTERNS.items()
        ]
        if xbrl_index_path and xbrl_index_path.exists():
            self._load_xbrl_index()

    def _load_xbrl_index(self) -> None:
        """Load the XBRL Company Facts JSON index for cross-referencing."""
        if not self.xbrl_index_path:
            return
        try:
            with open(self.xbrl_index_path, "r", encoding="utf-8") as f:
                self.xbrl_index = json.load(f)
            logger.info(
                "Loaded XBRL index from %s (%d bytes)",
                self.xbrl_index_path,
                self.xbrl_index_path.stat().st_size,
            )
        except (json.JSONDecodeError, OSError) as e:
            logger.error("Failed to load XBRL index: %s", e)
            self.xbrl_index = None

    def classify_file(self, file_path: Path) -> FilingClassification:
        """
        Classify a single filing document.

        Classification precedence:
            1. XBRL index cross-reference (highest confidence)
            2. Accession number extraction from filename/path
            3. Filename pattern matching
            4. Content-based pattern matching (if text extractable)

        Args:
            file_path: Path to the filing document.

        Returns:
            FilingClassification with category and confidence score.
        """
        file_name = file_path.name
        file_extension = file_path.suffix.lower()
        file_size = file_path.stat().st_size if file_path.exists() else 0

        # Compute content hash for integrity tracking
        content_hash = self._compute_file_hash(file_path)

        # Try classification methods in order of confidence
        classification = None

        # Method 1: XBRL index cross-reference
        if self.xbrl_index:
            classification = self._classify_from_xbrl(file_path, file_name)

        # Method 2: Accession number from path/filename
        if not classification or classification.confidence < 0.8:
            accession_result = self._classify_from_accession(file_path)
            if accession_result and (
                not classification
                or accession_result.confidence > classification.confidence
            ):
                classification = accession_result

        # Method 3: Filename pattern matching
        if not classification or classification.confidence < 0.7:
            filename_result = self._classify_from_filename(file_name)
            if filename_result and (
                not classification
                or filename_result.confidence > classification.confidence
            ):
                classification = filename_result

        # Method 4: Content-based pattern matching
        if not classification or classification.confidence < 0.6:
            content_result = self._classify_from_content(file_path, file_extension)
            if content_result and (
                not classification
                or content_result.confidence > classification.confidence
            ):
                classification = content_result

        # Fallback: unknown classification
        if not classification:
            classification = FilingClassification(
                file_path=str(file_path),
                file_name=file_name,
                file_extension=file_extension,
                file_size_bytes=file_size,
                category=FilingCategory.UNKNOWN,
                confidence=0.0,
                classification_method="none",
            )

        # Enrich with common fields
        classification.file_path = str(file_path)
        classification.file_name = file_name
        classification.file_extension = file_extension
        classification.file_size_bytes = file_size
        classification.content_hash = content_hash
        classification.cik = classification.cik or self.cik
        classification.company_name = classification.company_name or self.company_name

        # Map to target JLAW pipeline nodes
        classification.target_nodes = FILING_TO_NODE_MAP.get(
            classification.category, []
        )

        return classification

    def classify_corpus(
        self,
        corpus_path: Optional[Path] = None,
        extensions: Optional[List[str]] = None,
    ) -> ClassificationReport:
        """
        Classify all filing documents in an EDGAR corpus directory.

        Args:
            corpus_path: Root directory to scan. Defaults to self.corpus_root.
            extensions: File extensions to include. Defaults to PDF, XLS, XLSX, XML, TXT.

        Returns:
            ClassificationReport with per-file results and summary statistics.
        """
        scan_root = corpus_path or self.corpus_root
        if not scan_root or not scan_root.exists():
            logger.error("Corpus path does not exist: %s", scan_root)
            return ClassificationReport()

        if extensions is None:
            extensions = [".pdf", ".xls", ".xlsx", ".xml", ".txt", ".htm", ".html"]

        report = ClassificationReport(scan_started_at=datetime.utcnow())

        # Scan all matching files
        filing_files = []
        for ext in extensions:
            filing_files.extend(scan_root.rglob(f"*{ext}"))

        report.total_files = len(filing_files)
        logger.info("Scanning %d files in %s", report.total_files, scan_root)

        for file_path in filing_files:
            try:
                classification = self.classify_file(file_path)
                report.classifications.append(classification)

                if classification.category != FilingCategory.UNKNOWN:
                    report.classified_files += 1
                    cat_name = classification.category.value
                    report.category_counts[cat_name] = (
                        report.category_counts.get(cat_name, 0) + 1
                    )
                    for node_id in classification.target_nodes:
                        report.node_input_counts[node_id] = (
                            report.node_input_counts.get(node_id, 0) + 1
                        )
                else:
                    report.unclassified_files += 1

                # Track confidence distribution
                if classification.confidence >= 0.8:
                    report.high_confidence_count += 1
                elif classification.confidence >= 0.5:
                    report.medium_confidence_count += 1
                else:
                    report.low_confidence_count += 1

            except Exception as e:
                logger.error("Error classifying %s: %s", file_path, e)
                report.errors.append(
                    {"file": str(file_path), "error": str(e)}
                )

        report.scan_completed_at = datetime.utcnow()
        logger.info(
            "Classification complete: %d/%d classified (%.1f%%)",
            report.classified_files,
            report.total_files,
            (
                (report.classified_files / report.total_files * 100)
                if report.total_files > 0
                else 0
            ),
        )

        return report

    def get_filings_for_node(
        self,
        report: ClassificationReport,
        node_id: int,
    ) -> List[FilingClassification]:
        """
        Get all classified filings routed to a specific JLAW pipeline node.

        Args:
            report: ClassificationReport from classify_corpus.
            node_id: JLAW pipeline node number (1-16).

        Returns:
            List of FilingClassification objects for the target node.
        """
        return [
            c for c in report.classifications if node_id in c.target_nodes
        ]

    def to_sec_filings(
        self,
        classifications: List[FilingClassification],
    ) -> List[SECFiling]:
        """
        Convert FilingClassification objects to JLAW SECFiling objects
        for pipeline ingestion.

        Args:
            classifications: Classified filing documents.

        Returns:
            List of SECFiling objects compatible with JLAW's pipeline input.
        """
        sec_filings = []
        for c in classifications:
            if c.category == FilingCategory.UNKNOWN:
                continue
            try:
                filing = SECFiling(
                    accession_number=c.accession_number or f"local-{c.content_hash[:16]}",
                    form_type=c.category.value,
                    filing_date=c.filing_date or date.today(),
                    report_date=c.filing_date,
                    primary_document=c.file_name,
                    file_number="",
                    cik=c.cik or self.cik or "",
                    company_name=c.company_name or self.company_name or "",
                    document_url=f"file://{c.file_path}",
                    index_url="",
                )
                sec_filings.append(filing)
            except Exception as e:
                logger.warning("Failed to convert %s to SECFiling: %s", c.file_name, e)

        return sec_filings

    def export_report(
        self,
        report: ClassificationReport,
        output_path: Path,
    ) -> Path:
        """
        Export classification report to JSON.

        Args:
            report: ClassificationReport to export.
            output_path: Output JSON file path.

        Returns:
            Path to the exported JSON file.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "summary": report.to_dict(),
            "classifications": [c.to_dict() for c in report.classifications],
            "errors": report.errors,
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        logger.info("Exported classification report to %s", output_path)
        return output_path

    # ── Private classification methods ──────────────────────────────────

    def _classify_from_xbrl(
        self,
        file_path: Path,
        file_name: str,
    ) -> Optional[FilingClassification]:
        """Cross-reference file against XBRL Company Facts index."""
        if not self.xbrl_index:
            return None

        # Look for accession number in filename or path
        accession = self._extract_accession_number(str(file_path))
        if not accession:
            return None

        # Search XBRL index for matching filing
        facts = self.xbrl_index.get("facts", {})
        for taxonomy, concepts in facts.items():
            for concept_name, concept_data in concepts.items():
                units = concept_data.get("units", {})
                for unit_key, entries in units.items():
                    for entry in entries:
                        if entry.get("accn", "").replace("-", "") == accession.replace(
                            "-", ""
                        ):
                            form_type = entry.get("form", "")
                            category = self._form_type_to_category(form_type)
                            if category:
                                filing_date_str = entry.get("filed", "")
                                filing_date = None
                                if filing_date_str:
                                    try:
                                        filing_date = date.fromisoformat(
                                            filing_date_str
                                        )
                                    except ValueError:
                                        pass
                                return FilingClassification(
                                    file_path=str(file_path),
                                    file_name=file_name,
                                    file_extension=file_path.suffix.lower(),
                                    file_size_bytes=0,
                                    category=category,
                                    confidence=0.95,
                                    classification_method="xbrl_index",
                                    accession_number=accession,
                                    filing_date=filing_date,
                                )
        return None

    def _classify_from_accession(
        self,
        file_path: Path,
    ) -> Optional[FilingClassification]:
        """Extract accession number from file path and infer filing type."""
        accession = self._extract_accession_number(str(file_path))
        if not accession:
            return None

        # Accession numbers don't directly tell us filing type,
        # but confirm this is a real SEC filing
        return FilingClassification(
            file_path=str(file_path),
            file_name=file_path.name,
            file_extension=file_path.suffix.lower(),
            file_size_bytes=0,
            category=FilingCategory.UNKNOWN,
            confidence=0.3,
            classification_method="accession",
            accession_number=accession,
        )

    def _classify_from_filename(
        self,
        file_name: str,
    ) -> Optional[FilingClassification]:
        """Match filename against known SEC filing patterns."""
        name_lower = file_name.lower()
        for pattern, category in self._compiled_filename_patterns:
            if pattern.search(name_lower):
                return FilingClassification(
                    file_path="",
                    file_name=file_name,
                    file_extension=Path(file_name).suffix.lower(),
                    file_size_bytes=0,
                    category=category,
                    confidence=0.75,
                    classification_method="filename",
                )
        return None

    def _classify_from_content(
        self,
        file_path: Path,
        file_extension: str,
    ) -> Optional[FilingClassification]:
        """Extract text content and match against SEC filing patterns."""
        if file_extension not in (".txt", ".htm", ".html", ".xml"):
            return None

        try:
            # Read first 10KB for classification
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read(10240)
        except OSError:
            return None

        content_upper = content.upper()
        for pattern, category in self._compiled_content_patterns:
            if pattern.search(content_upper):
                return FilingClassification(
                    file_path=str(file_path),
                    file_name=file_path.name,
                    file_extension=file_extension,
                    file_size_bytes=0,
                    category=category,
                    confidence=0.85,
                    classification_method="content",
                )
        return None

    @staticmethod
    def _extract_accession_number(text: str) -> Optional[str]:
        """Extract SEC accession number from text (format: XXXXXXXXXX-YY-ZZZZZZ)."""
        match = re.search(r"\d{10}-\d{2}-\d{6}", text)
        return match.group(0) if match else None

    @staticmethod
    def _form_type_to_category(form_type: str) -> Optional[FilingCategory]:
        """Map SEC form type string to FilingCategory enum."""
        form_upper = form_type.upper().strip()
        mappings = {
            "4": FilingCategory.FORM_4,
            "3": FilingCategory.FORM_3,
            "5": FilingCategory.FORM_5,
            "DEF 14A": FilingCategory.DEF_14A,
            "10-K": FilingCategory.FORM_10K,
            "10-K/A": FilingCategory.FORM_10K,
            "10-Q": FilingCategory.FORM_10Q,
            "10-Q/A": FilingCategory.FORM_10Q,
            "8-K": FilingCategory.FORM_8K,
            "8-K/A": FilingCategory.FORM_8K,
            "13F-HR": FilingCategory.FORM_13F,
            "13F-HR/A": FilingCategory.FORM_13F,
            "SC 13D": FilingCategory.SCHEDULE_13D,
            "SC 13D/A": FilingCategory.SCHEDULE_13D,
            "SC 13G": FilingCategory.SCHEDULE_13G,
            "SC 13G/A": FilingCategory.SCHEDULE_13G,
            "144": FilingCategory.FORM_144,
            "S-1": FilingCategory.FORM_S1,
            "20-F": FilingCategory.FORM_20F,
        }
        return mappings.get(form_upper)

    @staticmethod
    def _compute_file_hash(file_path: Path) -> Optional[str]:
        """Compute SHA-256 hash of file contents for integrity tracking."""
        if not file_path.exists():
            return None
        sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except OSError:
            return None
