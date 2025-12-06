"""
Forensic Context Dataclass
===========================

Central dataclass that accumulates intelligence across all 13 phases of the
unified forensic pipeline. Each phase enriches this context with additional
findings that inform subsequent phases.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime


@dataclass
class SECFiling:
    """Represents a single SEC filing with metadata."""
    accession_number: str
    filing_type: str
    filing_date: str
    cik: str
    company_name: Optional[str] = None
    document_url: str = ""
    raw_content: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedDocument:
    """Parsed document from DocsGPT with extracted structure."""
    doc_id: str
    content: str
    sections: Dict[str, str] = field(default_factory=dict)
    tables: List[Dict[str, Any]] = field(default_factory=list)
    xbrl_facts: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentChunk:
    """Semantic chunk of a document for vector search."""
    chunk_id: str
    text: str
    doc_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None


@dataclass
class BenfordAnalysis:
    """Benford's Law analysis results."""
    chi_squared: float
    p_value: float
    is_anomalous: bool
    analyzed_fields: List[str] = field(default_factory=list)
    digit_distribution: Dict[str, float] = field(default_factory=dict)


@dataclass
class RevenueAnalysisResult:
    """Revenue recognition analysis findings."""
    dso_trend: List[float] = field(default_factory=list)
    hockey_stick_detected: bool = False
    cash_divergence_score: float = 0.0
    anomalies: List[str] = field(default_factory=list)
    risk_level: str = "LOW"


@dataclass
class FlowAnalysisResult:
    """Financial flow analysis results."""
    circular_flows: List[Dict[str, Any]] = field(default_factory=list)
    enrichment_schemes: List[Dict[str, Any]] = field(default_factory=list)
    coordinated_activity: List[Dict[str, Any]] = field(default_factory=list)
    risk_score: float = 0.0


@dataclass
class TimelineAnomaly:
    """Temporal timeline anomaly."""
    anomaly_type: str
    description: str
    severity: str
    date: Optional[str] = None
    related_filings: List[str] = field(default_factory=list)


@dataclass
class Contradiction:
    """Cross-document contradiction detected."""
    contradiction_type: str
    description: str
    source_document: str
    target_document: str
    source_quote: str
    target_quote: str
    severity: str


@dataclass
class Violation:
    """Legal violation identified."""
    violation_id: str
    violation_type: str
    statute: str
    severity: str
    description: str
    evidence: str
    document_url: str
    exact_quote: str
    prosecutorial_merit: str
    estimated_damages: float = 0.0
    criminal_referral: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StatuteMapping:
    """Legal statute mapping with GovInfo reference."""
    statute: str
    name: str
    jurisdiction: str
    penalties: str
    govinfo_url: str
    applicable_violations: List[str] = field(default_factory=list)


@dataclass
class CriminalReferral:
    """Criminal referral recommendation."""
    violation_id: str
    statute: str
    description: str
    evidence_hash: str
    recommended_action: str


@dataclass
class ForensicContext:
    """
    Central context object that accumulates all forensic intelligence
    across the 13-phase pipeline.
    """
    # Metadata
    company_name: str
    cik: str
    analysis_period_start: str
    analysis_period_end: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Phase 1-2: Document Layer
    filings: List[SECFiling] = field(default_factory=list)
    parsed_documents: List[ParsedDocument] = field(default_factory=list)
    chunks: List[DocumentChunk] = field(default_factory=list)
    
    # Phase 3: Agent Analysis
    agent_findings: Dict[str, Any] = field(default_factory=dict)
    
    # Phase 4: Quantitative Layer
    benford_results: Dict[str, BenfordAnalysis] = field(default_factory=dict)
    beneish_score: float = 0.0
    altman_z_score: float = 0.0
    fraud_probability: float = 0.0
    
    # Phase 5-6: Financial Flow Layer
    revenue_analysis: Optional[RevenueAnalysisResult] = None
    flow_analysis: Optional[FlowAnalysisResult] = None
    
    # Phase 7-8: Linguistic/Temporal Layer
    deception_metrics: Dict[str, float] = field(default_factory=dict)
    timeline_anomalies: List[TimelineAnomaly] = field(default_factory=list)
    
    # Phase 9-10: Detection Layer
    contradictions: List[Contradiction] = field(default_factory=list)
    ml_fraud_scores: Dict[str, float] = field(default_factory=dict)
    
    # Phase 11-12: Legal Layer
    violations: List[Violation] = field(default_factory=list)
    statute_mappings: List[StatuteMapping] = field(default_factory=list)
    criminal_referrals: List[CriminalReferral] = field(default_factory=list)
    
    # Chain of custody
    evidence_hashes: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for serialization."""
        return {
            'company_name': self.company_name,
            'cik': self.cik,
            'analysis_period': {
                'start': self.analysis_period_start,
                'end': self.analysis_period_end
            },
            'timestamp': self.timestamp.isoformat(),
            'filings_count': len(self.filings),
            'violations_count': len(self.violations),
            'criminal_referrals_count': len(self.criminal_referrals),
            'total_damages': sum(v.estimated_damages for v in self.violations)
        }
