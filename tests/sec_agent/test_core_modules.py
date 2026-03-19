"""
Tests for FilingClassifier, CIKValidator, and ClaudeCompositor.

Tests the core SEC-AGENT integration modules that bridge the raw EDGAR
corpus to JLAW's 16-node forensic pipeline.
"""

import json
import tempfile
from datetime import date, datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.sec_agent.filing_classifier import (
    FilingCategory,
    FilingClassification,
    FilingClassifier,
    ClassificationReport,
    FILING_TO_NODE_MAP,
)
from src.sec_agent.cik_validator import (
    CIKValidator,
    CIKValidationResult,
    CIKLookupResult,
    KNOWN_CIK_MAPPINGS,
)
from src.sec_agent.claude_compositor import (
    ClaudeCompositor,
    CompositorMode,
    CompositorResult,
    AnalysisScope,
    AgentConfig,
    DEFAULT_AGENT_CONFIGS,
)


# ═══════════════════════════════════════════════════════════════════════
# FilingClassifier Tests
# ═══════════════════════════════════════════════════════════════════════


class TestFilingCategory:
    """Test FilingCategory enum and mappings."""

    def test_all_categories_have_values(self):
        """All filing categories should have string values."""
        for cat in FilingCategory:
            assert isinstance(cat.value, str)

    def test_node_mapping_coverage(self):
        """Key filing categories should map to JLAW pipeline nodes."""
        assert 1 in FILING_TO_NODE_MAP[FilingCategory.FORM_4]
        assert 2 in FILING_TO_NODE_MAP[FilingCategory.DEF_14A]
        assert 3 in FILING_TO_NODE_MAP[FilingCategory.FORM_10Q]
        assert 4 in FILING_TO_NODE_MAP[FilingCategory.FORM_10K]
        assert 7 in FILING_TO_NODE_MAP[FilingCategory.FORM_13F]
        assert 8 in FILING_TO_NODE_MAP[FilingCategory.SCHEDULE_13D]
        assert 9 in FILING_TO_NODE_MAP[FilingCategory.FORM_8K]
        assert 10 in FILING_TO_NODE_MAP[FilingCategory.FORM_144]

    def test_unknown_category_not_in_node_map(self):
        """UNKNOWN category should not map to any nodes."""
        assert FilingCategory.UNKNOWN not in FILING_TO_NODE_MAP


class TestFilingClassification:
    """Test FilingClassification dataclass."""

    def test_to_dict(self):
        """Test serialization to dictionary."""
        fc = FilingClassification(
            file_path="/data/filing.pdf",
            file_name="filing.pdf",
            file_extension=".pdf",
            file_size_bytes=1024,
            category=FilingCategory.FORM_4,
            confidence=0.85,
            classification_method="filename",
            cik="320187",
            target_nodes=[1],
        )
        d = fc.to_dict()
        assert d["category"] == "4"
        assert d["confidence"] == 0.85
        assert d["cik"] == "320187"
        assert d["target_nodes"] == [1]

    def test_to_dict_with_none_values(self):
        """Test serialization handles None values gracefully."""
        fc = FilingClassification(
            file_path="",
            file_name="",
            file_extension="",
            file_size_bytes=0,
            category=FilingCategory.UNKNOWN,
            confidence=0.0,
            classification_method="none",
        )
        d = fc.to_dict()
        assert d["filing_date"] is None
        assert d["accession_number"] is None


