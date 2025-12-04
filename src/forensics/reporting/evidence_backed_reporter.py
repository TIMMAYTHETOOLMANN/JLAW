"""
Evidence-Backed Forensic Reporter
=================================

Zero-tolerance evidence standards for forensic reporting.
NO findings reported without complete evidence chains.

"Our system does not state a single finding that is not backed directly by 
rigorous evidence chains and exact quotes from said documentation citing 
exactly what was violated, where it was violated, the quote from the document... 
every single detail. Because otherwise it's just accusation."
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ConfidenceLevel(Enum):
    """Evidence confidence levels"""
    DEFINITIVE = 1.0      # 100% - Verified with primary source
    HIGH = 0.85           # 85% - Strong corroborating evidence
    MODERATE = 0.70       # 70% - Sufficient evidence, minor gaps
    LOW = 0.50            # 50% - Circumstantial evidence only
    INSUFFICIENT = 0.0    # 0% - Cannot verify


class EvidenceType(Enum):
    """Types of evidence"""
    TEMPORAL_DATA = "temporal_data"          # Dates, timestamps, deadlines
    NUMERICAL_DATA = "numerical_data"        # Financial figures, calculations
    TEXTUAL_QUOTE = "textual_quote"         # Exact quotes from documents
    REGULATORY_TEXT = "regulatory_text"      # Statute/regulation text
    METADATA = "metadata"                    # Filing metadata, headers
    CALCULATION = "calculation"              # Mathematical derivations
    CROSS_REFERENCE = "cross_reference"      # References between documents


@dataclass
class EvidenceItem:
    """Single piece of evidence with complete provenance"""
    evidence_type: EvidenceType
    source_document: str              # Document ID or filename
    source_location: str              # Page, section, line number, XML path
    content: str                      # Actual evidence (quote, number, date)
    extraction_method: str            # How it was obtained
    verification_status: str          # VERIFIED, UNVERIFIED, DISPUTED
    extracted_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': self.evidence_type.value,
            'source': self.source_document,
            'location': self.source_location,
            'content': self.content,
            'method': self.extraction_method,
            'status': self.verification_status,
            'timestamp': self.extracted_at
        }


@dataclass
class StatuteCitation:
    """Complete statute citation with actual regulatory text"""
    title: str                    # e.g., "15 U.S.C. § 78p(a)(2)(A)"
    full_text: str               # Actual text of the statute
    violation_description: str   # How the statute was violated
    source_url: str             # Link to authoritative source
    penalty_range: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'title': self.title,
            'text': self.full_text,
            'violation': self.violation_description,
            'source': self.source_url,
            'penalties': self.penalty_range
        }


@dataclass
class ViolationEvidence:
    """Complete evidence package for a violation"""
    violation_id: str
    violation_type: str
    severity: str
    
    # REQUIRED: Supporting evidence items
    supporting_evidence: List[EvidenceItem]
    
    # REQUIRED: Statute citations with actual text
    statute_citations: List[StatuteCitation]
    
    # REQUIRED: Reasoning chain (step-by-step logic)
    reasoning_chain: List[str]
    
    # REQUIRED: Confidence assessment
    confidence: ConfidenceLevel
    confidence_justification: str
    
    # Optional but recommended
    damages_calculation: Optional[Dict[str, Any]] = None
    corroborating_sources: List[str] = field(default_factory=list)
    contradicting_evidence: List[str] = field(default_factory=list)
    investigator_notes: str = ""
    
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def is_reportable(self) -> bool:
        """
        Determine if violation has sufficient evidence to be reported
        
        Criteria:
        1. At least MODERATE confidence
        2. Has supporting evidence
        3. Has statute citations
        4. Has reasoning chain (min 2 steps)
        """
        if self.confidence.value < ConfidenceLevel.MODERATE.value:
            logger.warning(f"Violation {self.violation_id}: Confidence too low ({self.confidence.name})")
            return False
        
        if not self.supporting_evidence:
            logger.warning(f"Violation {self.violation_id}: No supporting evidence")
            return False
        
        if not self.statute_citations:
            logger.warning(f"Violation {self.violation_id}: No statute citations")
            return False
        
        if len(self.reasoning_chain) < 2:
            logger.warning(f"Violation {self.violation_id}: Insufficient reasoning chain")
            return False
        
        return True
    
    def get_evidence_strength_score(self) -> float:
        """
        Calculate evidence strength score (0.0 to 1.0)
        
        Formula:
        - Evidence count (30%)
        - Citation count (20%)
        - Reasoning depth (20%)
        - Confidence level (30%)
        """
        # Evidence count score (cap at 5 items)
        evidence_score = min(len(self.supporting_evidence) / 5.0, 1.0) * 0.30
        
        # Citation count score (cap at 3 citations)
        citation_score = min(len(self.statute_citations) / 3.0, 1.0) * 0.20
        
        # Reasoning depth score (cap at 6 steps)
        reasoning_score = min(len(self.reasoning_chain) / 6.0, 1.0) * 0.20
        
        # Confidence score
        confidence_score = self.confidence.value * 0.30
        
        return evidence_score + citation_score + reasoning_score + confidence_score
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'violation_id': self.violation_id,
            'type': self.violation_type,
            'severity': self.severity,
            'evidence': [e.to_dict() for e in self.supporting_evidence],
            'statutes': [s.to_dict() for s in self.statute_citations],
            'reasoning': self.reasoning_chain,
            'confidence': {
                'level': self.confidence.name,
                'score': self.confidence.value,
                'justification': self.confidence_justification
            },
            'evidence_strength': self.get_evidence_strength_score(),
            'reportable': self.is_reportable(),
            'damages': self.damages_calculation,
            'corroborating': self.corroborating_sources,
            'contradicting': self.contradicting_evidence,
            'notes': self.investigator_notes,
            'timestamp': self.created_at
        }


class EvidenceBackedReporter:
    """
    Gatekeeper for forensic reporting
    
    REJECTS all violations without sufficient evidence
    """
    
    def __init__(self, min_confidence: ConfidenceLevel = ConfidenceLevel.MODERATE):
        self.min_confidence = min_confidence
        self.violations_evaluated = 0
        self.violations_accepted = 0
        self.violations_rejected = 0
        self.rejection_reasons = {
            'low_confidence': 0,
            'no_evidence': 0,
            'no_statutes': 0,
            'insufficient_reasoning': 0
        }
    
    def evaluate_violation(self, violation: ViolationEvidence) -> bool:
        """
        Evaluate if violation meets evidence standards
        
        Returns:
            True if violation should be reported
            False if violation should be rejected
        """
        self.violations_evaluated += 1
        
        # Check confidence level
        if violation.confidence.value < self.min_confidence.value:
            self.violations_rejected += 1
            self.rejection_reasons['low_confidence'] += 1
            logger.info(f"REJECTED: {violation.violation_id} - Confidence too low")
            return False
        
        # Check evidence
        if not violation.supporting_evidence:
            self.violations_rejected += 1
            self.rejection_reasons['no_evidence'] += 1
            logger.info(f"REJECTED: {violation.violation_id} - No supporting evidence")
            return False
        
        # Check statutes
        if not violation.statute_citations:
            self.violations_rejected += 1
            self.rejection_reasons['no_statutes'] += 1
            logger.info(f"REJECTED: {violation.violation_id} - No statute citations")
            return False
        
        # Check reasoning
        if len(violation.reasoning_chain) < 2:
            self.violations_rejected += 1
            self.rejection_reasons['insufficient_reasoning'] += 1
            logger.info(f"REJECTED: {violation.violation_id} - Insufficient reasoning")
            return False
        
        # ACCEPTED
        self.violations_accepted += 1
        logger.info(f"ACCEPTED: {violation.violation_id} - Evidence strength: {violation.get_evidence_strength_score():.2f}")
        return True
    
    def get_reportable_violations(self, violations: List[ViolationEvidence]) -> List[ViolationEvidence]:
        """
        Filter violations to only those meeting evidence standards
        """
        reportable = []
        for violation in violations:
            if self.evaluate_violation(violation):
                reportable.append(violation)
        
        return reportable
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get evaluation statistics"""
        reportable_rate = (self.violations_accepted / self.violations_evaluated * 100) if self.violations_evaluated > 0 else 0
        
        return {
            'evaluated': self.violations_evaluated,
            'accepted': self.violations_accepted,
            'rejected': self.violations_rejected,
            'reportable_rate': f"{reportable_rate:.1f}%",
            'rejection_reasons': self.rejection_reasons,
            'min_confidence': self.min_confidence.name
        }
    
    def generate_evidence_report(self, violation: ViolationEvidence) -> str:
        """
        Generate formatted evidence report for a violation
        """
        lines = [
            f"VIOLATION: {violation.violation_type}",
            f"ID: {violation.violation_id}",
            f"Severity: {violation.severity}",
            f"Confidence: {violation.confidence.name} ({violation.confidence.value:.0%})",
            f"Evidence Strength: {violation.get_evidence_strength_score():.2f}/1.00",
            "",
            "SUPPORTING EVIDENCE:",
            "-" * 80
        ]
        
        for i, evidence in enumerate(violation.supporting_evidence, 1):
            lines.extend([
                f"\nEvidence {i}: {evidence.evidence_type.value.upper()}",
                f"  Source: {evidence.source_document}",
                f"  Location: {evidence.source_location}",
                f"  Content: {evidence.content}",
                f"  Verification: {evidence.verification_status}",
                f"  Method: {evidence.extraction_method}"
            ])
        
        lines.extend([
            "",
            "STATUTE CITATIONS:",
            "-" * 80
        ])
        
        for i, statute in enumerate(violation.statute_citations, 1):
            lines.extend([
                f"\nStatute {i}: {statute.title}",
                f"  Text: {statute.full_text[:200]}...",
                f"  Violation: {statute.violation_description}",
                f"  Source: {statute.source_url}"
            ])
        
        lines.extend([
            "",
            "REASONING CHAIN:",
            "-" * 80
        ])
        
        for i, step in enumerate(violation.reasoning_chain, 1):
            lines.append(f"{i}. {step}")
        
        lines.extend([
            "",
            f"CONFIDENCE JUSTIFICATION:",
            f"{violation.confidence_justification}",
            "",
            "=" * 80
        ])
        
        return "\n".join(lines)


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Create evidence items
    evidence1 = EvidenceItem(
        evidence_type=EvidenceType.TEMPORAL_DATA,
        source_document="Form 4 (Accession: 0000320187-19-000001)",
        source_location="XML element <transactionDate>",
        content="Transaction Date: 2019-01-15",
        extraction_method="XML parsing",
        verification_status="VERIFIED"
    )
    
    evidence2 = EvidenceItem(
        evidence_type=EvidenceType.METADATA,
        source_document="SEC EDGAR filing header",
        source_location="Filing metadata",
        content="Filing Date: 2019-01-22",
        extraction_method="SEC API response",
        verification_status="VERIFIED"
    )
    
    # Create statute citation
    statute = StatuteCitation(
        title="15 U.S.C. § 78p(a)(2)(A)",
        full_text="Every person who is directly or indirectly the beneficial owner of more than 10 percent of any class of any equity security...shall file...before the end of the second business day following the day on which the subject transaction has been executed",
        violation_description="Filed 5 business days late",
        source_url="https://www.govinfo.gov/content/pkg/USCODE-2011-title15/html/USCODE-2011-title15-chap2B-sec78p.htm",
        penalty_range="$25,000 - $100,000 per violation"
    )
    
    # Create violation evidence
    violation = ViolationEvidence(
        violation_id="NIKE-2019-001",
        violation_type="Section 16(a) Late Form 4 Filing",
        severity="HIGH",
        supporting_evidence=[evidence1, evidence2],
        statute_citations=[statute],
        reasoning_chain=[
            "Transaction executed on 2019-01-15 (extracted from Form 4 XML)",
            "Form 4 filed on 2019-01-22 (SEC EDGAR metadata)",
            "Section 16(a) requires filing within 2 business days of transaction",
            "Business days between 2019-01-15 and 2019-01-22: 5 days",
            "Exceeds 2-day requirement by 3 business days",
            "CONCLUSION: Late filing violation of 15 U.S.C. § 78p(a)"
        ],
        confidence=ConfidenceLevel.DEFINITIVE,
        confidence_justification="Primary source documents verified, calculation confirmed, statute directly applicable"
    )
    
    # Evaluate with reporter
    reporter = EvidenceBackedReporter()
    
    print("Evaluating violation evidence...")
    if reporter.evaluate_violation(violation):
        print("\n✅ VIOLATION ACCEPTED FOR REPORTING\n")
        print(reporter.generate_evidence_report(violation))
    else:
        print("\n❌ VIOLATION REJECTED - Insufficient evidence\n")
    
    print("\nReporter Statistics:")
    stats = reporter.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")

