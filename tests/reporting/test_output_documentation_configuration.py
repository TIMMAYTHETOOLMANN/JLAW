"""Tests for forensic output documentation configuration control plane."""

import json
from datetime import datetime
from pathlib import Path

from src.reporting.doj_report_generator import DOJReportGenerator
from src.reporting.models import (
    AgentSource,
    ChainOfCustodyRecord,
    DamageEstimate,
    ExactQuote,
    FilingAnalysisReport,
    ProsecutorialMerit,
    SeverityLevel,
    StatutoryReference,
    ViolationEvidence,
)
from src.reporting.output_documentation_config import get_output_documentation_profile


def _sample_violation() -> ViolationEvidence:
    return ViolationEvidence(
        violation_id="V-001",
        violation_type="LATE_FORM4",
        severity=SeverityLevel.HIGH,
        statutory_reference=StatutoryReference(
            citation="15 U.S.C. § 78p(a)",
            title="Section 16(a)",
            summary="Insider reporting requirements",
        ),
        description="Late filing of Form 4.",
        exact_quotes=[
            ExactQuote(
                quote_text="Transaction Date: 2019-03-15, Filed: 2019-03-22",
                document_url="https://www.sec.gov/example",
                document_section="Transactions",
            )
        ],
        document_url="https://www.sec.gov/example",
        document_section="Transactions",
        filing_accession="0000000000-19-000001",
        filing_date="2019-03-22",
        prosecutorial_merit=ProsecutorialMerit.STRONG,
        damage_estimate=DamageEstimate(
            civil_minimum=10000,
            civil_maximum=50000,
            disgorgement_estimate=0,
            criminal_exposure=False,
            prison_years_maximum=0,
            calculation_methodology="SEC guideline estimate",
        ),
        detected_by=AgentSource.BOTH,
        confirmed_by=[AgentSource.OPENAI, AgentSource.ANTHROPIC],
        evidence_hash="abc123",
    )


def _sample_filing_report() -> FilingAnalysisReport:
    return FilingAnalysisReport(
        accession_number="0000000000-19-000001",
        filing_type="Form 4",
        filing_date="2019-03-22",
        company_name="NIKE, Inc.",
        cik="320187",
        document_url="https://www.sec.gov/example",
        violations=[_sample_violation()],
        red_flags=[],
    )


def test_profile_has_visual_and_quality_requirements():
    profile = get_output_documentation_profile()

    assert profile.profile_id == "JLAW-FORENSIC-OUTPUT-DOCCONFIG"
    assert profile.profile_version == "2.0"
    assert len(profile.required_sections) >= 7
    assert len(profile.visual_requirements) >= 4
    assert profile.quality_thresholds["exact_quotes_per_violation"] >= 1


def test_manifest_and_json_embed_documentation_profile(tmp_path: Path):
    generator = DOJReportGenerator(output_dir=str(tmp_path))
    filing_report = _sample_filing_report()
    custody = [
        ChainOfCustodyRecord(
            record_id="COC-001",
            evidence_type="document",
            evidence_description="Form 4 source",
            collected_at=datetime.utcnow(),
            collected_by="JLAW",
            storage_location="/tmp/evidence",
            sha256_hash="f" * 64,
            verification_status="verified",
        )
    ]

    outputs = generator.generate_comprehensive_report(
        case_id="CASE-TEST-001",
        company_name="NIKE, Inc.",
        cik="320187",
        filing_reports=[filing_report],
        chain_of_custody=custody,
        output_formats=["json", "markdown"],
    )

    assert "manifest" in outputs
    assert outputs["manifest"].exists()

    manifest = json.loads(outputs["manifest"].read_text())
    assert manifest["documentation_profile"]["profile_id"] == "JLAW-FORENSIC-OUTPUT-DOCCONFIG"
    assert manifest["quality_metrics"]["exact_quotes_per_violation"] >= 1

    json_report = json.loads(outputs["json"].read_text())
    profile = json_report["metadata"]["documentation_profile"]
    assert profile["profile_version"] == "2.0"
