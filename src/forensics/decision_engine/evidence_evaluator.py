"""
Forensic Evidence Evaluator
Evaluates evidence for admissibility, strength, and weight.
"""

from typing import List, Optional, Dict, Any, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class EvidenceType(Enum):
    """Types of evidence."""
    DOCUMENT = "document"
    TESTIMONY = "testimony"
    FINANCIAL_RECORD = "financial_record"
    DIGITAL = "digital"
    FORENSIC_ANALYSIS = "forensic_analysis"
    EXPERT_OPINION = "expert_opinion"
    TIMELINE = "timeline"
    CONTRADICTION = "contradiction"
    STATISTICAL = "statistical"


class AdmissibilityIssue(Enum):
    """Issues affecting admissibility."""
    HEARSAY = "hearsay"
    AUTHENTICATION = "authentication"
    RELEVANCE = "relevance"
    PRIVILEGE = "privilege"
    BEST_EVIDENCE = "best_evidence"
    PREJUDICE = "prejudice"
    CHAIN_OF_CUSTODY = "chain_of_custody"


class HearsayException(Enum):
    """Federal Rules of Evidence hearsay exceptions."""
    BUSINESS_RECORD = "business_record"  # FRE 803(6)
    PUBLIC_RECORD = "public_record"  # FRE 803(8)
    ADMISSION = "admission"  # FRE 801(d)(2)
    EXCITED_UTTERANCE = "excited_utterance"  # FRE 803(2)
    PRESENT_SENSE = "present_sense"  # FRE 803(1)
    STATEMENT_AGAINST_INTEREST = "statement_against_interest"  # FRE 804(b)(3)


@dataclass
class Evidence:
    """Base evidence structure."""
    id: str
    evidence_type: EvidenceType
    description: str
    source: str
    date_obtained: datetime
    content: Any
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Chain of custody
    custody_chain: List[str] = field(default_factory=list)
    hash_value: Optional[str] = None


@dataclass
class Authentication:
    """Authentication assessment for evidence."""
    valid: bool
    method: str  # FRE 901 authentication method
    confidence: float
    issues: List[str] = field(default_factory=list)
    supporting_evidence: List[str] = field(default_factory=list)


@dataclass
class HearsayAnalysis:
    """Hearsay analysis per FRE 801-807."""
    is_hearsay: bool
    explanation: str
    exceptions_applicable: List[HearsayException] = field(default_factory=list)
    admissible_despite_hearsay: bool = False


@dataclass
class RelevanceAssessment:
    """Relevance assessment per FRE 401-403."""
    score: float  # 0-1 scale
    probative_value: float
    prejudice_risk: float
    tends_to_prove: List[str] = field(default_factory=list)
    material_to: List[str] = field(default_factory=list)


@dataclass
class PrivilegeAnalysis:
    """Privilege analysis."""
    applies: bool
    privilege_type: Optional[str] = None
    waived: bool = False
    exceptions: List[str] = field(default_factory=list)


@dataclass
class Admissibility:
    """Complete admissibility assessment."""
    is_admissible: bool
    authentication: Authentication
    hearsay_analysis: HearsayAnalysis
    relevance: RelevanceAssessment
    privilege: PrivilegeAnalysis
    exceptions: List[str] = field(default_factory=list)
    issues: List[AdmissibilityIssue] = field(default_factory=list)
    confidence: float = 1.0


@dataclass
class EvidenceStrength:
    """Evidence strength assessment."""
    overall_strength: float  # 0-1 scale
    factual_accuracy: float
    source_credibility: float
    corroboration_level: float
    forensic_soundness: float
    temporal_consistency: float


@dataclass
class EvidenceIssue:
    """Issue with evidence."""
    issue_type: str
    severity: str  # 'critical', 'high', 'medium', 'low'
    description: str
    resolution: Optional[str] = None
    impact_on_admissibility: float = 0.0


@dataclass
class EvaluatedEvidence:
    """Evidence with complete evaluation."""
    evidence: Evidence
    admissibility: Admissibility
    strength: EvidenceStrength
    weight: float  # Combined score (0-1)
    corroboration: List[Evidence]
    issues: List[EvidenceIssue]
    enhancements: List[str]
    legal_foundation: List[str]
    statute_support: List[str] = field(default_factory=list)


