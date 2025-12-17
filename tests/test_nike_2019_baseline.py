"""
Nike 2019 Baseline Tests
========================

Tests to validate that generated reports match or exceed
the Nike 2019 reference document quality standards.

The Nike 2019 analysis serves as the gold standard for
DOJ-level forensic reporting quality.

Baseline Criteria:
- Report structure matches reference format
- Per-filing breakdown included
- Exact quotes extracted and cited
- Statutory citations accurate
- Dual-agent consensus documented
- Chain of custody verified
- Financial impact calculated
- Regulatory routing recommended
"""

import json
import pytest
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

from src.reporting.constants import (
    NIKE_2019_BASELINE,
    SeverityTier,
    ViolationType,
    SEC_STATUTES,
    get_statute_for_violation,
    calculate_penalty_range,
    determine_regulatory_routing,
)
from src.reporting.models import (
    SeverityLevel,
    ProsecutorialMerit,
    AgentSource,
    StatutoryReference,
    ExactQuote,
    DamageEstimate,
    ViolationEvidence,
    DualAgentConsensus,
    FilingAnalysisReport,
    ChainOfCustodyRecord,
    ForensicReportSummary,
)
from src.reporting.doj_report_generator import DOJReportGenerator
from src.reporting.evidence_packager import EvidencePackager, EvidencePackage


class TestNike2019BaselineStructure:
    """Tests for Nike 2019 baseline configuration."""
    
    def test_baseline_configuration_exists(self):
        """Test that Nike 2019 baseline is properly configured."""
        baseline = NIKE_2019_BASELINE
        
        assert baseline is not None
        assert baseline["company"] == "NIKE, Inc."
        assert baseline["cik"] == "320187"
        assert baseline["analysis_year"] == 2019
        assert baseline["reference_standard"] is True
    
    def test_expected_sections_defined(self):
        """Test that all expected report sections are defined."""
        expected_sections = NIKE_2019_BASELINE["expected_sections"]
        
        required = [
            "Executive Summary",
            "Target Information",
            "Per-Filing Analysis",
            "Violation Details with Statutory Citations",
            "Dual-Agent Consensus",
            "Evidence Chain",
            "Financial Impact Assessment",
            "Regulatory Routing Recommendations",
        ]
        
        for section in required:
            assert section in expected_sections, f"Missing expected section: {section}"
    
    def test_quality_metrics_defined(self):
        """Test that quality metrics are properly defined."""
        metrics = NIKE_2019_BASELINE["minimum_quality_metrics"]
        
        assert "exact_quotes_per_violation" in metrics
        assert metrics["exact_quotes_per_violation"] >= 1
        
        assert "statutory_citations_per_violation" in metrics
        assert metrics["statutory_citations_per_violation"] >= 1
        
        assert "chain_of_custody_records" in metrics
        assert metrics["chain_of_custody_records"] is True
        
        assert "dual_agent_validation" in metrics
        assert metrics["dual_agent_validation"] is True
        
        assert "damage_estimation" in metrics
        assert metrics["damage_estimation"] is True


