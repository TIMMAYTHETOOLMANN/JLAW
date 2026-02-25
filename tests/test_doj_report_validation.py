"""
DOJ Report Validation Tests
============================

Tests to validate DOJ-level forensic report generation quality.
Ensures reports meet Nike 2019 baseline standards and include
all required components for prosecution-ready documentation.

Quality Gates:
- Executive summary completeness
- Per-filing breakdown structure
- Exact quote extraction
- Statutory citation accuracy
- Dual-agent consensus tracking
- Chain of custody documentation
"""

import json
import pytest
from datetime import datetime
from pathlib import Path
from typing import List
from unittest.mock import MagicMock

# Import reporting modules
from src.reporting.models import (
    SeverityLevel,
    ProsecutorialMerit,
    AgentSource,
    StatutoryReference,
    ExactQuote,
    DamageEstimate,
    RedFlag,
    ViolationEvidence,
    DualAgentConsensus,
    FilingAnalysisReport,
    ChainOfCustodyRecord,
    ForensicReportSummary,
)
from src.reporting.doj_report_generator import (
    DOJReportGenerator,
    create_violation_evidence,
)
from src.reporting.constants import (
    SeverityTier,
    ViolationType,
    SEC_STATUTES,
    NIKE_2019_BASELINE,
    get_statute_for_violation,
    calculate_penalty_range,
)


