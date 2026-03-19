"""
Tests for SEC-AGENT ingestion pipeline and report generators.

Tests the corpus scanner, XBRL indexer, and report wiring modules.
"""

import json
import tempfile
from datetime import date, datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.sec_agent.ingestion.corpus_scanner import (
    CorpusScanner,
    CorpusManifest,
    FileEntry,
    SUPPORTED_EXTENSIONS,
)
from src.sec_agent.ingestion.xbrl_indexer import (
    XBRLIndexer,
    XBRLIndex,
    XBRLFact,
)
from src.sec_agent.reports.legislative_brief import (
    LegislativeBriefGenerator,
    LegislativeBriefOutput,
    CongressionalRecipient,
)
from src.sec_agent.pipeline import (
    SecAgentPipeline,
    PipelineResult,
    PipelineStageResult,
)


# ═══════════════════════════════════════════════════════════════════════
# CorpusScanner Tests
# ═══════════════════════════════════════════════════════════════════════


class TestCorpusScanner:
    """Test CorpusScanner functionality."""

    def test_scan_empty_directory(self):
        """Test scanning an empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scanner = CorpusScanner(corpus_root=Path(tmpdir))
            manifest = scanner.scan()
            assert manifest.total_files == 0
            assert manifest.total_size_bytes == 0

    def test_scan_with_files(self):
        """Test scanning directory with multiple file types."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "filing1.pdf").write_bytes(b"pdf content here")
            (root / "data.xls").write_bytes(b"xls content here")
            (root / "index.json").write_text('{"test": true}')
            (root / "readme.md").write_text("Not a filing")  # Should be excluded

            scanner = CorpusScanner(corpus_root=root)
            manifest = scanner.scan()

            assert manifest.total_files == 3  # .md not in SUPPORTED_EXTENSIONS
            assert manifest.total_size_bytes > 0
            assert ".pdf" in manifest.extension_counts
            assert ".xls" in manifest.extension_counts
            assert ".json" in manifest.extension_counts

    def test_scan_nested_directories(self):
        """Test scanning with nested directory structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            primary = root / "primary"
            primary.mkdir()
            secondary = root / "nits_secondary"
            secondary.mkdir()

            (primary / "filing1.pdf").write_bytes(b"test")
            (primary / "filing2.xls").write_bytes(b"test")
            (secondary / "filing3.pdf").write_bytes(b"test")

            scanner = CorpusScanner(corpus_root=root)
            manifest = scanner.scan()

            assert manifest.total_files == 3
            assert "primary" in manifest.directory_counts
            assert "nits_secondary" in manifest.directory_counts

    def test_scan_nonexistent_directory(self):
        """Test scanning nonexistent directory."""
        scanner = CorpusScanner(corpus_root=Path("/nonexistent/path"))
        manifest = scanner.scan()
        assert manifest.total_files == 0
        assert len(manifest.errors) > 0

    def test_scan_with_hashes(self):
        """Test scanning with SHA-256 hash computation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "filing.pdf").write_bytes(b"test content for hashing")

            scanner = CorpusScanner(corpus_root=root, compute_hashes=True)
            manifest = scanner.scan()

            assert manifest.total_files == 1
            assert manifest.files[0].sha256 is not None
            assert len(manifest.files[0].sha256) == 64  # SHA-256 hex length

    def test_manifest_to_dict(self):
        """Test CorpusManifest serialization."""
        manifest = CorpusManifest(
            corpus_root="/data/edgar",
            scan_timestamp=datetime(2024, 1, 1),
            total_files=100,
            total_size_bytes=1024 * 1024 * 50,
        )
        d = manifest.to_dict()
        assert d["total_files"] == 100
        assert d["total_size_mb"] == 50.0

    def test_manifest_get_files_by_extension(self):
        """Test filtering files by extension."""
        manifest = CorpusManifest(
            corpus_root="/data",
            scan_timestamp=datetime.utcnow(),
            files=[
                FileEntry(
                    file_path="/data/a.pdf", file_name="a.pdf",
                    extension=".pdf", size_bytes=100,
                    category="document", relative_path="a.pdf",
                    parent_directory="root",
                ),
                FileEntry(
                    file_path="/data/b.xls", file_name="b.xls",
                    extension=".xls", size_bytes=200,
                    category="spreadsheet", relative_path="b.xls",
                    parent_directory="root",
                ),
            ],
        )
        pdfs = manifest.get_files_by_extension(".pdf")
        assert len(pdfs) == 1
        assert pdfs[0].file_name == "a.pdf"

    def test_export_manifest(self):
        """Test manifest export to JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "corpus"
            root.mkdir()
            (root / "test.pdf").write_bytes(b"test")

            scanner = CorpusScanner(corpus_root=root)
            manifest = scanner.scan()

            output_path = Path(tmpdir) / "manifest.json"
            scanner.export_manifest(manifest, output_path)

            assert output_path.exists()
            with open(output_path) as f:
                data = json.load(f)
            assert data["total_files"] == 1


# ═══════════════════════════════════════════════════════════════════════
# XBRLIndexer Tests
# ═══════════════════════════════════════════════════════════════════════


class TestXBRLIndexer:
    """Test XBRLIndexer functionality."""

    @pytest.fixture
    def sample_xbrl_json(self, tmp_path):
        """Create a sample XBRL Company Facts JSON file."""
        data = {
            "cik": 320187,
            "entityName": "NIKE, Inc.",
            "facts": {
                "us-gaap": {
                    "Revenue": {
                        "label": "Revenue",
                        "units": {
                            "USD": [
                                {
                                    "val": 39117000000,
                                    "fy": 2019,
                                    "fp": "FY",
                                    "form": "10-K",
                                    "filed": "2019-07-25",
                                    "accn": "0000320187-19-000042",
                                    "start": "2018-06-01",
                                    "end": "2019-05-31",
                                },
                                {
                                    "val": 37403000000,
                                    "fy": 2020,
                                    "fp": "FY",
                                    "form": "10-K",
                                    "filed": "2020-07-24",
                                    "accn": "0000320187-20-000033",
                                    "start": "2019-06-01",
                                    "end": "2020-05-31",
                                },
                            ]
                        },
                    },
                    "NetIncomeLoss": {
                        "label": "Net Income (Loss)",
                        "units": {
                            "USD": [
                                {
                                    "val": 4029000000,
                                    "fy": 2019,
                                    "fp": "FY",
                                    "form": "10-K",
                                    "filed": "2019-07-25",
                                    "accn": "0000320187-19-000042",
                                },
                            ]
                        },
                    },
                },
                "dei": {
                    "EntityCommonStockSharesOutstanding": {
                        "label": "Shares Outstanding",
                        "units": {
                            "shares": [
                                {
                                    "val": 1571000000,
                                    "fy": 2019,
                                    "fp": "FY",
                                    "form": "10-K",
                                    "filed": "2019-07-25",
                                    "instant": "2019-05-31",
                                },
                            ]
                        },
                    },
                },
            },
        }

        path = tmp_path / "CIK0000320187.json"
        with open(path, "w") as f:
            json.dump(data, f)
        return path

    def test_index_xbrl_data(self, sample_xbrl_json):
        """Test XBRL data indexing."""
        indexer = XBRLIndexer(source_path=sample_xbrl_json)
        index = indexer.index()

        assert index.cik == "320187"
        assert index.entity_name == "NIKE, Inc."
        assert index.total_facts == 4
        assert "us-gaap" in index.taxonomies
        assert "dei" in index.taxonomies
        assert "Revenue" in index.concepts
        assert "NetIncomeLoss" in index.concepts

    def test_index_fiscal_years(self, sample_xbrl_json):
        """Test fiscal year extraction from XBRL index."""
        indexer = XBRLIndexer(source_path=sample_xbrl_json)
        index = indexer.index()

        assert 2019 in index.fiscal_years
        assert 2020 in index.fiscal_years

    def test_get_concept_values(self, sample_xbrl_json):
        """Test concept value lookup."""
        indexer = XBRLIndexer(source_path=sample_xbrl_json)
        index = indexer.index()

        revenue_facts = index.get_concept_values("Revenue")
        assert len(revenue_facts) == 2

        revenue_2019 = index.get_concept_values("Revenue", fiscal_year=2019)
        assert len(revenue_2019) == 1
        assert revenue_2019[0].value == 39117000000

    def test_get_concept_values_with_form_filter(self, sample_xbrl_json):
        """Test concept value lookup with form type filter."""
        indexer = XBRLIndexer(source_path=sample_xbrl_json)
        index = indexer.index()

        tenk_revenue = index.get_concept_values(
            "Revenue", form_type="10-K"
        )
        assert len(tenk_revenue) == 2

    def test_accession_numbers_tracked(self, sample_xbrl_json):
        """Test that accession numbers are tracked."""
        indexer = XBRLIndexer(source_path=sample_xbrl_json)
        index = indexer.index()

        assert "0000320187-19-000042" in index.accession_numbers

    def test_index_to_dict(self, sample_xbrl_json):
        """Test XBRLIndex serialization."""
        indexer = XBRLIndexer(source_path=sample_xbrl_json)
        index = indexer.index()
        d = index.to_dict()

        assert d["cik"] == "320187"
        assert d["entity_name"] == "NIKE, Inc."
        assert d["total_facts"] == 4

    def test_index_nonexistent_file(self):
        """Test indexing nonexistent file."""
        indexer = XBRLIndexer(source_path=Path("/nonexistent.json"))
        index = indexer.index()
        assert index.total_facts == 0

    def test_export_index(self, sample_xbrl_json, tmp_path):
        """Test XBRL index export to JSON."""
        indexer = XBRLIndexer(source_path=sample_xbrl_json)
        index = indexer.index()

        output_path = tmp_path / "index_export.json"
        indexer.export_index(index, output_path)

        assert output_path.exists()
        with open(output_path) as f:
            data = json.load(f)
        assert data["cik"] == "320187"
        assert data["total_facts"] == 4

    def test_xbrl_fact_to_dict(self):
        """Test XBRLFact serialization."""
        fact = XBRLFact(
            taxonomy="us-gaap",
            concept="Revenue",
            value=39117000000,
            unit="USD",
            period_end=date(2019, 5, 31),
            form_type="10-K",
            fiscal_year=2019,
        )
        d = fact.to_dict()
        assert d["taxonomy"] == "us-gaap"
        assert d["value"] == 39117000000
        assert d["fiscal_year"] == 2019


# ═══════════════════════════════════════════════════════════════════════
# LegislativeBriefGenerator Tests
# ═══════════════════════════════════════════════════════════════════════


class TestLegislativeBriefGenerator:
    """Test LegislativeBriefGenerator functionality."""

    def test_init_defaults(self):
        """Test initialization with default recipients."""
        with tempfile.TemporaryDirectory() as tmpdir:
            gen = LegislativeBriefGenerator(output_dir=tmpdir)
            assert len(gen.recipients) == 2

    def test_generate_brief(self):
        """Test legislative brief generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            gen = LegislativeBriefGenerator(output_dir=tmpdir)
            output = gen.generate_brief(
                case_id="NKE-2019",
                company_name="NIKE, Inc.",
                cik="320187",
                exec_summary={
                    "total_violations": 15,
                    "violations": [
                        {"violation_type": "LATE_FORM4"},
                        {"violation_type": "LATE_FORM4"},
                        {"violation_type": "LATE_FORM4"},
                        {"violation_type": "SHORT_SWING_PROFIT"},
                    ],
                },
            )

            assert output.status == "success"
            assert output.total_violations == 15
            assert output.executive_briefing is not None
            assert "executive_briefing" in output.output_paths
            assert "policy_analysis" in output.output_paths
            assert "legislative_brief" in output.output_paths

    def test_identify_systemic_issues(self):
        """Test systemic issue identification."""
        violations = [
            {"violation_type": "LATE_FORM4"},
            {"violation_type": "LATE_FORM4"},
            {"violation_type": "LATE_FORM4"},
            {"violation_type": "SHORT_SWING_PROFIT"},
        ]
        issues = LegislativeBriefGenerator._identify_systemic_issues(violations)
        assert len(issues) >= 1
        assert any("LATE_FORM4" in issue for issue in issues)

    def test_generate_recommendations(self):
        """Test policy recommendation generation."""
        recs = LegislativeBriefGenerator._generate_recommendations(
            systemic_issues=["Section 16 compliance gap"],
            total_violations=25,
        )
        assert len(recs) >= 2  # Should have funding + penalty recs

    def test_output_to_dict(self):
        """Test LegislativeBriefOutput serialization."""
        output = LegislativeBriefOutput(
            brief_id="LEG-NKE-2019",
            case_id="NKE-2019",
            company_name="NIKE, Inc.",
            cik="320187",
            generated_at=datetime(2024, 1, 1),
            total_violations=10,
        )
        d = output.to_dict()
        assert d["brief_id"] == "LEG-NKE-2019"
        assert d["total_violations"] == 10

    def test_congressional_recipient_to_dict(self):
        """Test CongressionalRecipient serialization."""
        r = CongressionalRecipient(
            name="Test Committee",
            title="Chairman",
            committee="Banking",
            chamber="Senate",
        )
        d = r.to_dict()
        assert d["chamber"] == "Senate"