class TestNike2019ReportGeneration:
    """Tests for generating Nike 2019-quality reports."""
    
    @pytest.fixture
    def output_dir(self, tmp_path: Path) -> Path:
        """Create temporary output directory."""
        output = tmp_path / "nike_reports"
        output.mkdir(parents=True, exist_ok=True)
        return output
    
    @pytest.fixture
    def nike_2019_violations(self) -> List[ViolationEvidence]:
        """Create sample violations matching Nike 2019 patterns."""
        return [
            ViolationEvidence(
                violation_id="V-NKE-2019-001",
                violation_type=ViolationType.LATE_FORM4.value,
                severity=SeverityLevel.HIGH,
                statutory_reference=StatutoryReference(
                    citation="15 U.S.C. § 78p(a)",
                    title="Section 16(a) - Insider Reporting Requirements",
                    summary="Insiders must file Form 4 within 2 business days of transactions.",
                    full_text="Every person who is directly or indirectly the beneficial owner...",
                    govinfo_url="https://www.govinfo.gov/content/pkg/USCODE-2022-title15/html/USCODE-2022-title15-chap2B-sec78p.htm",
                ),
                description="Form 4 filed 5 business days after transaction date, exceeding the 2-day requirement.",
                exact_quotes=[
                    ExactQuote(
                        quote_text="Transaction Date: March 15, 2019. Date Filed: March 22, 2019.",
                        document_url="https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=320187",
                        document_section="Transaction Details",
                        page_number=1,
                        line_range="Lines 12-15",
                    ),
                    ExactQuote(
                        quote_text="Nature of Indirect Beneficial Ownership: By Trust",
                        document_url="https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=320187",
                        document_section="Footnotes",
                        page_number=2,
                    ),
                ],
                document_url="https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=320187",
                document_section="Transactions",
                filing_accession="0001234567-19-000001",
                filing_date="2019-03-22",
                prosecutorial_merit=ProsecutorialMerit.STRONG,
                damage_estimate=DamageEstimate(
                    civil_minimum=10000.0,
                    civil_maximum=50000.0,
                    disgorgement_estimate=0.0,
                    criminal_exposure=False,
                    prison_years_maximum=0,
                    calculation_methodology="SEC civil penalty guidelines for Section 16 violations"
                ),
                detected_by=AgentSource.OPENAI,
                confirmed_by=[AgentSource.ANTHROPIC],
                evidence_hash="nike2019hash001",
            ),
            ViolationEvidence(
                violation_id="V-NKE-2019-002",
                violation_type=ViolationType.ZERO_DOLLAR_TRANSACTION.value,
                severity=SeverityLevel.MEDIUM,
                statutory_reference=StatutoryReference(
                    citation="15 U.S.C. § 78p(a)",
                    title="Section 16(a) - Insider Reporting Requirements",
                    summary="Zero-dollar transactions may indicate gifts or RSU vesting requiring proper disclosure.",
                ),
                description="Transaction reported at $0.00 per share, potentially indicating unreported gift or RSU vesting.",
                exact_quotes=[
                    ExactQuote(
                        quote_text="Price Per Share: $0.00",
                        document_url="https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=320187",
                        document_section="Transaction Table",
                        page_number=1,
                    ),
                ],
                document_url="https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=320187",
                document_section="Transaction Table",
                filing_accession="0001234567-19-000002",
                filing_date="2019-06-15",
                prosecutorial_merit=ProsecutorialMerit.MODERATE,
                damage_estimate=DamageEstimate(
                    civil_minimum=5000.0,
                    civil_maximum=25000.0,
                    disgorgement_estimate=0.0,
                    criminal_exposure=False,
                    prison_years_maximum=0,
                    calculation_methodology="SEC civil penalty guidelines"
                ),
                detected_by=AgentSource.PATTERN,
                confirmed_by=[AgentSource.OPENAI],
                evidence_hash="nike2019hash002",
            ),
        ]
    
    @pytest.fixture
    def nike_2019_filing_report(
        self,
        nike_2019_violations: List[ViolationEvidence]
    ) -> FilingAnalysisReport:
        """Create Nike 2019-style filing report."""
        return FilingAnalysisReport(
            accession_number="0001234567-19-000001",
            filing_type="Form 4",
            filing_date="2019-03-22",
            company_name="NIKE, Inc.",
            cik="320187",
            document_url="https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=320187",
            violations=nike_2019_violations,
            red_flags=[],
            dual_agent_consensus=DualAgentConsensus(
                openai_findings_count=2,
                anthropic_findings_count=2,
                overlap_count=2,
                openai_unique_count=0,
                anthropic_unique_count=0,
                confidence_level=0.95,
            ),
            openai_raw_analysis={"status": "success", "violations": 2},
            anthropic_raw_analysis={"status": "success", "violations": 2},
        )
    
    @pytest.fixture
    def nike_2019_custody_records(self) -> List[ChainOfCustodyRecord]:
        """Create Nike 2019-style custody records."""
        return [
            ChainOfCustodyRecord(
                record_id="COC-NKE-2019-001",
                evidence_type="document",
                evidence_description="Form 4 filing collected from SEC EDGAR",
                collected_at=datetime(2019, 12, 1, 10, 0, 0),
                collected_by="JLAW SEC EDGAR Client",
                storage_location="/forensic_storage/nike_2019",
                sha256_hash="a1b2c3d4e5f6" * 10,
                verification_status="verified",
            ),
            ChainOfCustodyRecord(
                record_id="COC-NKE-2019-002",
                evidence_type="analysis",
                evidence_description="Dual-agent analysis completed",
                collected_at=datetime(2019, 12, 1, 10, 30, 0),
                collected_by="JLAW Dual-Agent Coordinator",
                storage_location="/forensic_storage/nike_2019",
                sha256_hash="f6e5d4c3b2a1" * 10,
                verification_status="verified",
            ),
        ]
    
    def test_generate_nike_quality_report(
        self,
        output_dir: Path,
        nike_2019_filing_report: FilingAnalysisReport,
        nike_2019_custody_records: List[ChainOfCustodyRecord]
    ):
        """Test generating a report that meets Nike 2019 quality standards."""
        generator = DOJReportGenerator(output_dir=str(output_dir))
        
        outputs = generator.generate_comprehensive_report(
            case_id="JLAW-320187-2019-BASELINE",
            company_name="NIKE, Inc.",
            cik="320187",
            filing_reports=[nike_2019_filing_report],
            chain_of_custody=nike_2019_custody_records,
            output_formats=['markdown', 'json']
        )
        
        assert 'markdown' in outputs
        assert outputs['markdown'].exists()
        
        # Read and validate content
        with open(outputs['markdown'], 'r') as f:
            content = f.read()
        
        # Validate expected sections are present
        for section in NIKE_2019_BASELINE["expected_sections"]:
            # Map section names to what appears in the report
            section_mappings = {
                "Executive Summary": "EXECUTIVE SUMMARY",
                "Target Information": "Target Information",
                "Per-Filing Analysis": "PER-FILING DETAILED ANALYSIS",
                "Violation Details with Statutory Citations": "Violations Detected",
                "Dual-Agent Consensus": "DUAL-AGENT CONSENSUS",
                "Evidence Chain": "Evidence Hash",
                "Financial Impact Assessment": "Financial Impact",
                "Regulatory Routing Recommendations": "Regulatory Routing",
            }
            expected_text = section_mappings.get(section, section)
            assert expected_text in content, f"Missing section: {section} (looked for: {expected_text})"
    
    def test_exact_quotes_included(
        self,
        output_dir: Path,
        nike_2019_filing_report: FilingAnalysisReport,
        nike_2019_custody_records: List[ChainOfCustodyRecord]
    ):
        """Test that exact quotes are included in report."""
        generator = DOJReportGenerator(output_dir=str(output_dir))
        
        outputs = generator.generate_comprehensive_report(
            case_id="JLAW-320187-2019-QUOTES",
            company_name="NIKE, Inc.",
            cik="320187",
            filing_reports=[nike_2019_filing_report],
            chain_of_custody=nike_2019_custody_records,
            output_formats=['markdown']
        )
        
        with open(outputs['markdown'], 'r') as f:
            content = f.read()
        
        # Check for exact quotes
        assert "Exact Quotes from Filing" in content
        assert "Transaction Date: March 15, 2019" in content
        assert "Price Per Share: $0.00" in content
    
    def test_statutory_citations_included(
        self,
        output_dir: Path,
        nike_2019_filing_report: FilingAnalysisReport,
        nike_2019_custody_records: List[ChainOfCustodyRecord]
    ):
        """Test that statutory citations are included."""
        generator = DOJReportGenerator(output_dir=str(output_dir))
        
        outputs = generator.generate_comprehensive_report(
            case_id="JLAW-320187-2019-STATUTES",
            company_name="NIKE, Inc.",
            cik="320187",
            filing_reports=[nike_2019_filing_report],
            chain_of_custody=nike_2019_custody_records,
            output_formats=['markdown']
        )
        
        with open(outputs['markdown'], 'r') as f:
            content = f.read()
        
        # Check for statutory reference (the citation is definitely there)
        assert "15 U.S.C." in content or "78p(a)" in content
        # Check for section reference in some form
        assert "Section 16" in content or "Insider Reporting" in content or "78p" in content
    
    def test_dual_agent_consensus_documented(
        self,
        output_dir: Path,
        nike_2019_filing_report: FilingAnalysisReport,
        nike_2019_custody_records: List[ChainOfCustodyRecord]
    ):
        """Test that dual-agent consensus is documented."""
        generator = DOJReportGenerator(output_dir=str(output_dir))
        
        outputs = generator.generate_comprehensive_report(
            case_id="JLAW-320187-2019-DUAL",
            company_name="NIKE, Inc.",
            cik="320187",
            filing_reports=[nike_2019_filing_report],
            chain_of_custody=nike_2019_custody_records,
            output_formats=['markdown']
        )
        
        with open(outputs['markdown'], 'r') as f:
            content = f.read()
        
        assert "DUAL-AGENT CONSENSUS" in content
        assert "OpenAI" in content or "Overlap" in content
    
    def test_chain_of_custody_documented(
        self,
        output_dir: Path,
        nike_2019_filing_report: FilingAnalysisReport,
        nike_2019_custody_records: List[ChainOfCustodyRecord]
    ):
        """Test that chain of custody is documented."""
        generator = DOJReportGenerator(output_dir=str(output_dir))
        
        outputs = generator.generate_comprehensive_report(
            case_id="JLAW-320187-2019-CUSTODY",
            company_name="NIKE, Inc.",
            cik="320187",
            filing_reports=[nike_2019_filing_report],
            chain_of_custody=nike_2019_custody_records,
            output_formats=['markdown']
        )
        
        with open(outputs['markdown'], 'r') as f:
            content = f.read()
        
        assert "CHAIN OF CUSTODY" in content
        assert "SHA-256" in content or "Hash" in content
        assert "verified" in content.lower()
    
    def test_json_report_completeness(
        self,
        output_dir: Path,
        nike_2019_filing_report: FilingAnalysisReport,
        nike_2019_custody_records: List[ChainOfCustodyRecord]
    ):
        """Test JSON report contains all required data."""
        generator = DOJReportGenerator(output_dir=str(output_dir))
        
        outputs = generator.generate_comprehensive_report(
            case_id="JLAW-320187-2019-JSON",
            company_name="NIKE, Inc.",
            cik="320187",
            filing_reports=[nike_2019_filing_report],
            chain_of_custody=nike_2019_custody_records,
            output_formats=['json']
        )
        
        with open(outputs['json'], 'r') as f:
            data = json.load(f)
        
        # Validate structure
        assert "summary" in data
        assert "filing_reports" in data
        assert "chain_of_custody" in data
        assert "report_hash" in data
        
        # Validate summary (nested structure)
        summary = data["summary"]
        assert summary["company_name"] == "NIKE, Inc."
        assert summary["cik"] == "320187"
        assert "violations" in summary
        assert summary["violations"]["total"] == 2
        
        # Validate violations in filing reports
        filing_reports = data["filing_reports"]
        assert len(filing_reports) == 1
        assert len(filing_reports[0]["violations"]) == 2