class ForensicEvidenceEvaluator:
    """
    Comprehensive evidence evaluator integrating with forensic system.
    
    Evaluates evidence for:
    - Legal admissibility (Federal Rules of Evidence)
    - Forensic strength
    - Corroboration
    - Weight in prosecution
    """
    
    def __init__(self):
        """Initialize evidence evaluator."""
        logger.info("ForensicEvidenceEvaluator initialized")
    
    async def evaluate(
        self,
        evidence: List[Evidence],
        case_context: Optional[Dict[str, Any]] = None
    ) -> List[EvaluatedEvidence]:
        """
        Evaluate all evidence comprehensively.
        
        Args:
            evidence: List of evidence to evaluate
            case_context: Optional case context
        
        Returns:
            List of evaluated evidence
        """
        logger.info(f"Evaluating {len(evidence)} pieces of evidence...")
        
        evaluated = []
        
        for item in evidence:
            # Assess admissibility
            admissibility = await self._assess_admissibility(item)
            
            # Assess strength
            strength = await self._assess_strength(item)
            
            # Find corroboration
            corroboration = await self._find_corroboration(item, evidence)
            
            # Calculate weight
            weight = self._calculate_weight(admissibility, strength, corroboration)
            
            # Identify issues
            issues = self._identify_issues(item, admissibility, strength)
            
            # Suggest enhancements
            enhancements = self._suggest_enhancements(item, issues)
            
            # Identify legal foundation
            legal_foundation = self._identify_legal_foundation(item)
            
            evaluated_item = EvaluatedEvidence(
                evidence=item,
                admissibility=admissibility,
                strength=strength,
                weight=weight,
                corroboration=corroboration,
                issues=issues,
                enhancements=enhancements,
                legal_foundation=legal_foundation
            )
            
            evaluated.append(evaluated_item)
        
        logger.info(f"Evaluation complete. Average weight: {sum(e.weight for e in evaluated)/len(evaluated):.2f}")
        return evaluated
    
    async def _assess_admissibility(self, evidence: Evidence) -> Admissibility:
        """Assess evidence admissibility per Federal Rules of Evidence."""
        # Check authentication (FRE 901)
        authentication = self._check_authentication(evidence)
        
        # Check hearsay (FRE 801-807)
        hearsay = self._analyze_hearsay(evidence)
        
        # Check relevance (FRE 401-403)
        relevance = self._assess_relevance(evidence)
        
        # Check privilege
        privilege = self._check_privilege(evidence)
        
        # Determine overall admissibility
        is_admissible = (
            authentication.valid and
            (not hearsay.is_hearsay or hearsay.admissible_despite_hearsay) and
            relevance.score > 0.5 and
            not privilege.applies
        )
        
        # Identify issues
        issues = []
        if not authentication.valid:
            issues.append(AdmissibilityIssue.AUTHENTICATION)
        if hearsay.is_hearsay and not hearsay.admissible_despite_hearsay:
            issues.append(AdmissibilityIssue.HEARSAY)
        if relevance.score <= 0.5:
            issues.append(AdmissibilityIssue.RELEVANCE)
        if privilege.applies and not privilege.waived:
            issues.append(AdmissibilityIssue.PRIVILEGE)
        
        # Find applicable exceptions
        exceptions = []
        if hearsay.exceptions_applicable:
            exceptions.extend([e.value for e in hearsay.exceptions_applicable])
        
        confidence = min(
            authentication.confidence,
            relevance.score,
            0.9 if is_admissible else 0.3
        )
        
        return Admissibility(
            is_admissible=is_admissible,
            authentication=authentication,
            hearsay_analysis=hearsay,
            relevance=relevance,
            privilege=privilege,
            exceptions=exceptions,
            issues=issues,
            confidence=confidence
        )
    
    def _check_authentication(self, evidence: Evidence) -> Authentication:
        """Check authentication per FRE 901."""
        # Different authentication methods based on evidence type
        if evidence.evidence_type == EvidenceType.DOCUMENT:
            # Check for signatures, seals, or chain of custody
            has_hash = evidence.hash_value is not None
            has_custody = len(evidence.custody_chain) > 0
            
            valid = has_hash or has_custody
            method = "FRE 901(b)(1) - Testimony of witness with knowledge"
            confidence = 0.9 if (has_hash and has_custody) else 0.6
            
        elif evidence.evidence_type == EvidenceType.DIGITAL:
            # Requires hash and chain of custody
            valid = evidence.hash_value is not None
            method = "FRE 901(b)(9) - Process or system"
            confidence = 0.95 if valid else 0.3
            
        elif evidence.evidence_type == EvidenceType.FORENSIC_ANALYSIS:
            # Requires expert credentials and methodology
            valid = True  # Assume forensic system provides this
            method = "FRE 901(b)(1) - Expert testimony"
            confidence = 0.95
            
        else:
            valid = True
            method = "FRE 901(b)(1) - Testimony"
            confidence = 0.7
        
        issues = []
        if not valid:
            issues.append("Authentication insufficient")
        
        return Authentication(
            valid=valid,
            method=method,
            confidence=confidence,
            issues=issues
        )
    
    def _analyze_hearsay(self, evidence: Evidence) -> HearsayAnalysis:
        """Analyze hearsay per FRE 801-807."""
        # Determine if evidence is hearsay
        is_hearsay = evidence.evidence_type in [
            EvidenceType.DOCUMENT,
            EvidenceType.TESTIMONY
        ]
        
        exceptions = []
        admissible = False
        explanation = ""
        
        if is_hearsay:
            # Check for business records exception (FRE 803(6))
            if evidence.evidence_type == EvidenceType.FINANCIAL_RECORD:
                exceptions.append(HearsayException.BUSINESS_RECORD)
                admissible = True
                explanation = "Business record exception applies (FRE 803(6))"
            
            # Check for public records exception (FRE 803(8))
            elif 'sec_filing' in str(evidence.source).lower():
                exceptions.append(HearsayException.PUBLIC_RECORD)
                admissible = True
                explanation = "Public record exception applies (FRE 803(8))"
            
            # Check for admission by party-opponent (FRE 801(d)(2))
            elif evidence.metadata.get('party_admission'):
                exceptions.append(HearsayException.ADMISSION)
                admissible = True
                explanation = "Party admission - not hearsay (FRE 801(d)(2))"
            
            else:
                explanation = "Hearsay without applicable exception"
        else:
            explanation = "Not hearsay - forensic analysis or direct observation"
        
        return HearsayAnalysis(
            is_hearsay=is_hearsay,
            explanation=explanation,
            exceptions_applicable=exceptions,
            admissible_despite_hearsay=admissible
        )
    
    def _assess_relevance(self, evidence: Evidence) -> RelevanceAssessment:
        """Assess relevance per FRE 401-403."""
        # Calculate probative value
        probative = 0.8  # Default high value for forensic evidence
        
        # Calculate prejudice risk
        prejudice = 0.2  # Low for forensic evidence
        
        # Overall relevance score
        score = probative - prejudice
        
        tends_to_prove = [
            "Material fact in issue",
            "Element of violation",
            "Intent or knowledge"
        ]
        
        material_to = evidence.metadata.get('material_to', [])
        
        return RelevanceAssessment(
            score=max(0.0, min(1.0, score)),
            probative_value=probative,
            prejudice_risk=prejudice,
            tends_to_prove=tends_to_prove,
            material_to=material_to
        )
    
    def _check_privilege(self, evidence: Evidence) -> PrivilegeAnalysis:
        """Check for privilege issues."""
        # Check common privileges
        applies = False
        privilege_type = None
        
        if 'attorney' in str(evidence.source).lower():
            applies = True
            privilege_type = "Attorney-client privilege"
        elif 'doctor' in str(evidence.source).lower():
            applies = True
            privilege_type = "Physician-patient privilege"
        
        # Check for waiver
        waived = evidence.metadata.get('privilege_waived', False)
        
        return PrivilegeAnalysis(
            applies=applies,
            privilege_type=privilege_type,
            waived=waived
        )
    
    async def _assess_strength(self, evidence: Evidence) -> EvidenceStrength:
        """Assess overall evidence strength."""
        # Factual accuracy (based on type)
        accuracy_map = {
            EvidenceType.FORENSIC_ANALYSIS: 0.95,
            EvidenceType.FINANCIAL_RECORD: 0.9,
            EvidenceType.DOCUMENT: 0.85,
            EvidenceType.DIGITAL: 0.9,
            EvidenceType.STATISTICAL: 0.85,
            EvidenceType.TESTIMONY: 0.7,
            EvidenceType.EXPERT_OPINION: 0.8
        }
        factual_accuracy = accuracy_map.get(evidence.evidence_type, 0.7)
        
        # Source credibility
        source_credibility = 0.9  # High for forensic system
        if 'sec.gov' in str(evidence.source).lower():
            source_credibility = 0.95
        
        # Corroboration (will be calculated later)
        corroboration_level = 0.5  # Default
        
        # Forensic soundness
        forensic_soundness = 0.9 if evidence.hash_value else 0.7
        
        # Temporal consistency
        temporal_consistency = 0.8  # Default
        
        # Overall strength
        overall = (
            factual_accuracy * 0.3 +
            source_credibility * 0.2 +
            corroboration_level * 0.2 +
            forensic_soundness * 0.15 +
            temporal_consistency * 0.15
        )
        
        return EvidenceStrength(
            overall_strength=overall,
            factual_accuracy=factual_accuracy,
            source_credibility=source_credibility,
            corroboration_level=corroboration_level,
            forensic_soundness=forensic_soundness,
            temporal_consistency=temporal_consistency
        )
    
    async def _find_corroboration(
        self,
        evidence: Evidence,
        all_evidence: List[Evidence]
    ) -> List[Evidence]:
        """Find corroborating evidence."""
        corroboration = []
        
        for other in all_evidence:
            if other.id == evidence.id:
                continue
            
            # Check for corroboration based on content similarity
            # or temporal proximity
            if self._is_corroborating(evidence, other):
                corroboration.append(other)
        
        return corroboration[:5]  # Top 5 corroborating pieces
    
    def _is_corroborating(self, evidence1: Evidence, evidence2: Evidence) -> bool:
        """Check if evidence2 corroborates evidence1."""
        # Simple heuristic: same source or related content
        same_source = evidence1.source == evidence2.source
        
        # Check temporal proximity (within 30 days)
        time_diff = abs((evidence1.date_obtained - evidence2.date_obtained).days)
        temporal_proximity = time_diff <= 30
        
        return same_source or temporal_proximity
    
    def _calculate_weight(
        self,
        admissibility: Admissibility,
        strength: EvidenceStrength,
        corroboration: List[Evidence]
    ) -> float:
        """Calculate overall evidence weight."""
        # Start with strength
        weight = strength.overall_strength
        
        # Adjust for admissibility
        if not admissibility.is_admissible:
            weight *= 0.3  # Severely reduced if inadmissible
        else:
            weight *= admissibility.confidence
        
        # Boost for corroboration
        corroboration_boost = min(len(corroboration) * 0.1, 0.5)
        weight *= (1 + corroboration_boost)
        
        return min(1.0, weight)
    
    def _identify_issues(
        self,
        evidence: Evidence,
        admissibility: Admissibility,
        strength: EvidenceStrength
    ) -> List[EvidenceIssue]:
        """Identify issues with evidence."""
        issues = []
        
        # Admissibility issues
        for issue_type in admissibility.issues:
            issues.append(EvidenceIssue(
                issue_type=issue_type.value,
                severity='high',
                description=f"Admissibility issue: {issue_type.value}",
                impact_on_admissibility=0.7
            ))
        
        # Strength issues
        if strength.overall_strength < 0.5:
            issues.append(EvidenceIssue(
                issue_type='weak_evidence',
                severity='medium',
                description="Evidence strength below threshold",
                impact_on_admissibility=0.3
            ))
        
        # Chain of custody issues
        if not evidence.custody_chain:
            issues.append(EvidenceIssue(
                issue_type='custody',
                severity='medium',
                description="Chain of custody not established",
                impact_on_admissibility=0.4
            ))
        
        return issues
    
    def _suggest_enhancements(
        self,
        evidence: Evidence,
        issues: List[EvidenceIssue]
    ) -> List[str]:
        """Suggest ways to enhance evidence."""
        enhancements = []
        
        for issue in issues:
            if issue.issue_type == 'authentication':
                enhancements.append("Obtain authenticating witness testimony")
            elif issue.issue_type == 'hearsay':
                enhancements.append("Establish business records exception")
            elif issue.issue_type == 'custody':
                enhancements.append("Document complete chain of custody")
            elif issue.issue_type == 'weak_evidence':
                enhancements.append("Seek corroborating evidence")
        
        return enhancements
    
    def _identify_legal_foundation(self, evidence: Evidence) -> List[str]:
        """Identify legal foundation for evidence."""
        foundation = []
        
        # Federal Rules of Evidence
        foundation.append("FRE 401 - Relevance")
        foundation.append("FRE 901 - Authentication")
        
        if evidence.evidence_type == EvidenceType.FORENSIC_ANALYSIS:
            foundation.append("FRE 702 - Expert Testimony")
            foundation.append("Daubert standard for scientific evidence")
        
        if evidence.evidence_type == EvidenceType.FINANCIAL_RECORD:
            foundation.append("FRE 803(6) - Business Records Exception")
        
        return foundation