class TestFilingClassifier:
    """Test FilingClassifier functionality."""

    def test_init_without_xbrl(self):
        """FilingClassifier should initialize without XBRL index."""
        classifier = FilingClassifier(cik="320187", company_name="NIKE, Inc.")
        assert classifier.cik == "320187"
        assert classifier.company_name == "NIKE, Inc."
        assert classifier.xbrl_index is None

    def test_classify_from_filename_form4(self):
        """Test filename-based classification for Form 4."""
        classifier = FilingClassifier()
        with tempfile.NamedTemporaryFile(suffix=".pdf", prefix="form4_", delete=False) as f:
            f.write(b"test content")
            path = Path(f.name)

        result = classifier.classify_file(path)
        assert result.category == FilingCategory.FORM_4
        assert result.confidence > 0
        path.unlink()

    def test_classify_from_filename_10k(self):
        """Test filename-based classification for 10-K."""
        classifier = FilingClassifier()
        with tempfile.NamedTemporaryFile(suffix=".pdf", prefix="10-K_", delete=False) as f:
            f.write(b"test content")
            path = Path(f.name)

        result = classifier.classify_file(path)
        assert result.category == FilingCategory.FORM_10K
        path.unlink()

    def test_classify_from_filename_def14a(self):
        """Test filename-based classification for DEF 14A."""
        classifier = FilingClassifier()
        with tempfile.NamedTemporaryFile(suffix=".pdf", prefix="def14a_", delete=False) as f:
            f.write(b"test content")
            path = Path(f.name)

        result = classifier.classify_file(path)
        assert result.category == FilingCategory.DEF_14A
        path.unlink()

    def test_classify_unknown_filename(self):
        """Test classification of file with non-SEC filename."""
        classifier = FilingClassifier()
        with tempfile.NamedTemporaryFile(suffix=".pdf", prefix="random_uuid_", delete=False) as f:
            f.write(b"test content")
            path = Path(f.name)

        result = classifier.classify_file(path)
        assert result.category == FilingCategory.UNKNOWN
        path.unlink()

    def test_classify_from_content(self):
        """Test content-based classification for text files."""
        classifier = FilingClassifier()
        with tempfile.NamedTemporaryFile(suffix=".txt", prefix="filing_", delete=False, mode="w") as f:
            f.write("STATEMENT OF CHANGES IN BENEFICIAL OWNERSHIP OF SECURITIES")
            path = Path(f.name)

        result = classifier.classify_file(path)
        assert result.category == FilingCategory.FORM_4
        assert result.classification_method == "content"
        path.unlink()

    def test_classify_corpus_empty_dir(self):
        """Test corpus classification on empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            classifier = FilingClassifier(corpus_root=Path(tmpdir))
            report = classifier.classify_corpus()
            assert report.total_files == 0
            assert report.classified_files == 0

    def test_classify_corpus_with_files(self):
        """Test corpus classification with mixed files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            (Path(tmpdir) / "form4_insider.pdf").write_bytes(b"test")
            (Path(tmpdir) / "10-K_annual.pdf").write_bytes(b"test")
            (Path(tmpdir) / "random_file.pdf").write_bytes(b"test")

            classifier = FilingClassifier(corpus_root=Path(tmpdir))
            report = classifier.classify_corpus()

            assert report.total_files == 3
            assert report.classified_files >= 2  # form4 and 10-K

    def test_get_filings_for_node(self):
        """Test filtering classifications by pipeline node."""
        classifier = FilingClassifier()
        report = ClassificationReport(
            classifications=[
                FilingClassification(
                    file_path="a.pdf", file_name="a.pdf", file_extension=".pdf",
                    file_size_bytes=100, category=FilingCategory.FORM_4,
                    confidence=0.9, classification_method="filename",
                    target_nodes=[1],
                ),
                FilingClassification(
                    file_path="b.pdf", file_name="b.pdf", file_extension=".pdf",
                    file_size_bytes=200, category=FilingCategory.FORM_10K,
                    confidence=0.8, classification_method="filename",
                    target_nodes=[4],
                ),
            ]
        )

        node1_filings = classifier.get_filings_for_node(report, 1)
        assert len(node1_filings) == 1
        assert node1_filings[0].category == FilingCategory.FORM_4

        node4_filings = classifier.get_filings_for_node(report, 4)
        assert len(node4_filings) == 1

    def test_to_sec_filings(self):
        """Test conversion to JLAW SECFiling objects."""
        classifier = FilingClassifier(cik="320187", company_name="NIKE, Inc.")
        classifications = [
            FilingClassification(
                file_path="/data/form4.pdf",
                file_name="form4.pdf",
                file_extension=".pdf",
                file_size_bytes=100,
                category=FilingCategory.FORM_4,
                confidence=0.9,
                classification_method="filename",
                content_hash="abc123def456",
            ),
        ]

        sec_filings = classifier.to_sec_filings(classifications)
        assert len(sec_filings) == 1
        assert sec_filings[0].form_type == "4"
        assert sec_filings[0].cik == "320187"

    def test_to_sec_filings_skips_unknown(self):
        """Unknown classifications should be skipped in conversion."""
        classifier = FilingClassifier()
        classifications = [
            FilingClassification(
                file_path="/data/unknown.pdf",
                file_name="unknown.pdf",
                file_extension=".pdf",
                file_size_bytes=100,
                category=FilingCategory.UNKNOWN,
                confidence=0.0,
                classification_method="none",
                content_hash="abc123",
            ),
        ]

        sec_filings = classifier.to_sec_filings(classifications)
        assert len(sec_filings) == 0

    def test_form_type_to_category_mapping(self):
        """Test static form type to category mapping."""
        assert FilingClassifier._form_type_to_category("4") == FilingCategory.FORM_4
        assert FilingClassifier._form_type_to_category("10-K") == FilingCategory.FORM_10K
        assert FilingClassifier._form_type_to_category("10-K/A") == FilingCategory.FORM_10K
        assert FilingClassifier._form_type_to_category("DEF 14A") == FilingCategory.DEF_14A
        assert FilingClassifier._form_type_to_category("SC 13D") == FilingCategory.SCHEDULE_13D
        assert FilingClassifier._form_type_to_category("UNKNOWN_FORM") is None

    def test_extract_accession_number(self):
        """Test accession number extraction from text."""
        assert FilingClassifier._extract_accession_number(
            "/data/0000320187-19-000042/form4.xml"
        ) == "0000320187-19-000042"
        assert FilingClassifier._extract_accession_number("no-accession-here") is None

    def test_export_report(self):
        """Test classification report export to JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            classifier = FilingClassifier()
            report = ClassificationReport(
                total_files=5,
                classified_files=3,
                unclassified_files=2,
            )
            output_path = Path(tmpdir) / "report.json"
            result_path = classifier.export_report(report, output_path)

            assert result_path.exists()
            with open(result_path) as f:
                data = json.load(f)
            assert data["summary"]["total_files"] == 5


# ═══════════════════════════════════════════════════════════════════════
# CIKValidator Tests
# ═══════════════════════════════════════════════════════════════════════


class TestCIKValidator:
    """Test CIKValidator functionality."""

    def test_normalize_cik(self):
        """Test CIK normalization removes leading zeros."""
        assert CIKValidator.normalize_cik("0000320187") == "320187"
        assert CIKValidator.normalize_cik("320187") == "320187"
        assert CIKValidator.normalize_cik("000") == "0"

    def test_pad_cik(self):
        """Test CIK zero-padding to 10 digits."""
        assert CIKValidator.pad_cik("320187") == "0000320187"
        assert CIKValidator.pad_cik("0000320187") == "0000320187"

    def test_validate_format_valid(self):
        """Test format validation for valid CIK."""
        validator = CIKValidator()
        result = validator.validate_format("320187")
        assert result.is_valid
        assert result.cik == "320187"
        assert result.cik_padded == "0000320187"

    def test_validate_format_known_cik(self):
        """Test validation recognizes known CIK mappings."""
        validator = CIKValidator()
        result = validator.validate_format("320187")
        assert result.is_valid
        assert result.company_name == "NIKE, Inc."
        assert result.validation_method == "known_mapping"

    def test_validate_format_empty(self):
        """Test validation fails for empty CIK."""
        validator = CIKValidator()
        result = validator.validate_format("")
        assert not result.is_valid
        assert len(result.errors) > 0

    def test_validate_format_too_long(self):
        """Test validation fails for CIK exceeding 10 digits."""
        validator = CIKValidator()
        result = validator.validate_format("12345678901")
        assert not result.is_valid

    def test_validate_offline_without_xbrl(self):
        """Test offline validation without XBRL data."""
        validator = CIKValidator()
        result = validator.validate_offline("320187")
        # Should still pass format validation
        assert result.is_valid
        assert "No XBRL data loaded" in result.errors[0]

    def test_validate_offline_with_xbrl(self):
        """Test offline validation with XBRL data."""
        with tempfile.NamedTemporaryFile(
            suffix=".json", delete=False, mode="w"
        ) as f:
            json.dump({
                "cik": 320187,
                "entityName": "NIKE, Inc.",
                "facts": {
                    "us-gaap": {
                        "Revenue": {
                            "units": {
                                "USD": [
                                    {"val": 39117000000, "fy": 2019, "form": "10-K", "filed": "2019-07-25"}
                                ]
                            }
                        }
                    }
                }
            }, f)
            xbrl_path = Path(f.name)

        validator = CIKValidator(xbrl_index_path=xbrl_path)
        result = validator.validate_offline("320187")
        assert result.is_valid
        assert result.company_name == "NIKE, Inc."
        assert result.validation_method == "xbrl_index"
        assert result.xbrl_fact_count > 0
        xbrl_path.unlink()

    def test_validate_batch(self):
        """Test batch CIK validation."""
        validator = CIKValidator()
        results = validator.validate_batch(["320187", "789019", "invalid"])
        assert len(results) == 3
        assert results["320187"].is_valid
        assert results["789019"].is_valid

    def test_validation_result_to_dict(self):
        """Test CIKValidationResult serialization."""
        result = CIKValidationResult(
            cik="320187",
            cik_padded="0000320187",
            is_valid=True,
            company_name="NIKE, Inc.",
            validation_method="known_mapping",
            validation_timestamp=datetime(2024, 1, 1),
        )
        d = result.to_dict()
        assert d["cik"] == "320187"
        assert d["is_valid"] is True
        assert d["company_name"] == "NIKE, Inc."

    def test_export_validation_report(self):
        """Test validation report export to JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            validator = CIKValidator()
            results = validator.validate_batch(["320187"])
            output_path = Path(tmpdir) / "validation.json"
            validator.export_validation_report(results, output_path)

            assert output_path.exists()
            with open(output_path) as f:
                data = json.load(f)
            assert data["validation_report"]["total_ciks"] == 1


