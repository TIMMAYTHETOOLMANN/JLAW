"""
DOJ-Level Reporting Data Models
===============================

Standardized data structures for forensic analysis reporting.
These models ensure data flow integrity throughout the pipeline and
enable comprehensive, prosecution-ready output generation.

Key Models:
- ViolationEvidence: Individual violation with full evidence chain
- FilingAnalysisReport: Per-filing detailed analysis report
- DualAgentConsensus: Tracks agreement between analysis agents
- EvidencePackage: Court-ready evidence compilation
- ForensicReportSummary: Executive summary and statistics
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional


class SeverityLevel(str, Enum):
    """Violation severity classification."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ProsecutorialMerit(str, Enum):
    """Prosecutorial merit assessment."""
    STRONG = "STRONG"
    MODERATE = "MODERATE"
    WEAK = "WEAK"


class AgentSource(str, Enum):
    """Source of violation detection."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    BOTH = "both"  # Detected by both agents
    PATTERN = "pattern"  # Detected by pattern detection
    NODE = "node"  # Detected by recursive node analysis


@dataclass
class StatutoryReference:
    """Legal statute or regulation reference."""
    citation: str  # e.g., "15 U.S.C. § 78j(b)", "Exchange Act Rule 10b-5"
    title: str
    summary: str
    full_text: Optional[str] = None
    govinfo_url: Optional[str] = None
    cfr_reference: Optional[str] = None
    penalties: Optional[Dict[str, Any]] = None


@dataclass
class ExactQuote:
    """Exact quote extracted from source document."""
    quote_text: str
    document_url: str
    document_section: str
    page_number: Optional[int] = None
    line_range: Optional[str] = None  # e.g., "lines 45-52"
    html_context: Optional[str] = None
    extraction_timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class DamageEstimate:
    """Estimated financial damages for a violation."""
    civil_minimum: float
    civil_maximum: float
    disgorgement_estimate: float
    criminal_exposure: bool
    prison_years_maximum: int
    calculation_methodology: str
    affected_shareholders: Optional[int] = None
    stock_price_impact: Optional[float] = None


@dataclass
class RedFlag:
    """Identified red flag indicator."""
    flag_type: str
    description: str
    significance: SeverityLevel
    related_violations: List[str] = field(default_factory=list)


@dataclass
class ViolationEvidence:
    """
    Complete evidence package for a single violation.
    
    This is the core data structure for DOJ-level reporting,
    containing all information needed for prosecution.
    """
    violation_id: str
    violation_type: str
    severity: SeverityLevel
    statutory_reference: StatutoryReference
    description: str
    
    # Evidence
    exact_quotes: List[ExactQuote]
    document_url: str
    document_section: str
    filing_accession: str
    filing_date: str
    
    # Assessment
    prosecutorial_merit: ProsecutorialMerit
    damage_estimate: DamageEstimate
    
    # Provenance
    detected_by: AgentSource
    confirmed_by: List[AgentSource] = field(default_factory=list)
    detection_timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Evidence chain
    evidence_hash: str = ""
    chain_of_custody_id: Optional[str] = None
    
    # Additional context
    red_flags: List[RedFlag] = field(default_factory=list)
    related_filings: List[str] = field(default_factory=list)
    additional_context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "violation_id": self.violation_id,
            "violation_type": self.violation_type,
            "severity": self.severity.value,
            "statutory_reference": {
                "citation": self.statutory_reference.citation,
                "title": self.statutory_reference.title,
                "summary": self.statutory_reference.summary,
                "full_text": self.statutory_reference.full_text,
                "govinfo_url": self.statutory_reference.govinfo_url,
                "cfr_reference": self.statutory_reference.cfr_reference,
                "penalties": self.statutory_reference.penalties,
            },
            "description": self.description,
            "exact_quotes": [
                {
                    "quote_text": q.quote_text,
                    "document_url": q.document_url,
                    "document_section": q.document_section,
                    "page_number": q.page_number,
                    "line_range": q.line_range,
                    "html_context": q.html_context,
                    "extraction_timestamp": q.extraction_timestamp.isoformat()
                }
                for q in self.exact_quotes
            ],
            "document_url": self.document_url,
            "document_section": self.document_section,
            "filing_accession": self.filing_accession,
            "filing_date": self.filing_date,
            "prosecutorial_merit": self.prosecutorial_merit.value,
            "damage_estimate": {
                "civil_minimum": self.damage_estimate.civil_minimum,
                "civil_maximum": self.damage_estimate.civil_maximum,
                "disgorgement_estimate": self.damage_estimate.disgorgement_estimate,
                "criminal_exposure": self.damage_estimate.criminal_exposure,
                "prison_years_maximum": self.damage_estimate.prison_years_maximum,
                "calculation_methodology": self.damage_estimate.calculation_methodology,
            },
            "detected_by": self.detected_by.value,
            "confirmed_by": [a.value for a in self.confirmed_by],
            "detection_timestamp": self.detection_timestamp.isoformat(),
            "evidence_hash": self.evidence_hash,
            "chain_of_custody_id": self.chain_of_custody_id,
            "red_flags": [
                {
                    "flag_type": r.flag_type,
                    "description": r.description,
                    "significance": r.significance.value,
                }
                for r in self.red_flags
            ],
            "related_filings": self.related_filings,
        }


@dataclass
class DualAgentConsensus:
    """Tracks dual-agent analysis consensus."""
    openai_findings_count: int
    anthropic_findings_count: int
    overlap_count: int
    openai_unique_count: int
    anthropic_unique_count: int
    confidence_level: float
    disagreements: List[Dict[str, Any]] = field(default_factory=list)
    
    @property
    def agreement_ratio(self) -> float:
        """Calculate agreement ratio between agents."""
        total = self.openai_findings_count + self.anthropic_findings_count
        if total == 0:
            return 1.0
        return (2 * self.overlap_count) / total


@dataclass
class FilingAnalysisReport:
    """
    Detailed analysis report for a single SEC filing.
    
    Contains all violations, evidence, and analysis results
    for one filing document.
    """
    accession_number: str
    filing_type: str
    filing_date: str
    company_name: str
    cik: str
    document_url: str
    
    # Analysis results
    violations: List[ViolationEvidence]
    red_flags: List[RedFlag]
    
    # Agent analysis
    dual_agent_consensus: Optional[DualAgentConsensus] = None
    openai_raw_analysis: Optional[Dict[str, Any]] = None
    anthropic_raw_analysis: Optional[Dict[str, Any]] = None
    
    # Financial metrics
    financial_metrics: Dict[str, Any] = field(default_factory=dict)
    
    # Statistical data
    statistical_data: Dict[str, Any] = field(default_factory=dict)
    
    # Timestamps
    analysis_start: datetime = field(default_factory=datetime.utcnow)
    analysis_end: Optional[datetime] = None
    
    # Evidence chain
    filing_content_hash: str = ""
    
    @property
    def violation_count(self) -> int:
        return len(self.violations)
    
    @property
    def critical_count(self) -> int:
        return len([v for v in self.violations if v.severity == SeverityLevel.CRITICAL])
    
    @property
    def high_count(self) -> int:
        return len([v for v in self.violations if v.severity == SeverityLevel.HIGH])
    
    @property
    def total_estimated_damages(self) -> float:
        return sum(v.damage_estimate.civil_maximum for v in self.violations)
    
    @property
    def requires_criminal_referral(self) -> bool:
        return any(v.damage_estimate.criminal_exposure for v in self.violations)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "accession_number": self.accession_number,
            "filing_type": self.filing_type,
            "filing_date": self.filing_date,
            "company_name": self.company_name,
            "cik": self.cik,
            "document_url": self.document_url,
            "violations": [v.to_dict() for v in self.violations],
            "red_flags": [
                {
                    "flag_type": r.flag_type,
                    "description": r.description,
                    "significance": r.significance.value,
                }
                for r in self.red_flags
            ],
            "dual_agent_consensus": {
                "openai_findings_count": self.dual_agent_consensus.openai_findings_count,
                "anthropic_findings_count": self.dual_agent_consensus.anthropic_findings_count,
                "overlap_count": self.dual_agent_consensus.overlap_count,
                "confidence_level": self.dual_agent_consensus.confidence_level,
                "agreement_ratio": self.dual_agent_consensus.agreement_ratio,
            } if self.dual_agent_consensus else None,
            "financial_metrics": self.financial_metrics,
            "statistical_data": self.statistical_data,
            "analysis_start": self.analysis_start.isoformat(),
            "analysis_end": self.analysis_end.isoformat() if self.analysis_end else None,
            "filing_content_hash": self.filing_content_hash,
            "summary": {
                "violation_count": self.violation_count,
                "critical_count": self.critical_count,
                "high_count": self.high_count,
                "total_estimated_damages": self.total_estimated_damages,
                "requires_criminal_referral": self.requires_criminal_referral,
            }
        }


@dataclass
class SubagentFinding:
    """Finding from a specialized subagent."""
    subagent_name: str
    finding_type: str
    description: str
    confidence: float
    supporting_data: Dict[str, Any] = field(default_factory=dict)
    related_violations: List[str] = field(default_factory=list)


@dataclass
class ChainOfCustodyRecord:
    """Chain of custody documentation for evidence integrity."""
    record_id: str
    evidence_type: str
    evidence_description: str
    collected_at: datetime
    collected_by: str
    storage_location: str
    sha256_hash: str
    sha3_512_hash: Optional[str] = None
    rfc3161_timestamp: Optional[str] = None
    verification_status: str = "verified"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "evidence_type": self.evidence_type,
            "evidence_description": self.evidence_description,
            "collected_at": self.collected_at.isoformat(),
            "collected_by": self.collected_by,
            "storage_location": self.storage_location,
            "sha256_hash": self.sha256_hash,
            "sha3_512_hash": self.sha3_512_hash,
            "rfc3161_timestamp": self.rfc3161_timestamp,
            "verification_status": self.verification_status,
        }


@dataclass
class ForensicReportSummary:
    """
    Executive summary and statistics for the complete forensic report.
    
    Aggregates data from all filing analysis reports.
    """
    case_id: str
    company_name: str
    cik: str
    analysis_period_start: str
    analysis_period_end: str
    
    # Filing statistics
    total_filings_analyzed: int
    filings_by_type: Dict[str, int]
    
    # Violation statistics
    total_violations: int
    violations_by_severity: Dict[str, int]
    violations_by_type: Dict[str, int]
    
    # Financial impact
    total_estimated_damages_min: float
    total_estimated_damages_max: float
    total_disgorgement: float
    
    # Referral recommendations
    sec_referral: bool
    doj_referral: bool
    irs_referral: bool
    criminal_referral_count: int
    
    # Dual-agent summary
    dual_agent_active: bool
    overall_confidence: float
    
    # Subagent summary
    subagent_findings: List[SubagentFinding] = field(default_factory=list)
    
    # Chain of custody
    evidence_items_count: int = 0
    chain_of_custody_verified: bool = True
    
    # Timestamps
    report_generated: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "company_name": self.company_name,
            "cik": self.cik,
            "analysis_period": {
                "start": self.analysis_period_start,
                "end": self.analysis_period_end,
            },
            "filings": {
                "total_analyzed": self.total_filings_analyzed,
                "by_type": self.filings_by_type,
            },
            "violations": {
                "total": self.total_violations,
                "by_severity": self.violations_by_severity,
                "by_type": self.violations_by_type,
            },
            "financial_impact": {
                "estimated_damages_min": self.total_estimated_damages_min,
                "estimated_damages_max": self.total_estimated_damages_max,
                "disgorgement": self.total_disgorgement,
            },
            "referrals": {
                "SEC": self.sec_referral,
                "DOJ": self.doj_referral,
                "IRS": self.irs_referral,
                "criminal_referral_count": self.criminal_referral_count,
            },
            "dual_agent": {
                "active": self.dual_agent_active,
                "overall_confidence": self.overall_confidence,
            },
            "subagent_findings": [
                {
                    "subagent_name": f.subagent_name,
                    "finding_type": f.finding_type,
                    "description": f.description,
                    "confidence": f.confidence,
                }
                for f in self.subagent_findings
            ],
            "evidence_chain": {
                "items_count": self.evidence_items_count,
                "chain_verified": self.chain_of_custody_verified,
            },
            "report_generated": self.report_generated.isoformat(),
        }
