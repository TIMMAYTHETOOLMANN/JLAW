"""
Tests for FYAnalyzer — Fiscal Year Filing Analysis Module.

Tests the research report baseline loading, binary file extraction
(PDF via pdfplumber, XLS via pandas/openpyxl), and output generation
(narrative_report.md and analysis.json).
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

# Import directly from the module to avoid heavy dependency chain
# through src.sec_agent.__init__ which pulls in plotly, etc.
from src.sec_agent.ingestion.fy_analyzer import (
    FYAnalyzer,
    FYAnalysisResult,
    FilingExtraction,
    _extract_pdf_text,
    _extract_xls_data,
)
from src.sec_agent.ingestion.corpus_scanner import (
    CorpusManifest,
    FileEntry,
)


# ═══════════════════════════════════════════════════════════════════════
# FilingExtraction Tests
# ═══════════════════════════════════════════════════════════════════════


class TestFilingExtraction:
    """Test FilingExtraction dataclass."""

    def test_to_dict(self):
        """Test serialization of FilingExtraction."""
        extraction = FilingExtraction(
            file_path="/data/filing.pdf",
            file_name="filing.pdf",
            extension=".pdf",
            category="document",
            text_content="Test text content",
            extraction_method="pdfplumber/PyMuPDF",
            extraction_success=True,
            sha256="abc123",
        )
        d = extraction.to_dict()
        assert d["file_name"] == "filing.pdf"
        assert d["extension"] == ".pdf"
        assert d["extraction_success"] is True
        assert d["text_length"] == 17
        assert d["sha256"] == "abc123"

    def test_to_dict_failed_extraction(self):
        """Test serialization with failed extraction."""
        extraction = FilingExtraction(
            file_path="/data/bad.pdf",
            file_name="bad.pdf",
            extension=".pdf",
            category="document",
            extraction_success=False,
            error="Corrupted file",
        )
        d = extraction.to_dict()
        assert d["extraction_success"] is False
        assert d["error"] == "Corrupted file"
        assert d["text_length"] == 0


# ═══════════════════════════════════════════════════════════════════════
# FYAnalysisResult Tests
# ═══════════════════════════════════════════════════════════════════════


class TestFYAnalysisResult:
    """Test FYAnalysisResult dataclass."""

    def _make_result(self, **kwargs) -> FYAnalysisResult:
        """Create a test result with defaults."""
        defaults = {
            "case_id": "JLAW-NKE-2019-001",
            "fiscal_year": 2019,
            "company_name": "NIKE, Inc.",
            "cik": "0000320187",
            "analysis_timestamp": datetime(2026, 4, 1, 12, 0, 0),
        }
        defaults.update(kwargs)
        return FYAnalysisResult(**defaults)

    def test_to_dict(self):
        """Test serialization to analysis.json format."""
        result = self._make_result(
            total_filings_processed=10,
            successful_extractions=8,
            failed_extractions=2,
            status="complete",
        )
        d = result.to_dict()
        assert d["case_id"] == "JLAW-NKE-2019-001"
        assert d["fiscal_year"] == 2019
        assert d["statistics"]["total_filings_processed"] == 10
        assert d["statistics"]["successful_extractions"] == 8
        assert d["status"] == "complete"

    def test_to_narrative_markdown(self):
        """Test narrative report generation."""
        result = self._make_result(
            total_filings_processed=5,
            successful_extractions=4,
            failed_extractions=1,
            pdf_extractions=2,
            xls_extractions=1,
            text_extractions=2,
            research_baseline_loaded=True,
            status="complete",
        )
        md = result.to_narrative_markdown()
        assert "# Forensic Analysis Narrative Report — FY2019" in md
        assert "NIKE, Inc." in md
        assert "CIK 0000320187" in md
        assert "5 SEC filings" in md
        assert "Phase 1 protocol" in md

    def test_narrative_warns_no_baseline(self):
        """Test narrative warns when baseline not loaded."""
        result = self._make_result(
            research_baseline_loaded=False,
        )
        md = result.to_narrative_markdown()
        assert "WARNING" in md
        assert "Research baseline was NOT loaded" in md

    def test_success_rate(self):
        """Test success rate calculation."""
        result = self._make_result(
            total_filings_processed=10,
            successful_extractions=8,
        )
        assert result._success_rate() == "80.0"

    def test_success_rate_zero_files(self):
        """Test success rate with zero files."""
        result = self._make_result(total_filings_processed=0)
        assert result._success_rate() == "0.0"


# ═══════════════════════════════════════════════════════════════════════
# FYAnalyzer Tests
# ═══════════════════════════════════════════════════════════════════════


class TestFYAnalyzer:
    """Test FYAnalyzer fiscal year analysis."""

    def test_init_defaults(self):
        """Test FYAnalyzer initialization with defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            analyzer = FYAnalyzer(
                corpus_root=Path(tmpdir),
                cik="0000320187",
                company_name="NIKE, Inc.",
            )
            assert analyzer.cik == "0000320187"
            assert analyzer.company_name == "NIKE, Inc."
            assert analyzer.corpus_root == Path(tmpdir)

    def test_load_research_report(self):
        """Test that research report is loaded before filing analysis."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            reports_dir = root / "reports"
            reports_dir.mkdir()
            (reports_dir / "2019.md").write_text(
                "# FY2019 Research Report\nBaseline content."
            )

            analyzer = FYAnalyzer(
                corpus_root=root / "corpus",
                research_reports_dir=reports_dir,
                output_dir=root / "output",
                cik="0000320187",
                company_name="NIKE, Inc.",
            )

            content = analyzer._load_research_report(2019)
            assert "FY2019 Research Report" in content
            assert "Baseline content" in content

    def test_load_research_report_missing(self):
        """Test graceful handling when research report doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            analyzer = FYAnalyzer(
                corpus_root=Path(tmpdir),
                research_reports_dir=Path(tmpdir) / "nonexistent",
            )
            content = analyzer._load_research_report(2019)
            assert content == ""

    def test_analyze_empty_corpus(self):
        """Test analysis with empty corpus directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            corpus = root / "corpus"
            corpus.mkdir()

            analyzer = FYAnalyzer(
                corpus_root=corpus,
                output_dir=root / "output",
                cik="0000320187",
                company_name="NIKE, Inc.",
            )

            result = analyzer.analyze_fiscal_year(2019)
            assert result.status == "no_data"
            assert result.total_filings_processed == 0

    def test_analyze_with_text_files(self):
        """Test analysis with text files in corpus."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            corpus = root / "corpus"
            corpus.mkdir()
            output = root / "output"

            # Create test text files
            (corpus / "filing.txt").write_text("SEC Filing content here")
            (corpus / "index.json").write_text('{"filing_type": "10-K"}')
            (corpus / "report.html").write_text(
                "<html><body>Annual Report</body></html>"
            )

            # Create research report
            reports_dir = root / "reports"
            reports_dir.mkdir()
            (reports_dir / "2019.md").write_text("# FY2019 Baseline")

            analyzer = FYAnalyzer(
                corpus_root=corpus,
                research_reports_dir=reports_dir,
                output_dir=output,
                cik="0000320187",
                company_name="NIKE, Inc.",
                case_id="JLAW-NKE-2019-001",
            )

            result = analyzer.analyze_fiscal_year(2019)
            assert result.status == "complete"
            assert result.research_baseline_loaded is True
            assert result.total_filings_processed == 3
            assert result.successful_extractions == 3
            assert result.failed_extractions == 0

            # Check output files created
            assert (output / "narrative_report.md").exists()
            assert (output / "analysis.json").exists()

            # Validate analysis.json
            with open(output / "analysis.json") as f:
                analysis = json.load(f)
            assert analysis["case_id"] == "JLAW-NKE-2019-001"
            assert analysis["fiscal_year"] == 2019
            assert analysis["status"] == "complete"

            # Validate narrative_report.md
            narrative = (output / "narrative_report.md").read_text()
            assert "FY2019" in narrative
            assert "NIKE, Inc." in narrative

    def test_analyze_research_report_loaded_first(self):
        """Test that research report is loaded BEFORE filing extraction."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            corpus = root / "corpus"
            corpus.mkdir()
            (corpus / "test.txt").write_text("content")

            reports_dir = root / "reports"
            reports_dir.mkdir()
            (reports_dir / "2019.md").write_text("# Baseline Report")

            analyzer = FYAnalyzer(
                corpus_root=corpus,
                research_reports_dir=reports_dir,
                output_dir=root / "output",
            )

            result = analyzer.analyze_fiscal_year(2019)
            # Research baseline should be loaded
            assert result.research_baseline_loaded is True
            assert "Baseline Report" in result.research_baseline
            # Findings should confirm Phase 1 compliance
            assert result.findings["research_baseline"]["phase_1_compliant"]

    def test_merkle_root_computation(self):
        """Test Merkle root is computed from evidence hashes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            corpus = root / "corpus"
            corpus.mkdir()
            (corpus / "a.txt").write_text("content a")
            (corpus / "b.txt").write_text("content b")

            analyzer = FYAnalyzer(
                corpus_root=corpus,
                output_dir=root / "output",
            )

            result = analyzer.analyze_fiscal_year(2019)
            assert result.merkle_root is not None
            assert len(result.merkle_root) == 64  # SHA-256 hex length

    def test_compute_merkle_root_empty(self):
        """Test Merkle root with no hashes."""
        root = FYAnalyzer._compute_merkle_root([])
        assert len(root) == 64

    def test_compute_merkle_root_single(self):
        """Test Merkle root with single hash."""
        import hashlib
        h = hashlib.sha256(b"test").hexdigest()
        root = FYAnalyzer._compute_merkle_root([h])
        assert root == h

    def test_compute_merkle_root_multiple(self):
        """Test Merkle root with multiple hashes."""
        import hashlib
        h1 = hashlib.sha256(b"a").hexdigest()
        h2 = hashlib.sha256(b"b").hexdigest()
        root = FYAnalyzer._compute_merkle_root([h1, h2])
        # Root should be hash of concatenation
        expected = hashlib.sha256(
            bytes.fromhex(h1) + bytes.fromhex(h2)
        ).hexdigest()
        assert root == expected

    def test_extract_filing_unsupported(self):
        """Test extraction of unsupported file type."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            corpus = root / "corpus"
            corpus.mkdir()

            analyzer = FYAnalyzer(corpus_root=corpus)

            entry = FileEntry(
                file_path=str(corpus / "file.unknown"),
                file_name="file.unknown",
                extension=".unknown",
                size_bytes=0,
                category="other",
                relative_path="file.unknown",
                parent_directory="root",
            )
            extraction = analyzer._extract_filing(entry)
            assert not extraction.extraction_success
            assert "Unsupported" in (extraction.error or "")


# ═══════════════════════════════════════════════════════════════════════
# PDF/XLS Extraction Function Tests
# ═══════════════════════════════════════════════════════════════════════


class TestBinaryExtraction:
    """Test binary file extraction functions."""

    def test_extract_pdf_pdfplumber_import_error(self):
        """Test PDF extraction falls back when pdfplumber unavailable."""
        # When both libraries are unavailable, returns empty string
        result = _extract_pdf_text("/nonexistent/file.pdf")
        assert isinstance(result, str)

    def test_extract_xls_import_error(self):
        """Test XLS extraction returns empty when pandas unavailable."""
        with patch.dict("sys.modules", {"pandas": None}):
            result = _extract_xls_data("/nonexistent/file.xlsx")
            assert result == {}

    def test_extract_xls_nonexistent_file(self):
        """Test XLS extraction with nonexistent file."""
        result = _extract_xls_data("/nonexistent/file.xlsx")
        assert result == {}