# ═══════════════════════════════════════════════════════════════════════
# Pipeline Tests
# ═══════════════════════════════════════════════════════════════════════


class TestSecAgentPipeline:
    """Test SecAgentPipeline functionality."""

    def test_init(self):
        """Test pipeline initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = SecAgentPipeline(
                corpus_root=Path(tmpdir),
                cik="320187",
                company_name="NIKE, Inc.",
            )
            assert pipeline.cik == "320187"
            assert pipeline.company_name == "NIKE, Inc."

    def test_get_node_routing_empty(self):
        """Test node routing without classification report."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = SecAgentPipeline(
                corpus_root=Path(tmpdir),
                cik="320187",
            )
            routing = pipeline.get_node_routing()
            assert routing == {}

    def test_pipeline_result_to_dict(self):
        """Test PipelineResult serialization."""
        result = PipelineResult(
            pipeline_id="test-123",
            cik="320187",
            company_name="NIKE, Inc.",
            started_at=datetime(2024, 1, 1),
            status="success",
            total_files_scanned=100,
            total_files_classified=80,
        )
        d = result.to_dict()
        assert d["pipeline_id"] == "test-123"
        assert d["total_files_scanned"] == 100
        assert d["status"] == "success"

    def test_pipeline_stage_result_to_dict(self):
        """Test PipelineStageResult serialization."""
        stage = PipelineStageResult(
            stage_name="corpus_scan",
            status="success",
            duration_seconds=1.5,
        )
        d = stage.to_dict()
        assert d["stage_name"] == "corpus_scan"
        assert d["duration_seconds"] == 1.5

    @pytest.mark.asyncio
    async def test_execute_pipeline_with_files(self):
        """Test pipeline execution with corpus files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            corpus = Path(tmpdir) / "corpus"
            corpus.mkdir()
            output = Path(tmpdir) / "output"

            # Create some test files
            (corpus / "form4_insider.pdf").write_bytes(b"form 4 content")
            (corpus / "10-K_annual.pdf").write_bytes(b"10-K content")

            pipeline = SecAgentPipeline(
                corpus_root=corpus,
                cik="320187",
                company_name="NIKE, Inc.",
                output_dir=output,
            )

            result = await pipeline.execute(
                skip_stages=["cik_validation"]  # Skip API call
            )

            assert result.status in ("success", "partial")
            assert result.total_files_scanned == 2
            assert result.total_files_classified >= 1

            # Check stage results
            stage_names = [s.stage_name for s in result.stages]
            assert "corpus_scan" in stage_names
            assert "filing_classification" in stage_names

    @pytest.mark.asyncio
    async def test_execute_pipeline_skip_stages(self):
        """Test pipeline execution with skipped stages."""
        with tempfile.TemporaryDirectory() as tmpdir:
            corpus = Path(tmpdir) / "corpus"
            corpus.mkdir()

            pipeline = SecAgentPipeline(
                corpus_root=corpus,
                cik="320187",
                output_dir=Path(tmpdir) / "output",
            )

            result = await pipeline.execute(
                skip_stages=["cik_validation", "xbrl_indexing"]
            )

            skipped = [s for s in result.stages if s.status == "skipped"]
            assert len(skipped) >= 2
