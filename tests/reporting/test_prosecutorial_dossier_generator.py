"""
Test Suite for Prosecutorial Dossier Generator - Phase 4
=========================================================

Tests the generation of DOJ-grade prosecutorial dossiers with 7 RIM-mandated sections.
"""

import pytest
import json
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Any
import tempfile

from src.reporting.prosecutorial_dossier_generator import (
    ProsecutorialDossierGenerator,
    ProsecutorialDossier,
)
from src.detection.actor_extraction_engine import ActorProfile
from src.legal.statutory_binding_engine import (
    StatutoryBinding,
    Statute,
    EnforcementAgency,
    CaseType,
)
from src.core.recursive_analysis_engine import (
    RecursiveAnalysisResult,
    ViolationDetail,
    TransactionCluster,
    RiskLevel,
)
from src.reporting.interrogation_package import (
    InterrogationPackage,
)
from src.detection.actor_role_classifier import ActorRole
from decimal import Decimal


# ═══════════════════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════════════════


@pytest.fixture
def temp_output_dir():
    """Create temporary output directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_actor_profiles():
    """Create sample actor profiles for testing."""
    return [
        ActorProfile(
            actor_id="actor_001",
            name="John Doe",
            actor_type="INDIVIDUAL",
            roles=["CEO", "Director"],
            cik="1234567",
            first_appearance=date(2019, 1, 1),
            last_appearance=date(2019, 12, 31),
            evidence_items=["evidence_001", "evidence_002"],
            violations=["violation_001", "violation_002"],
            risk_score=85.0,
        ),
        ActorProfile(
            actor_id="actor_002",
            name="Jane Smith",
            actor_type="INDIVIDUAL",
            roles=["CFO"],
            cik="1234568",
            first_appearance=date(2019, 3, 1),
            last_appearance=date(2019, 11, 30),
            evidence_items=["evidence_003"],
            violations=["violation_003"],
            risk_score=65.0,
        ),
    ]


@pytest.fixture
def sample_statutory_bindings():
    """Create sample statutory bindings for testing."""
    statute = Statute(
        code="17 CFR § 240.10b-5",
        title="Rule 10b-5 Insider Trading",
        description="Prohibits fraudulent activities in connection with securities trading",
        enforcement_agency=EnforcementAgency.SEC,
        case_type=CaseType.BOTH,
        penalty_range="$5M fine, 20 years imprisonment",
    )
    
    return [
        StatutoryBinding(
            binding_id="binding_001",
            violation_id="violation_001",
            violation_type="INSIDER_TRADING",
            statutes=[statute],
            confidence=0.95,
            enforcement_pathway="SEC_ENFORCEMENT",
            plain_language_explanation="This violation establishes insider trading under Rule 10b-5.",
            recommended_actions=["Refer to SEC Enforcement Division", "Initiate civil proceedings"],
            evidence_requirements=["Trading records", "Material non-public information proof"],
        ),
        StatutoryBinding(
            binding_id="binding_002",
            violation_id="violation_002",
            violation_type="FORM_4_LATE_FILING",
            statutes=[statute],
            confidence=0.85,
            enforcement_pathway="SEC_COMPLIANCE",
            plain_language_explanation="This violation establishes late Form 4 filing.",
            recommended_actions=["Issue compliance notice"],
            evidence_requirements=["Filing dates", "Transaction dates"],
        ),
    ]


@pytest.fixture
def sample_recursive_analysis():
    """Create sample recursive analysis result."""
    primary_violation = ViolationDetail(
        violation_id="violation_001",
        violation_type="INSIDER_TRADING",
        description="Insider sold shares before earnings announcement",
        actor_name="John Doe",
        actor_cik="1234567",
        transaction_date=date(2019, 6, 15),
        confidence=0.95,
        evidence={"shares": 10000, "value": 500000},
        severity="CRITICAL",
    )
    
    cluster = TransactionCluster(
        cluster_id="cluster_001",
        actor_name="John Doe",
        actor_cik="1234567",
        transactions=[{"date": "2019-06-15", "shares": 10000, "value": 500000}],
        aggregate_value=Decimal("500000"),
        aggregate_shares=10000,
        date_range=(date(2019, 6, 15), date(2019, 6, 15)),
        suspicious_patterns=["Large transaction before earnings"],
        risk_level=RiskLevel.CRITICAL,
    )
    
    return RecursiveAnalysisResult(
        case_id="CASE_001",
        primary_violations=[primary_violation],
        transaction_clusters=[cluster],
        temporal_correlations=[],
        actor_coordination_patterns=[],
        analysis_period=(date(2019, 1, 1), date(2019, 12, 31)),
        execution_time=120.5,
    )


@pytest.fixture
def sample_interrogation_packages():
    """Create sample interrogation packages."""
    package = InterrogationPackage(
        actor_id="actor_001",
        actor_name="John Doe",
        actor_role=ActorRole.C_SUITE,
        risk_score=85.0,
        generation_date=datetime.utcnow(),
        corporate_positions=[{"title": "CEO", "start_date": "2015-01-01"}],
        violations=[{"violation_id": "violation_001", "type": "INSIDER_TRADING"}],
        evidence_exhibits=[{"exhibit_id": "EX-001", "type": "Form 4"}],
        interview_objectives=["Establish knowledge of material information"],
        applicable_statutes=[{"code": "17 CFR § 240.10b-5", "title": "Rule 10b-5"}],
    )
    
    return {"actor_001": package}


# ═══════════════════════════════════════════════════════════════════════════
# TESTS
# ═══════════════════════════════════════════════════════════════════════════


class TestProsecutorialDossierGenerator:
    """Test suite for ProsecutorialDossierGenerator."""
    
    def test_initialization(self, temp_output_dir):
        """Test generator initialization."""
        generator = ProsecutorialDossierGenerator(
            output_dir=temp_output_dir,
            bates_prefix="JLAW-TEST",
            dossier_type="DOJ_GRADE",
        )
        
        assert generator.output_dir == temp_output_dir
        assert generator.bates_prefix == "JLAW-TEST"
        assert generator.dossier_type == "DOJ_GRADE"
        assert generator.output_dir.exists()
    
    @pytest.mark.asyncio
    async def test_generate_dossier_basic(
        self,
        temp_output_dir,
        sample_actor_profiles,
        sample_statutory_bindings,
        sample_recursive_analysis,
        sample_interrogation_packages,
    ):
        """Test basic dossier generation."""
        generator = ProsecutorialDossierGenerator(output_dir=temp_output_dir)
        
        dossier = await generator.generate_dossier(
            case_id="CASE_001",
            company_name="Test Company",
            cik="1234567",
            node_results={},
            detection_results={},
            actor_profiles=sample_actor_profiles,
            interrogation_packages=sample_interrogation_packages,
            statutory_bindings=sample_statutory_bindings,
            recursive_analysis=sample_recursive_analysis,
            output_formats=['json'],
        )
        
        assert dossier.case_id == "CASE_001"
        assert dossier.company_name == "Test Company"
        assert dossier.cik == "1234567"
        assert dossier.total_violations == len(sample_statutory_bindings)
        assert dossier.total_actors == len(sample_actor_profiles)
    
    def test_executive_summary_generation(
        self,
        temp_output_dir,
        sample_actor_profiles,
        sample_statutory_bindings,
        sample_recursive_analysis,
    ):
        """Test executive summary generation."""
        generator = ProsecutorialDossierGenerator(output_dir=temp_output_dir)
        
        exec_summary = generator._generate_executive_summary(
            case_id="CASE_001",
            company_name="Test Company",
            cik="1234567",
            node_results={},
            detection_results={},
            actor_profiles=sample_actor_profiles,
            statutory_bindings=sample_statutory_bindings,
            recursive_analysis=sample_recursive_analysis,
        )
        
        assert "threat_level" in exec_summary
        assert "threat_statement" in exec_summary
        assert "enforcement_recommendation" in exec_summary
        assert exec_summary["total_violations"] == len(sample_statutory_bindings)
        assert exec_summary["total_actors"] == len(sample_actor_profiles)
    
    def test_violations_table_generation(
        self,
        temp_output_dir,
        sample_statutory_bindings,
        sample_recursive_analysis,
    ):
        """Test violations table generation."""
        generator = ProsecutorialDossierGenerator(output_dir=temp_output_dir)
        
        violations_table = generator._generate_violations_table(
            statutory_bindings=sample_statutory_bindings,
            detection_results={},
            recursive_analysis=sample_recursive_analysis,
        )
        
        assert len(violations_table) == len(sample_statutory_bindings)
        assert all("violation_id" in v for v in violations_table)
        assert all("statutes" in v for v in violations_table)
        assert all("confidence" in v for v in violations_table)
    
    def test_actor_mapping_generation(
        self,
        temp_output_dir,
        sample_actor_profiles,
        sample_statutory_bindings,
        sample_interrogation_packages,
    ):
        """Test actor mapping generation."""
        generator = ProsecutorialDossierGenerator(output_dir=temp_output_dir)
        
        actor_mapping = generator._generate_actor_mapping(
            actor_profiles=sample_actor_profiles,
            statutory_bindings=sample_statutory_bindings,
            interrogation_packages=sample_interrogation_packages,
        )
        
        assert "total_actors" in actor_mapping
        assert "actors" in actor_mapping
        assert actor_mapping["total_actors"] == len(sample_actor_profiles)
    
    def test_transaction_clustering_generation(
        self,
        temp_output_dir,
        sample_recursive_analysis,
    ):
        """Test transaction clustering generation."""
        generator = ProsecutorialDossierGenerator(output_dir=temp_output_dir)
        
        clustering = generator._generate_transaction_clustering(
            recursive_analysis=sample_recursive_analysis,
        )
        
        assert "total_clusters" in clustering
        assert "clusters" in clustering
        assert "deduplication_applied" in clustering
        assert clustering["total_clusters"] == len(sample_recursive_analysis.transaction_clusters)
    
    def test_enforcement_pathways_generation(
        self,
        temp_output_dir,
        sample_statutory_bindings,
    ):
        """Test enforcement pathways generation."""
        generator = ProsecutorialDossierGenerator(output_dir=temp_output_dir)
        
        pathways = generator._generate_enforcement_pathways(
            statutory_bindings=sample_statutory_bindings,
        )
        
        assert "primary_pathway" in pathways
        assert "pathway_justification" in pathways
        assert "sec_violations" in pathways
        assert "doj_violations" in pathways
        assert "irs_violations" in pathways
    
    def test_evidence_strength_generation(
        self,
        temp_output_dir,
        sample_statutory_bindings,
        sample_recursive_analysis,
    ):
        """Test evidence strength generation."""
        generator = ProsecutorialDossierGenerator(output_dir=temp_output_dir)
        
        evidence_strength = generator._generate_evidence_strength(
            statutory_bindings=sample_statutory_bindings,
            recursive_analysis=sample_recursive_analysis,
            merkle_root="abc123def456",
        )
        
        assert "overall_assessment" in evidence_strength
        assert "average_confidence" in evidence_strength
        assert "fre_902_compliant" in evidence_strength
        assert "merkle_root" in evidence_strength
        assert "statute_strengths" in evidence_strength
    
    @pytest.mark.asyncio
    async def test_json_export(
        self,
        temp_output_dir,
        sample_actor_profiles,
        sample_statutory_bindings,
        sample_recursive_analysis,
        sample_interrogation_packages,
    ):
        """Test JSON export functionality."""
        generator = ProsecutorialDossierGenerator(output_dir=temp_output_dir)
        
        dossier = await generator.generate_dossier(
            case_id="CASE_001",
            company_name="Test Company",
            cik="1234567",
            node_results={},
            detection_results={},
            actor_profiles=sample_actor_profiles,
            interrogation_packages=sample_interrogation_packages,
            statutory_bindings=sample_statutory_bindings,
            recursive_analysis=sample_recursive_analysis,
            output_formats=['json'],
        )
        
        # Check JSON file exists
        json_file = temp_output_dir / "dossier_CASE_001.json"
        assert json_file.exists()
        
        # Verify JSON content
        with open(json_file, 'r') as f:
            json_data = json.load(f)
        
        assert json_data["case_id"] == "CASE_001"
        assert "executive_summary" in json_data
        assert "violations_table" in json_data
    
    @pytest.mark.asyncio
    async def test_markdown_export(
        self,
        temp_output_dir,
        sample_actor_profiles,
        sample_statutory_bindings,
        sample_recursive_analysis,
        sample_interrogation_packages,
    ):
        """Test Markdown export functionality."""
        generator = ProsecutorialDossierGenerator(output_dir=temp_output_dir)
        
        dossier = await generator.generate_dossier(
            case_id="CASE_001",
            company_name="Test Company",
            cik="1234567",
            node_results={},
            detection_results={},
            actor_profiles=sample_actor_profiles,
            interrogation_packages=sample_interrogation_packages,
            statutory_bindings=sample_statutory_bindings,
            recursive_analysis=sample_recursive_analysis,
            output_formats=['markdown'],
        )
        
        # Check Markdown file exists
        md_file = temp_output_dir / "dossier_CASE_001.md"
        assert md_file.exists()
        
        # Verify Markdown content
        with open(md_file, 'r') as f:
            md_content = f.read()
        
        assert "PROSECUTORIAL FORENSIC DOSSIER" in md_content
        assert "CASE_001" in md_content
        assert "EXECUTIVE FORENSIC SUMMARY" in md_content
    
    def test_rim_compliance_validation(
        self,
        temp_output_dir,
        sample_actor_profiles,
        sample_statutory_bindings,
        sample_recursive_analysis,
    ):
        """Test RIM compliance validation."""
        generator = ProsecutorialDossierGenerator(output_dir=temp_output_dir)
        
        # Create a mock dossier
        dossier = ProsecutorialDossier(
            dossier_id="test_001",
            case_id="CASE_001",
            company_name="Test Company",
            cik="1234567",
            generation_date=datetime.utcnow(),
            dossier_type="DOJ_GRADE",
            executive_summary={},
            violations_table=[{"statutes": [{"code": "17 CFR § 240.10b-5"}]}],
            actor_mapping={},
            transaction_clustering={},
            interrogation_packages={},
            enforcement_pathways={},
            evidence_strength={
                "overall_assessment": "Test assessment",
                "average_confidence": 0.9,
            },
            total_violations=1,
            total_actors=1,
            total_evidence_items=1,
            rim_compliance_status="PENDING",
            merkle_root="abc123",
        )
        
        compliance = generator._validate_rim_compliance(dossier)
        
        assert "is_compliant" in compliance
        assert "prohibited_terms_found" in compliance
        assert "statutory_coverage" in compliance
        assert "explicit_evidence_strength" in compliance
    
    def test_threat_level_assessment(self, temp_output_dir):
        """Test threat level assessment logic."""
        generator = ProsecutorialDossierGenerator(output_dir=temp_output_dir)
        
        # Test CRITICAL level
        critical_bindings = [
            StatutoryBinding(
                binding_id=f"binding_{i}",
                violation_id=f"violation_{i}",
                violation_type="INSIDER_TRADING",
                statutes=[],
                confidence=0.95,
                enforcement_pathway="DOJ_CRIMINAL",
                plain_language_explanation="Test",
                recommended_actions=[],
                evidence_requirements=[],
            )
            for i in range(5)
        ]
        
        exec_summary = generator._generate_executive_summary(
            case_id="CASE_001",
            company_name="Test",
            cik="123",
            node_results={},
            detection_results={},
            actor_profiles=[],
            statutory_bindings=critical_bindings,
            recursive_analysis=RecursiveAnalysisResult(
                case_id="CASE_001",
                primary_violations=[],
                transaction_clusters=[],
                temporal_correlations=[],
                actor_coordination_patterns=[],
                analysis_period=(date(2019, 1, 1), date(2019, 12, 31)),
                execution_time=0.0,
            ),
        )
        
        assert exec_summary["threat_level"] == "CRITICAL"
    
    def test_no_hedging_language(
        self,
        temp_output_dir,
        sample_statutory_bindings,
        sample_recursive_analysis,
    ):
        """Test that generated content has no hedging language."""
        generator = ProsecutorialDossierGenerator(output_dir=temp_output_dir)
        
        exec_summary = generator._generate_executive_summary(
            case_id="CASE_001",
            company_name="Test",
            cik="123",
            node_results={},
            detection_results={},
            actor_profiles=[],
            statutory_bindings=sample_statutory_bindings,
            recursive_analysis=sample_recursive_analysis,
        )
        
        # Check for prohibited terms
        prohibited_terms = ["may", "might", "could", "possibly", "potentially", "appears"]
        threat_statement = exec_summary["threat_statement"].lower()
        
        for term in prohibited_terms:
            assert term not in threat_statement, f"Hedging term '{term}' found in threat statement"


# ═══════════════════════════════════════════════════════════════════════════
# RUN TESTS
# ═══════════════════════════════════════════════════════════════════════════


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