class TestDOJReportGenerator:
    """Test DOJ report generation functionality."""
    
    @pytest.fixture
    def output_dir(self, tmp_path: Path) -> Path:
        """Create temporary output directory."""
        output = tmp_path / "reports"
        output.mkdir(parents=True, exist_ok=True)
        return output
    
    @pytest.fixture
    def sample_violation(self) -> ViolationEvidence:
        """Create sample violation for testing."""
        return ViolationEvidence(
            violation_id="V-TEST-001",
            violation_type="LATE_FORM4",
            severity=SeverityLevel.HIGH,
            statutory_reference=StatutoryReference(
                citation="15 U.S.C. § 78p(a)",
                title="Section 16(a) - Insider Reporting Requirements",
                summary="Directors and officers must file Form 4 within 2 business days.",
            ),
            description="Form 4 filing delayed by 5 business days",
            exact_quotes=[
                ExactQuote(
                    quote_text="Transaction Date: 2019-03-15, Filed: 2019-03-22",
                    document_url="https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany",
                    document_section="Transaction Table",
                )
            ],
            document_url="https://www.sec.gov/example",
            document_section="Transactions",
            filing_accession="0001234567-19-000001",
            filing_date="2019-03-22",
            prosecutorial_merit=ProsecutorialMerit.STRONG,
            damage_estimate=DamageEstimate(
                civil_minimum=5000.0,
                civil_maximum=25000.0,
                disgorgement_estimate=0.0,
                criminal_exposure=False,
                prison_years_maximum=0,
                calculation_methodology="SEC civil penalty guidelines"
            ),
            detected_by=AgentSource.OPENAI,
            confirmed_by=[AgentSource.ANTHROPIC],
            evidence_hash="abc123def456",
        )
    
    @pytest.fixture
    def sample_filing_report(self, sample_violation: ViolationEvidence) -> FilingAnalysisReport:
        """Create sample filing report for testing."""
        return FilingAnalysisReport(
            accession_number="0001234567-19-000001",
            filing_type="Form 4",
            filing_date="2019-03-22",
            company_name="NIKE, Inc.",
            cik="320187",
            document_url="https://www.sec.gov/example",
            violations=[sample_violation],
            red_flags=[
                RedFlag(
                    flag_type="TIMING",
                    description="Filing submitted on Friday afternoon",
                    significance=SeverityLevel.MEDIUM,
                )
            ],
            dual_agent_consensus=DualAgentConsensus(
                openai_findings_count=1,
                anthropic_findings_count=1,
                overlap_count=1,
                openai_unique_count=0,
                anthropic_unique_count=0,
                confidence_level=0.95,
            ),
        )
    
    @pytest.fixture
    def sample_custody_records(self) -> List[ChainOfCustodyRecord]:
        """Create sample custody records."""
        return [
            ChainOfCustodyRecord(
                record_id="COC-001",
                evidence_type="document",
                evidence_description="Form 4 filing collected from SEC EDGAR",
                collected_at=datetime.utcnow(),
                collected_by="JLAW SEC Client",
                storage_location="/data/filings",
                sha256_hash="abcdef123456789",
                verification_status="verified",
            ),
            ChainOfCustodyRecord(
                record_id="COC-002",
                evidence_type="analysis",
                evidence_description="Violation analysis completed",
                collected_at=datetime.utcnow(),
                collected_by="JLAW Analysis Engine",
                storage_location="/data/analysis",
                sha256_hash="fedcba987654321",
                verification_status="verified",
            ),
        ]
    
    def test_generator_initialization(self, output_dir: Path):
        """Test DOJ report generator initialization."""
        generator = DOJReportGenerator(output_dir=str(output_dir))
        assert generator.output_dir.exists()
    
    def test_comprehensive_report_generation(
        self,
        output_dir: Path,
        sample_filing_report: FilingAnalysisReport,
        sample_custody_records: List[ChainOfCustodyRecord]
    ):
        """Test comprehensive report generation."""
        generator = DOJReportGenerator(output_dir=str(output_dir))
        
        outputs = generator.generate_comprehensive_report(
            case_id="JLAW-320187-TEST",
            company_name="NIKE, Inc.",
            cik="320187",
            filing_reports=[sample_filing_report],
            chain_of_custody=sample_custody_records,
            output_formats=['markdown', 'json']
        )
        
        # Check outputs were generated
        assert 'markdown' in outputs
        assert 'json' in outputs
        assert outputs['markdown'].exists()
        assert outputs['json'].exists()
    
    def test_markdown_report_structure(
        self,
        output_dir: Path,
        sample_filing_report: FilingAnalysisReport,
        sample_custody_records: List[ChainOfCustodyRecord]
    ):
        """Test markdown report has required sections."""
        generator = DOJReportGenerator(output_dir=str(output_dir))
        
        outputs = generator.generate_comprehensive_report(
            case_id="JLAW-320187-TEST",
            company_name="NIKE, Inc.",
            cik="320187",
            filing_reports=[sample_filing_report],
            chain_of_custody=sample_custody_records,
            output_formats=['markdown']
        )
        
        # Read generated report
        with open(outputs['markdown'], 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for required sections
        required_sections = [
            "EXECUTIVE SUMMARY",
            "Target Information",
            "Violation Summary",
            "Financial Impact",
            "Regulatory Routing",
            "PER-FILING DETAILED ANALYSIS",
            "DUAL-AGENT CONSENSUS",
            "CHAIN OF CUSTODY",
        ]
        
        for section in required_sections:
            assert section in content, f"Missing required section: {section}"
    
    def test_violation_details_in_report(
        self,
        output_dir: Path,
        sample_filing_report: FilingAnalysisReport,
        sample_custody_records: List[ChainOfCustodyRecord]
    ):
        """Test violation details are properly included."""
        generator = DOJReportGenerator(output_dir=str(output_dir))
        
        outputs = generator.generate_comprehensive_report(
            case_id="JLAW-320187-TEST",
            company_name="NIKE, Inc.",
            cik="320187",
            filing_reports=[sample_filing_report],
            chain_of_custody=sample_custody_records,
            output_formats=['markdown']
        )
        
        with open(outputs['markdown'], 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check violation details
        assert "LATE_FORM4" in content
        assert "15 U.S.C. § 78p(a)" in content
        assert "Form 4 filing delayed" in content
        assert "Exact Quotes from Filing" in content
    
    def test_json_report_structure(
        self,
        output_dir: Path,
        sample_filing_report: FilingAnalysisReport,
        sample_custody_records: List[ChainOfCustodyRecord]
    ):
        """Test JSON report has correct structure."""
        generator = DOJReportGenerator(output_dir=str(output_dir))
        
        outputs = generator.generate_comprehensive_report(
            case_id="JLAW-320187-TEST",
            company_name="NIKE, Inc.",
            cik="320187",
            filing_reports=[sample_filing_report],
            chain_of_custody=sample_custody_records,
            output_formats=['json']
        )
        
        with open(outputs['json'], 'r') as f:
            data = json.load(f)
        
        # Check required keys
        assert 'metadata' in data
        assert 'summary' in data
        assert 'filing_reports' in data
        assert 'chain_of_custody' in data
        assert 'report_hash' in data
        
        # Check summary structure (nested format)
        summary = data['summary']
        assert 'case_id' in summary
        assert 'violations' in summary
        assert 'total' in summary['violations']
    
    def test_create_violation_evidence_factory(self):
        """Test violation evidence factory function."""
        violation = create_violation_evidence(
            violation_id="V-FACTORY-001",
            violation_type="LATE_FORM4",
            severity="HIGH",
            citation="15 U.S.C. § 78p(a)",
            description="Late Form 4 filing",
            document_url="https://example.com",
            filing_accession="0001234567-19-000001",
            filing_date="2019-03-22",
            quote_text="Transaction delayed by 5 days",
            detected_by="openai"
        )
        
        assert violation.violation_id == "V-FACTORY-001"
        assert violation.severity == SeverityLevel.HIGH
        assert len(violation.exact_quotes) == 1
        assert violation.detected_by == AgentSource.OPENAI
        assert violation.evidence_hash != ""


class TestNike2019Baseline:
    """Tests for Nike 2019 baseline compliance."""
    
    def test_baseline_sections_defined(self):
        """Test Nike 2019 baseline has required sections."""
        baseline = NIKE_2019_BASELINE
        
        assert baseline['company'] == "NIKE, Inc."
        assert baseline['cik'] == "320187"
        assert baseline['reference_standard'] is True
        assert 'expected_sections' in baseline
        assert 'minimum_quality_metrics' in baseline
    
    def test_baseline_quality_metrics(self):
        """Test Nike 2019 quality metrics are properly defined."""
        metrics = NIKE_2019_BASELINE['minimum_quality_metrics']
        
        assert 'exact_quotes_per_violation' in metrics
        assert 'statutory_citations_per_violation' in metrics
        assert 'chain_of_custody_records' in metrics
        assert 'dual_agent_validation' in metrics
        assert 'damage_estimation' in metrics


class TestStatutoryReferences:
    """Tests for statutory reference handling."""
    
    def test_sec_statutes_database(self):
        """Test SEC statutes database is populated."""
        assert len(SEC_STATUTES) > 0
        
        # Check key statutes exist
        assert "15_USC_78p_a" in SEC_STATUTES  # Section 16(a)
        assert "15_USC_78j_b" in SEC_STATUTES  # Section 10(b)
        assert "15_USC_7241" in SEC_STATUTES   # SOX 302
    
    def test_get_statute_for_violation(self):
        """Test statute lookup for violation types."""
        statute = get_statute_for_violation(ViolationType.LATE_FORM4)
        
        assert statute is not None
        assert "78p" in statute.citation
        assert statute.default_severity == SeverityTier.HIGH
    
    def test_calculate_penalty_range(self):
        """Test penalty range calculation."""
        min_penalty, max_penalty = calculate_penalty_range(
            ViolationType.LATE_FORM4,
            SeverityTier.HIGH,
            profit_amount=10000.0
        )
        
        assert min_penalty > 0
        assert max_penalty > min_penalty


class TestViolationModels:
    """Tests for violation data models."""
    
    def test_violation_evidence_to_dict(self):
        """Test ViolationEvidence serialization."""
        violation = ViolationEvidence(
            violation_id="V-TEST-001",
            violation_type="LATE_FORM4",
            severity=SeverityLevel.HIGH,
            statutory_reference=StatutoryReference(
                citation="15 U.S.C. § 78p(a)",
                title="Section 16(a)",
                summary="Insider reporting",
            ),
            description="Late filing",
            exact_quotes=[],
            document_url="https://example.com",
            document_section="Transactions",
            filing_accession="0001234567-19-000001",
            filing_date="2019-03-22",
            prosecutorial_merit=ProsecutorialMerit.STRONG,
            damage_estimate=DamageEstimate(
                civil_minimum=5000.0,
                civil_maximum=25000.0,
                disgorgement_estimate=0.0,
                criminal_exposure=False,
                prison_years_maximum=0,
                calculation_methodology="Standard"
            ),
            detected_by=AgentSource.PATTERN,
            evidence_hash="test123",
        )
        
        data = violation.to_dict()
        
        assert data['violation_id'] == "V-TEST-001"
        assert data['severity'] == "HIGH"
        assert data['prosecutorial_merit'] == "STRONG"
        assert data['detected_by'] == "pattern"
    
    def test_filing_analysis_report_properties(self):
        """Test FilingAnalysisReport computed properties."""
        report = FilingAnalysisReport(
            accession_number="0001234567-19-000001",
            filing_type="Form 4",
            filing_date="2019-03-22",
            company_name="Test Corp",
            cik="123456",
            document_url="https://example.com",
            violations=[
                ViolationEvidence(
                    violation_id="V-1",
                    violation_type="LATE_FORM4",
                    severity=SeverityLevel.CRITICAL,
                    statutory_reference=StatutoryReference("", "", ""),
                    description="Critical violation",
                    exact_quotes=[],
                    document_url="",
                    document_section="",
                    filing_accession="",
                    filing_date="",
                    prosecutorial_merit=ProsecutorialMerit.STRONG,
                    damage_estimate=DamageEstimate(
                        civil_minimum=100000.0,
                        civil_maximum=500000.0,
                        disgorgement_estimate=0.0,
                        criminal_exposure=True,
                        prison_years_maximum=20,
                        calculation_methodology="Standard"
                    ),
                    detected_by=AgentSource.BOTH,
                    evidence_hash="",
                ),
                ViolationEvidence(
                    violation_id="V-2",
                    violation_type="LATE_FORM4",
                    severity=SeverityLevel.HIGH,
                    statutory_reference=StatutoryReference("", "", ""),
                    description="High violation",
                    exact_quotes=[],
                    document_url="",
                    document_section="",
                    filing_accession="",
                    filing_date="",
                    prosecutorial_merit=ProsecutorialMerit.MODERATE,
                    damage_estimate=DamageEstimate(
                        civil_minimum=10000.0,
                        civil_maximum=50000.0,
                        disgorgement_estimate=0.0,
                        criminal_exposure=False,
                        prison_years_maximum=0,
                        calculation_methodology="Standard"
                    ),
                    detected_by=AgentSource.OPENAI,
                    evidence_hash="",
                ),
            ],
            red_flags=[],
        )
        
        assert report.violation_count == 2
        assert report.critical_count == 1
        assert report.high_count == 1
        assert report.total_estimated_damages == 550000.0
        assert report.requires_criminal_referral is True
    
    def test_dual_agent_consensus_agreement_ratio(self):
        """Test DualAgentConsensus agreement ratio calculation."""
        consensus = DualAgentConsensus(
            openai_findings_count=5,
            anthropic_findings_count=5,
            overlap_count=4,
            openai_unique_count=1,
            anthropic_unique_count=1,
            confidence_level=0.9,
        )
        
        # Agreement ratio = 2 * overlap / total
        # = 2 * 4 / 10 = 0.8
        assert consensus.agreement_ratio == 0.8


class TestDocumentationProfileV3:
    """Tests for v3.0 documentation profile structure."""

    def test_profile_version_is_3(self):
        """Profile version must be 3.0."""
        from src.reporting.output_documentation_config import get_output_documentation_profile
        profile = get_output_documentation_profile()
        assert profile.profile_version == "3.0"

    def test_profile_has_15_required_sections(self):
        """Profile must declare exactly 15 required sections."""
        from src.reporting.output_documentation_config import get_output_documentation_profile
        profile = get_output_documentation_profile()
        assert len(profile.required_sections) == 15

    def test_required_sections_are_numbered(self):
        """Every required section must have a unique positive section_number."""
        from src.reporting.output_documentation_config import get_output_documentation_profile
        profile = get_output_documentation_profile()
        numbers = [s.section_number for s in profile.required_sections]
        assert all(n > 0 for n in numbers)
        assert len(set(numbers)) == len(numbers), "Section numbers must be unique"

    def test_required_sections_have_phase_alignment(self):
        """Every required section must declare a pipeline phase alignment."""
        from src.reporting.output_documentation_config import get_output_documentation_profile
        profile = get_output_documentation_profile()
        for section in profile.required_sections:
            assert section.phase_alignment, f"Section {section.name} lacks phase_alignment"

    def test_profile_has_8_visual_requirements(self):
        """Profile must declare exactly 8 visual requirements."""
        from src.reporting.output_documentation_config import get_output_documentation_profile
        profile = get_output_documentation_profile()
        assert len(profile.visual_requirements) == 8

    def test_visual_requirements_have_generator_module(self):
        """Every visual requirement must reference a generator module."""
        from src.reporting.output_documentation_config import get_output_documentation_profile
        profile = get_output_documentation_profile()
        for visual in profile.visual_requirements:
            assert visual.generator_module, f"Visual {visual.key} lacks generator_module"

    def test_profile_has_compliance_standards(self):
        """Profile must declare at least 4 compliance standards."""
        from src.reporting.output_documentation_config import get_output_documentation_profile
        profile = get_output_documentation_profile()
        assert len(profile.compliance_standards) >= 4

    def test_compliance_standards_include_fre_902(self):
        """FRE 902(13) and FRE 902(14) must be in compliance standards."""
        from src.reporting.output_documentation_config import get_output_documentation_profile
        profile = get_output_documentation_profile()
        ids = {std.standard_id for std in profile.compliance_standards}
        assert "FRE_902_13" in ids
        assert "FRE_902_14" in ids

    def test_profile_has_pipeline_stage_audits(self):
        """Profile must declare 9 pipeline stage audits."""
        from src.reporting.output_documentation_config import get_output_documentation_profile
        profile = get_output_documentation_profile()
        assert len(profile.pipeline_stage_audits) == 9

    def test_profile_has_output_file_requirements(self):
        """Profile must declare output file requirements with at least 5 required files."""
        from src.reporting.output_documentation_config import get_output_documentation_profile
        profile = get_output_documentation_profile()
        required = [f for f in profile.output_file_requirements if f.required]
        assert len(required) >= 5

    def test_quality_thresholds_expanded(self):
        """Quality thresholds must include pipeline and compliance gates."""
        from src.reporting.output_documentation_config import get_output_documentation_profile
        profile = get_output_documentation_profile()
        qt = profile.quality_thresholds
        assert "minimum_pipeline_phases_completed" in qt
        assert "minimum_node_success_rate" in qt
        assert "minimum_detection_patterns_executed" in qt
        assert "evidence_hash_algorithms_required" in qt
        assert "compliance_standards_referenced" in qt
        assert qt["evidence_hash_algorithms_required"] == 3

    def test_profile_to_dict_includes_new_fields(self):
        """to_dict() must include compliance_standards and pipeline_stage_audits."""
        from src.reporting.output_documentation_config import get_output_documentation_profile
        profile = get_output_documentation_profile()
        d = profile.to_dict()
        assert "compliance_standards" in d
        assert "pipeline_stage_audits" in d
        assert "output_file_requirements" in d
        assert len(d["compliance_standards"]) == len(profile.compliance_standards)
        assert len(d["pipeline_stage_audits"]) == len(profile.pipeline_stage_audits)

    def test_section_requirement_fields_include_section_number(self):
        """to_dict() section entries must include section_number and phase_alignment."""
        from src.reporting.output_documentation_config import get_output_documentation_profile
        profile = get_output_documentation_profile()
        d = profile.to_dict()
        for section in d["required_sections"]:
            assert "section_number" in section
            assert "phase_alignment" in section


class TestMarkdownReportNewSections:
    """Tests for new v3.0 sections in Markdown report output."""

    @pytest.fixture
    def output_dir(self, tmp_path: Path) -> Path:
        output = tmp_path / "reports"
        output.mkdir(parents=True, exist_ok=True)
        return output

    @pytest.fixture
    def sample_filing_report(self) -> FilingAnalysisReport:
        return FilingAnalysisReport(
            accession_number="0001234567-19-000001",
            filing_type="Form 4",
            filing_date="2019-03-22",
            company_name="NIKE, Inc.",
            cik="320187",
            document_url="https://www.sec.gov/example",
            violations=[
                ViolationEvidence(
                    violation_id="V-TEST-001",
                    violation_type="LATE_FORM4",
                    severity=SeverityLevel.HIGH,
                    statutory_reference=StatutoryReference(
                        citation="15 U.S.C. § 78p(a)",
                        title="Section 16(a)",
                        summary="Insider reporting",
                    ),
                    description="Late Form 4 filing",
                    exact_quotes=[
                        ExactQuote(
                            quote_text="Transaction Date: 2019-03-15",
                            document_url="https://www.sec.gov/ex",
                            document_section="Transactions",
                        )
                    ],
                    document_url="https://www.sec.gov/example",
                    document_section="Transactions",
                    filing_accession="0001234567-19-000001",
                    filing_date="2019-03-22",
                    prosecutorial_merit=ProsecutorialMerit.STRONG,
                    damage_estimate=DamageEstimate(
                        civil_minimum=5000.0,
                        civil_maximum=25000.0,
                        disgorgement_estimate=0.0,
                        criminal_exposure=False,
                        prison_years_maximum=0,
                        calculation_methodology="Standard"
                    ),
                    detected_by=AgentSource.OPENAI,
                    confirmed_by=[AgentSource.ANTHROPIC],
                    evidence_hash="abc123",
                ),
            ],
            red_flags=[],
            dual_agent_consensus=DualAgentConsensus(
                openai_findings_count=1,
                anthropic_findings_count=1,
                overlap_count=1,
                openai_unique_count=0,
                anthropic_unique_count=0,
                confidence_level=0.95,
            ),
        )

    @pytest.fixture
    def sample_custody_records(self) -> list:
        return [
            ChainOfCustodyRecord(
                record_id="COC-001",
                evidence_type="document",
                evidence_description="Form 4 filing",
                collected_at=datetime.utcnow(),
                collected_by="JLAW SEC Client",
                storage_location="/data/filings",
                sha256_hash="abcdef123456789",
                verification_status="verified",
            ),
        ]

    def test_markdown_contains_detection_pattern_section(
        self, output_dir, sample_filing_report, sample_custody_records
    ):
        """Markdown report must include Detection Pattern Analysis section."""
        generator = DOJReportGenerator(output_dir=str(output_dir))
        outputs = generator.generate_comprehensive_report(
            case_id="JLAW-TEST",
            company_name="NIKE, Inc.",
            cik="320187",
            filing_reports=[sample_filing_report],
            chain_of_custody=sample_custody_records,
            output_formats=["markdown"],
        )
        content = outputs["markdown"].read_text(encoding="utf-8")
        assert "DETECTION PATTERN ANALYSIS" in content

    def test_markdown_contains_penalty_assessment_section(
        self, output_dir, sample_filing_report, sample_custody_records
    ):
        """Markdown report must include Penalty Assessment Matrix section."""
        generator = DOJReportGenerator(output_dir=str(output_dir))
        outputs = generator.generate_comprehensive_report(
            case_id="JLAW-TEST",
            company_name="NIKE, Inc.",
            cik="320187",
            filing_reports=[sample_filing_report],
            chain_of_custody=sample_custody_records,
            output_formats=["markdown"],
        )
        content = outputs["markdown"].read_text(encoding="utf-8")
        assert "PENALTY ASSESSMENT MATRIX" in content

    def test_markdown_contains_compliance_standards_section(
        self, output_dir, sample_filing_report, sample_custody_records
    ):
        """Markdown report must include Compliance Standards Declaration section."""
        generator = DOJReportGenerator(output_dir=str(output_dir))
        outputs = generator.generate_comprehensive_report(
            case_id="JLAW-TEST",
            company_name="NIKE, Inc.",
            cik="320187",
            filing_reports=[sample_filing_report],
            chain_of_custody=sample_custody_records,
            output_formats=["markdown"],
        )
        content = outputs["markdown"].read_text(encoding="utf-8")
        assert "COMPLIANCE STANDARDS DECLARATION" in content
        assert "FRE_902_13" in content

    def test_markdown_documentation_profile_header(
        self, output_dir, sample_filing_report, sample_custody_records
    ):
        """Markdown report header must include documentation profile version."""
        generator = DOJReportGenerator(output_dir=str(output_dir))
        outputs = generator.generate_comprehensive_report(
            case_id="JLAW-TEST",
            company_name="NIKE, Inc.",
            cik="320187",
            filing_reports=[sample_filing_report],
            chain_of_custody=sample_custody_records,
            output_formats=["markdown"],
        )
        content = outputs["markdown"].read_text(encoding="utf-8")
        assert "v3.0" in content

    def test_json_report_includes_compliance_and_pipeline_metadata(
        self, output_dir, sample_filing_report, sample_custody_records
    ):
        """JSON report metadata must include compliance_standards and pipeline_stage_audits."""
        generator = DOJReportGenerator(output_dir=str(output_dir))
        outputs = generator.generate_comprehensive_report(
            case_id="JLAW-TEST",
            company_name="NIKE, Inc.",
            cik="320187",
            filing_reports=[sample_filing_report],
            chain_of_custody=sample_custody_records,
            output_formats=["json"],
        )
        data = json.loads(outputs["json"].read_text())
        assert "compliance_standards" in data["metadata"]
        assert "pipeline_stage_audits" in data["metadata"]
        assert len(data["metadata"]["compliance_standards"]) >= 4
        assert len(data["metadata"]["pipeline_stage_audits"]) == 9

    def test_manifest_includes_compliance_and_pipeline(
        self, output_dir, sample_filing_report, sample_custody_records
    ):
        """Output manifest must include compliance_standards and pipeline_stage_audits."""
        generator = DOJReportGenerator(output_dir=str(output_dir))
        outputs = generator.generate_comprehensive_report(
            case_id="JLAW-TEST",
            company_name="NIKE, Inc.",
            cik="320187",
            filing_reports=[sample_filing_report],
            chain_of_custody=sample_custody_records,
            output_formats=["json"],
        )
        manifest_data = json.loads(outputs["manifest"].read_text())
        assert "compliance_standards" in manifest_data
        assert "pipeline_stage_audits" in manifest_data
        assert len(manifest_data["compliance_standards"]) >= 4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