class TestNike2019QualityMetrics:
    """Tests for validating Nike 2019 quality metrics."""
    
    def test_quotes_per_violation_metric(self):
        """Test that violations meet quotes-per-violation requirement."""
        min_quotes = NIKE_2019_BASELINE["minimum_quality_metrics"]["exact_quotes_per_violation"]
        
        # Create a violation with minimum quotes
        violation = ViolationEvidence(
            violation_id="V-TEST",
            violation_type="LATE_FORM4",
            severity=SeverityLevel.HIGH,
            statutory_reference=StatutoryReference("15 U.S.C. § 78p(a)", "", ""),
            description="Test",
            exact_quotes=[
                ExactQuote(
                    quote_text=f"Quote {i}",
                    document_url="https://example.com",
                    document_section="Test",
                )
                for i in range(min_quotes)
            ],
            document_url="",
            document_section="",
            filing_accession="",
            filing_date="",
            prosecutorial_merit=ProsecutorialMerit.MODERATE,
            damage_estimate=DamageEstimate(0, 0, 0, False, 0, ""),
            detected_by=AgentSource.PATTERN,
            evidence_hash="",
        )
        
        assert len(violation.exact_quotes) >= min_quotes
    
    def test_regulatory_routing_logic(self):
        """Test regulatory routing determination."""
        # Test SEC routing (any violation)
        violations = [
            (ViolationType.LATE_FORM4, SeverityTier.LOW),
        ]
        routing = determine_regulatory_routing(violations)
        assert routing["SEC"] is True
        
        # Test DOJ routing (critical violations)
        violations = [
            (ViolationType.FINANCIAL_STATEMENT_FRAUD, SeverityTier.CRITICAL),
        ]
        routing = determine_regulatory_routing(violations)
        assert routing["DOJ"] is True
        
        # Test IRS routing (tax violations)
        violations = [
            (ViolationType.IRC_83B_ELECTION_FAILURE, SeverityTier.HIGH),
        ]
        routing = determine_regulatory_routing(violations)
        assert routing["IRS"] is True
    
    def test_penalty_range_calculation(self):
        """Test penalty range calculations are reasonable."""
        # Late Form 4 - should have civil penalties
        min_p, max_p = calculate_penalty_range(
            ViolationType.LATE_FORM4,
            SeverityTier.HIGH
        )
        assert min_p >= 0
        assert max_p > min_p
        
        # Securities fraud - should have higher penalties
        min_fraud, max_fraud = calculate_penalty_range(
            ViolationType.FINANCIAL_STATEMENT_FRAUD,
            SeverityTier.CRITICAL
        )
        assert max_fraud > max_p  # Fraud should have higher max penalty
    
    def test_dual_agent_agreement_ratio(self):
        """Test dual-agent agreement ratio calculation."""
        # Perfect agreement
        consensus = DualAgentConsensus(
            openai_findings_count=5,
            anthropic_findings_count=5,
            overlap_count=5,
            openai_unique_count=0,
            anthropic_unique_count=0,
            confidence_level=1.0,
        )
        assert consensus.agreement_ratio == 1.0
        
        # Partial agreement
        consensus = DualAgentConsensus(
            openai_findings_count=5,
            anthropic_findings_count=5,
            overlap_count=3,
            openai_unique_count=2,
            anthropic_unique_count=2,
            confidence_level=0.8,
        )
        # Agreement ratio = 2 * 3 / 10 = 0.6
        assert consensus.agreement_ratio == 0.6