# ═══════════════════════════════════════════════════════════════════════
# ClaudeCompositor Tests
# ═══════════════════════════════════════════════════════════════════════


class TestClaudeCompositor:
    """Test ClaudeCompositor functionality."""

    def test_init_defaults(self):
        """Test compositor initialization with defaults."""
        comp = ClaudeCompositor()
        assert comp.mode == CompositorMode.MULTI_AGENT
        assert comp.max_cost_usd == 2.0
        assert len(comp.agent_configs) == len(DEFAULT_AGENT_CONFIGS)
        assert comp.enable_cross_validation is True

    def test_init_custom_mode(self):
        """Test compositor initialization with custom mode."""
        comp = ClaudeCompositor(
            mode=CompositorMode.SINGLE_AGENT,
            max_cost_usd=5.0,
        )
        assert comp.mode == CompositorMode.SINGLE_AGENT
        assert comp.max_cost_usd == 5.0

    def test_get_enabled_agents(self):
        """Test getting enabled agents."""
        comp = ClaudeCompositor()
        enabled = comp.get_enabled_agents()
        assert len(enabled) == len(DEFAULT_AGENT_CONFIGS)
        assert all(a.enabled for a in enabled)

    def test_get_agent_by_id(self):
        """Test agent lookup by ID."""
        comp = ClaudeCompositor()
        agent = comp.get_agent_by_id("insider-trading-analyst")
        assert agent is not None
        assert agent.agent_name == "Insider Trading Analyst"

    def test_get_agent_by_id_not_found(self):
        """Test agent lookup for non-existent ID."""
        comp = ClaudeCompositor()
        agent = comp.get_agent_by_id("nonexistent-agent")
        assert agent is None

    def test_get_usage_stats(self):
        """Test usage statistics reporting."""
        comp = ClaudeCompositor(max_cost_usd=10.0)
        stats = comp.get_usage_stats()
        assert stats["total_tokens_used"] == 0
        assert stats["total_cost_usd"] == 0.0
        assert stats["budget_remaining_usd"] == 10.0
        assert stats["mode"] == "multi_agent"

    def test_compositor_result_to_dict(self):
        """Test CompositorResult serialization."""
        result = CompositorResult(
            compositor_id="comp-123",
            mode=CompositorMode.MULTI_AGENT,
            scope=AnalysisScope.FILING_LEVEL,
            status="success",
            agents_invoked=3,
            agents_succeeded=3,
            violations_detected=5,
        )
        d = result.to_dict()
        assert d["compositor_id"] == "comp-123"
        assert d["mode"] == "multi_agent"
        assert d["scope"] == "filing_level"
        assert d["violations_detected"] == 5

    def test_agent_config_to_dict(self):
        """Test AgentConfig serialization."""
        config = AgentConfig(
            agent_id="test-agent",
            agent_name="Test Agent",
            specialization="testing",
        )
        d = config.to_dict()
        assert d["agent_id"] == "test-agent"
        assert d["specialization"] == "testing"

    def test_agents_for_filing_type_routing(self):
        """Test filing type to agent routing."""
        comp = ClaudeCompositor()
        form4_agents = comp._get_agents_for_filing_type("4")
        assert any(a.agent_id == "insider-trading-analyst" for a in form4_agents)

        def14a_agents = comp._get_agents_for_filing_type("DEF 14A")
        assert any(a.agent_id == "compensation-analyst" for a in def14a_agents)

        tenk_agents = comp._get_agents_for_filing_type("10-K")
        assert any(
            a.agent_id == "financial-statement-analyst" for a in tenk_agents
        )

    def test_default_agent_configs_complete(self):
        """Test that all 10 default agent configs are present."""
        assert len(DEFAULT_AGENT_CONFIGS) == 10
        ids = {a.agent_id for a in DEFAULT_AGENT_CONFIGS}
        assert "insider-trading-analyst" in ids
        assert "compensation-analyst" in ids
        assert "financial-statement-analyst" in ids
        assert "beneficial-ownership-analyst" in ids
        assert "material-event-analyst" in ids
        assert "institutional-holdings-analyst" in ids
        assert "network-intelligence-analyst" in ids
        assert "quantitative-forensics-analyst" in ids
        assert "market-correlation-analyst" in ids
        assert "cross-validation-analyst" in ids
