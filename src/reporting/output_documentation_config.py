"""
Forensic Output Documentation Configuration
==========================================

Central configuration and quality controls for all JLAW forensic report
outputs (JSON, Markdown, HTML, PDF, and companion manifests).

This module codifies the NIKE 2019 baseline, HOLY_GRAIL pipeline, and
DOJ prosecution-readiness expectations into a unified documentation
profile.  Every generator — ``doj_report_generator``,
``forensic_dossier``, ``visual_report_generator`` — embeds and
enforces this profile so that output quality is deterministic and
auditable.

Profile lineage
---------------
v1.0  Initial format-centric sections (legacy, removed).
v2.0  Added 7 required sections, 4 visual requirements, quality gates.
v3.0  Expanded to 15 required sections covering the full 9-phase
      pipeline, 8 visual requirements aligned to all visualization
      modules, compliance standards (FRE 902, NIST, ISO, RFC 3161),
      output file manifest requirements, and pipeline stage audit
      expectations.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List


# ═══════════════════════════════════════════════════════════════════════════
# DATA CLASSES
# ═══════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class SectionRequirement:
    """Required documentation section and why it exists."""
    name: str
    objective: str
    minimum_fields: List[str]
    section_number: int = 0
    phase_alignment: str = ""


@dataclass(frozen=True)
class VisualRequirement:
    """Expected visual artifact for forensic presentation quality."""
    key: str
    title: str
    rationale: str
    generator_module: str = ""
    output_formats: tuple = ("png",)


@dataclass(frozen=True)
class ComplianceStandard:
    """Legal or technical compliance standard referenced in output."""
    standard_id: str
    title: str
    description: str
    applicable_sections: List[str]


@dataclass(frozen=True)
class OutputFileRequirement:
    """Expected deliverable file in the output bundle."""
    file_key: str
    description: str
    format: str
    required: bool = True


@dataclass(frozen=True)
class PipelineStageAudit:
    """Audit expectation for a single pipeline stage."""
    stage_number: int
    stage_name: str
    gate_description: str
    failure_exit_code: int


@dataclass(frozen=True)
class DocumentationProfile:
    """
    Single canonical profile governing output documentation behaviour,
    quality gates, visual evidence requirements, compliance standards,
    and output file expectations.
    """
    profile_id: str
    reference_document: str
    profile_version: str
    required_sections: List[SectionRequirement]
    visual_requirements: List[VisualRequirement]
    quality_thresholds: Dict[str, Any]
    compliance_standards: List[ComplianceStandard] = field(default_factory=list)
    output_file_requirements: List[OutputFileRequirement] = field(default_factory=list)
    pipeline_stage_audits: List[PipelineStageAudit] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "reference_document": self.reference_document,
            "profile_version": self.profile_version,
            "required_sections": [
                {
                    "section_number": s.section_number,
                    "name": s.name,
                    "objective": s.objective,
                    "minimum_fields": s.minimum_fields,
                    "phase_alignment": s.phase_alignment,
                }
                for s in self.required_sections
            ],
            "visual_requirements": [
                {
                    "key": v.key,
                    "title": v.title,
                    "rationale": v.rationale,
                    "generator_module": v.generator_module,
                    "output_formats": list(v.output_formats),
                }
                for v in self.visual_requirements
            ],
            "quality_thresholds": self.quality_thresholds,
            "compliance_standards": [
                {
                    "standard_id": c.standard_id,
                    "title": c.title,
                    "description": c.description,
                    "applicable_sections": c.applicable_sections,
                }
                for c in self.compliance_standards
            ],
            "output_file_requirements": [
                {
                    "file_key": o.file_key,
                    "description": o.description,
                    "format": o.format,
                    "required": o.required,
                }
                for o in self.output_file_requirements
            ],
            "pipeline_stage_audits": [
                {
                    "stage_number": p.stage_number,
                    "stage_name": p.stage_name,
                    "gate_description": p.gate_description,
                    "failure_exit_code": p.failure_exit_code,
                }
                for p in self.pipeline_stage_audits
            ],
        }


# ═══════════════════════════════════════════════════════════════════════════
# REQUIRED SECTIONS (15) — aligned to the 9-phase Holy Grail pipeline
# ═══════════════════════════════════════════════════════════════════════════

_REQUIRED_SECTIONS: List[SectionRequirement] = [
    # --- I. Orientation & Executive Posture ---
    SectionRequirement(
        section_number=1,
        name="Executive Summary",
        objective="Lead with prosecutorially relevant findings, threat assessment, and regulatory routing.",
        minimum_fields=["threat_level", "violation_totals", "routing", "confidence_score"],
        phase_alignment="Phase 9 — Dossier Generation",
    ),
    SectionRequirement(
        section_number=2,
        name="Target Company Profile",
        objective="Establish investigative context: entity identity, CIK, filing history, and analysis window.",
        minimum_fields=["company_name", "cik", "analysis_period", "filings_by_type", "ticker_symbol"],
        phase_alignment="Phase 1 — Configuration & Target Acquisition",
    ),

    # --- II. Evidence & Filing Analysis ---
    SectionRequirement(
        section_number=3,
        name="Per-Filing Analysis",
        objective="Preserve filing-granular evidence, accession numbers, and exact quotes from source documents.",
        minimum_fields=["accession_number", "filing_type", "filing_date", "violations", "exact_quotes"],
        phase_alignment="Phase 2/3 — Data Collection & Document Parsing",
    ),
    SectionRequirement(
        section_number=4,
        name="Violation Details with Statutory Citations",
        objective="Bind each violation to legal authority, prosecutorial merit, and estimated penalties.",
        minimum_fields=["violation_id", "violation_type", "severity", "citation", "damage_estimate", "prosecutorial_merit"],
        phase_alignment="Phase 4 — 15-Node Recursive Analysis",
    ),

    # --- III. Detection & Validation ---
    SectionRequirement(
        section_number=5,
        name="Detection Pattern Analysis",
        objective="Report results from all 23 detection algorithms with accuracy scores and match counts.",
        minimum_fields=["pattern_name", "accuracy", "matches_found", "category"],
        phase_alignment="Phase 5 — Advanced Detection Patterns (23 algorithms)",
    ),
    SectionRequirement(
        section_number=6,
        name="Dual-Agent Consensus",
        objective="Document AI corroboration, disagreement controls, and cross-validation confidence.",
        minimum_fields=["overlap", "confidence", "disagreements", "agreement_ratio"],
        phase_alignment="Phase 6 — Dual-Agent AI Cross-Validation",
    ),
    SectionRequirement(
        section_number=7,
        name="Subagent Specialized Findings",
        objective="Surface deep-dive findings from the 10 Claude specialized forensic subagents.",
        minimum_fields=["subagent_name", "finding_type", "confidence", "description"],
        phase_alignment="Phase 7 — Subagent Orchestration",
    ),

    # --- IV. Contradiction & Financial Analysis ---
    SectionRequirement(
        section_number=8,
        name="Contradiction Analysis",
        objective="Expose discrepancies between public claims, SEC filings, and forensic findings.",
        minimum_fields=["contradiction_type", "public_claim", "sec_finding", "severity"],
        phase_alignment="Phase 4 — Cross-Node Correlation",
    ),
    SectionRequirement(
        section_number=9,
        name="Financial Impact Assessment",
        objective="Quantify civil/criminal exposure, disgorgement, and shareholder damage estimates.",
        minimum_fields=["civil_range", "disgorgement", "criminal_exposure", "prejudgment_interest"],
        phase_alignment="Phase 4 — Nodes 13-14 (Z-Score / F-Score)",
    ),
    SectionRequirement(
        section_number=10,
        name="Penalty Assessment Matrix",
        objective="Provide per-violation and aggregate penalty estimates with statutory authority.",
        minimum_fields=["violation_type", "statute", "civil_min", "civil_max", "criminal_years"],
        phase_alignment="Phase 9 — Dossier Generation",
    ),

    # --- V. Routing & Compliance ---
    SectionRequirement(
        section_number=11,
        name="Regulatory Routing Recommendations",
        objective="Explicitly route to SEC/DOJ/IRS with rationale, thresholds, and priority ordering.",
        minimum_fields=["sec_referral", "doj_referral", "irs_referral", "routing_rationale"],
        phase_alignment="Phase 4 — Node 6 (Enforcement Routing)",
    ),
    SectionRequirement(
        section_number=12,
        name="Evidence Chain & Integrity Verification",
        objective="Maintain FRE 902-ready integrity with triple-hash provenance and Merkle root.",
        minimum_fields=["sha256", "sha3_512", "blake2b", "merkle_root", "collector", "verification_status"],
        phase_alignment="Phase 8 — Evidence Chain Finalization",
    ),

    # --- VI. Audit & Methodology ---
    SectionRequirement(
        section_number=13,
        name="Pipeline Execution Audit",
        objective="Document 9-phase execution with timing, gate results, node success rates, and exit code.",
        minimum_fields=["phase_name", "duration_seconds", "gate_result", "node_success_rate"],
        phase_alignment="Phases 1-9 — Full Pipeline",
    ),
    SectionRequirement(
        section_number=14,
        name="Compliance Standards Declaration",
        objective="Declare adherence to FRE 902(13)/(14), NIST SP 800-86, ISO 27037, and RFC 3161.",
        minimum_fields=["standard_id", "title", "compliance_status"],
        phase_alignment="Phase 8 — Evidence Chain Finalization",
    ),
    SectionRequirement(
        section_number=15,
        name="Appendices & Exhibits",
        objective="Collect standalone charts, source document inventories, and methodology references.",
        minimum_fields=["exhibit_id", "exhibit_title", "file_reference"],
        phase_alignment="Phase 9 — Dossier Generation",
    ),
]


# ═══════════════════════════════════════════════════════════════════════════
# VISUAL REQUIREMENTS (8) — mapped to src/reporting/visualizations/
# ═══════════════════════════════════════════════════════════════════════════

_VISUAL_REQUIREMENTS: List[VisualRequirement] = [
    VisualRequirement(
        key="severity_distribution",
        title="Severity distribution chart",
        rationale="Instantly communicates case posture and enforcement urgency.",
        generator_module="visualizations (embedded matplotlib)",
        output_formats=("png", "svg"),
    ),
    VisualRequirement(
        key="transaction_timeline",
        title="Transaction timeline",
        rationale="Shows sequence linkage between transactions, filings, and material events.",
        generator_module="visualizations.timeline_generator",
        output_formats=("png", "html"),
    ),
    VisualRequirement(
        key="beneficiary_profits",
        title="Beneficiary profit waterfall",
        rationale="Surfaces concentration of gains and likely beneficiaries for disgorgement.",
        generator_module="visualizations.beneficiary_profit_chart",
        output_formats=("png", "html"),
    ),
    VisualRequirement(
        key="actor_network",
        title="Actor relationship network",
        rationale="Visual evidence of actor coordination, board interlocks, and control paths.",
        generator_module="visualizations.network_graph",
        output_formats=("png", "html"),
    ),
    VisualRequirement(
        key="filing_compliance_heatmap",
        title="Filing compliance heatmap",
        rationale="Highlights temporal filing patterns and deadline adherence across filing types.",
        generator_module="visualizations.heat_map",
        output_formats=("png", "html"),
    ),
    VisualRequirement(
        key="bubble_chart_analysis",
        title="Comparative bubble chart",
        rationale="Multi-dimensional comparison of violation severity, frequency, and financial impact.",
        generator_module="visualizations.bubble_chart",
        output_formats=("png", "html"),
    ),
    VisualRequirement(
        key="filing_deadline_compliance",
        title="Filing deadline compliance chart",
        rationale="Visualizes SEC filing deadline compliance and late-filing patterns.",
        generator_module="visualizations.filing_deadline_chart",
        output_formats=("png", "html"),
    ),
    VisualRequirement(
        key="merkle_tree_evidence",
        title="Merkle tree evidence visualization",
        rationale="Renders the RFC 6962 evidence integrity tree for court presentation.",
        generator_module="visualizations.merkle_tree_viz",
        output_formats=("png", "svg"),
    ),
]


# ═══════════════════════════════════════════════════════════════════════════
# COMPLIANCE STANDARDS — legal/technical frameworks referenced in output
# ═══════════════════════════════════════════════════════════════════════════

_COMPLIANCE_STANDARDS: List[ComplianceStandard] = [
    ComplianceStandard(
        standard_id="FRE_902_13",
        title="Federal Rules of Evidence 902(13)",
        description="Self-authentication of records generated by an electronic process or system.",
        applicable_sections=["Evidence Chain & Integrity Verification", "Appendices & Exhibits"],
    ),
    ComplianceStandard(
        standard_id="FRE_902_14",
        title="Federal Rules of Evidence 902(14)",
        description="Self-authentication via certified copies of electronically stored information with hash verification.",
        applicable_sections=["Evidence Chain & Integrity Verification"],
    ),
    ComplianceStandard(
        standard_id="NIST_SP_800_86",
        title="NIST SP 800-86 — Guide to Integrating Forensic Techniques",
        description="NIST framework for collection, examination, analysis, and reporting of digital evidence.",
        applicable_sections=["Pipeline Execution Audit", "Evidence Chain & Integrity Verification"],
    ),
    ComplianceStandard(
        standard_id="ISO_27037",
        title="ISO/IEC 27037 — Digital Evidence Collection and Preservation",
        description="International standard for identification, collection, acquisition, and preservation of digital evidence.",
        applicable_sections=["Evidence Chain & Integrity Verification", "Per-Filing Analysis"],
    ),
    ComplianceStandard(
        standard_id="RFC_3161",
        title="RFC 3161 — Internet X.509 PKI Time-Stamp Protocol",
        description="Trusted timestamping protocol for cryptographic proof of evidence existence at a point in time.",
        applicable_sections=["Evidence Chain & Integrity Verification"],
    ),
    ComplianceStandard(
        standard_id="RFC_6962",
        title="RFC 6962 — Certificate Transparency (Merkle Tree)",
        description="Merkle tree construction standard used for hierarchical evidence integrity verification.",
        applicable_sections=["Evidence Chain & Integrity Verification", "Appendices & Exhibits"],
    ),
]


# ═══════════════════════════════════════════════════════════════════════════
# OUTPUT FILE REQUIREMENTS — expected deliverables per analysis run
# ═══════════════════════════════════════════════════════════════════════════

_OUTPUT_FILE_REQUIREMENTS: List[OutputFileRequirement] = [
    OutputFileRequirement("markdown_report", "Human-readable forensic dossier", "md", required=True),
    OutputFileRequirement("json_report", "Machine-readable structured dossier", "json", required=True),
    OutputFileRequirement("pdf_dossier", "Court-ready forensic PDF with embedded charts", "pdf", required=True),
    OutputFileRequirement("output_manifest", "Documentation governance manifest", "manifest.json", required=True),
    OutputFileRequirement("analysis_results", "Raw analysis results bundle", "json", required=True),
    OutputFileRequirement("chart_severity", "Severity distribution chart", "png", required=False),
    OutputFileRequirement("chart_timeline", "Transaction timeline chart", "png", required=False),
    OutputFileRequirement("chart_network", "Actor relationship network", "png", required=False),
    OutputFileRequirement("chart_beneficiary", "Beneficiary profit waterfall", "png", required=False),
]


# ═══════════════════════════════════════════════════════════════════════════
# PIPELINE STAGE AUDITS — gate expectations per phase
# ═══════════════════════════════════════════════════════════════════════════

_PIPELINE_STAGE_AUDITS: List[PipelineStageAudit] = [
    PipelineStageAudit(1, "Configuration & Target Acquisition", "SEC API config valid, 6+ modules loaded", 1),
    PipelineStageAudit(2, "SEC EDGAR Data Collection", "Minimum 5 filings collected", 2),
    PipelineStageAudit(3, "Document Parsing & Indexing", "80% documents parsed successfully", 3),
    PipelineStageAudit(4, "15-Node Recursive Analysis", "12/15 nodes successful (80%)", 4),
    PipelineStageAudit(5, "Advanced Detection Patterns", "20/23 patterns executed (87%)", 5),
    PipelineStageAudit(6, "Dual-Agent AI Cross-Validation", "At least 1 AI agent responsive", 0),
    PipelineStageAudit(7, "Subagent Orchestration", "Subagent results collected", 0),
    PipelineStageAudit(8, "Evidence Chain Finalization", "100% hash match, Merkle root computed", 6),
    PipelineStageAudit(9, "DOJ-Grade Dossier Generation", "Report generated successfully", 7),
]


# ═══════════════════════════════════════════════════════════════════════════
# QUALITY THRESHOLDS — expanded gate criteria
# ═══════════════════════════════════════════════════════════════════════════

_QUALITY_THRESHOLDS: Dict[str, Any] = {
    # Per-violation requirements
    "exact_quotes_per_violation": 1,
    "statutory_citations_per_violation": 1,
    # Evidence chain
    "chain_of_custody_records_required": True,
    "evidence_hash_algorithms_required": 3,       # SHA-256 + SHA3-512 + BLAKE2b
    # AI validation
    "dual_agent_validation_required": True,
    "minimum_overall_confidence": 0.70,
    # Pipeline completeness
    "minimum_pipeline_phases_completed": 7,
    "minimum_node_success_rate": 0.80,
    "minimum_detection_patterns_executed": 20,
    # Filing coverage
    "minimum_filings_analyzed": 5,
    # Compliance
    "compliance_standards_referenced": 4,          # FRE 902, NIST, ISO, RFC 3161 minimum
    # Output completeness
    "required_output_files": 5,                    # md, json, pdf, manifest, analysis_results
}


# ═══════════════════════════════════════════════════════════════════════════
# CANONICAL PROFILE — v3.0
# ═══════════════════════════════════════════════════════════════════════════

FORENSIC_OUTPUT_DOCUMENTATION_PROFILE = DocumentationProfile(
    profile_id="JLAW-FORENSIC-OUTPUT-DOCCONFIG",
    reference_document="NIKE 2019 baseline dossier + HOLY_GRAIL_PIPELINE.md",
    profile_version="3.0",
    required_sections=_REQUIRED_SECTIONS,
    visual_requirements=_VISUAL_REQUIREMENTS,
    quality_thresholds=_QUALITY_THRESHOLDS,
    compliance_standards=_COMPLIANCE_STANDARDS,
    output_file_requirements=_OUTPUT_FILE_REQUIREMENTS,
    pipeline_stage_audits=_PIPELINE_STAGE_AUDITS,
)


def get_output_documentation_profile() -> DocumentationProfile:
    """Return the active output documentation profile."""
    return FORENSIC_OUTPUT_DOCUMENTATION_PROFILE