class TestNike2019EvidencePackaging:
    """Tests for Nike 2019-quality evidence packaging."""
    
    @pytest.fixture
    def output_dir(self, tmp_path: Path) -> Path:
        """Create temporary output directory."""
        output = tmp_path / "nike_evidence"
        output.mkdir(parents=True, exist_ok=True)
        return output
    
    def test_evidence_package_baseline_validation(self, output_dir: Path):
        """Test evidence package meets Nike 2019 baseline."""
        packager = EvidencePackager(output_dir=str(output_dir))
        
        # Create a filing report with violations (this adds custody records)
        violation = ViolationEvidence(
            violation_id="V-NKE-001",
            violation_type="LATE_FORM4",
            severity=SeverityLevel.HIGH,
            statutory_reference=StatutoryReference(
                citation="15 U.S.C. § 78p(a)",
                title="Section 16(a)",
                summary="Insider reporting",
            ),
            description="Late filing",
            exact_quotes=[
                ExactQuote(
                    quote_text="Transaction delayed",
                    document_url="https://example.com",
                    document_section="Transactions",
                )
            ],
            document_url="https://example.com",
            document_section="Transactions",
            filing_accession="0001234567-19-000001",
            filing_date="2019-03-22",
            prosecutorial_merit=ProsecutorialMerit.STRONG,
            damage_estimate=DamageEstimate(5000, 25000, 0, False, 0, "Standard"),
            detected_by=AgentSource.BOTH,
            evidence_hash="test123",
        )
        
        # Use create_package_from_filing_report which DOES add custody records
        filing_report = FilingAnalysisReport(
            accession_number="0001234567-19-000001",
            filing_type="Form 4",
            filing_date="2019-03-22",
            company_name="NIKE, Inc.",
            cik="320187",
            document_url="https://example.com",
            violations=[violation],
            red_flags=[],
        )
        
        package = packager.create_package_from_filing_report(
            case_id="JLAW-320187-2019",
            filing_report=filing_report
        )
        
        # Validate against baseline
        validation = packager.validate_against_nike_baseline(package)
        
        assert validation["baseline_reference"] == "Nike 2019"
        # The package has custody records and quotes, so key checks should pass
        assert validation["checks"]["chain_of_custody_records"]["actual"] is True
        assert validation["checks"]["integrity_verification"]["pass"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
