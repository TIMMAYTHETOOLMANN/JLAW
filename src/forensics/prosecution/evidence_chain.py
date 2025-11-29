"""
Evidence Chain Analyzer - Chain of Custody and Evidence Validation
=================================================================

Validates evidence chains for admissibility and strength:
- Chain of custody verification
- Evidence admissibility rules (Federal Rules of Evidence)
- Evidence type classification
- Corroboration analysis
- Reliability scoring

Federal Rules of Evidence compliance:
- Rule 401: Relevance
- Rule 403: Prejudice vs probative value
- Rule 702: Expert testimony
- Rule 801-807: Hearsay
- Rule 901: Authentication
"""

import logging
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import hashlib

logger = logging.getLogger(__name__)


class EvidenceType(Enum):
    """Types of evidence"""
    DOCUMENTARY = "documentary"
    TESTIMONIAL = "testimonial"
    PHYSICAL = "physical"
    DIGITAL = "digital"
    DEMONSTRATIVE = "demonstrative"
    EXPERT = "expert"


class AdmissibilityStatus(Enum):
    """Evidence admissibility status"""
    ADMISSIBLE = "admissible"
    INADMISSIBLE = "inadmissible"
    CONDITIONAL = "conditional"
    CHALLENGED = "challenged"


@dataclass
class ChainOfCustodyEntry:
    """Single entry in chain of custody"""
    timestamp: datetime
    custodian: str
    action: str  # 'collected', 'transferred', 'analyzed', 'stored'
    location: str
    condition: str
    hash_value: Optional[str] = None
    signature: Optional[str] = None
    notes: str = ""


@dataclass
class EvidenceItem:
    """Evidence item with metadata"""
    evidence_id: str
    description: str
    evidence_type: EvidenceType
    
    # Origin
    source: str
    collected_date: datetime
    collected_by: str
    
    # Content
    content: Any
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Chain of custody
    custody_chain: List[ChainOfCustodyEntry] = field(default_factory=list)
    
    # Admissibility
    admissibility_status: AdmissibilityStatus = AdmissibilityStatus.CONDITIONAL
    admissibility_issues: List[str] = field(default_factory=list)
    
    # Strength
    reliability_score: float = 0.0
    corroboration_count: int = 0
    
    # Links
    corroborates: List[str] = field(default_factory=list)  # Evidence IDs
    contradicts: List[str] = field(default_factory=list)   # Evidence IDs
    supports_charges: List[str] = field(default_factory=list)  # Charge IDs
    
    def get_integrity_hash(self) -> str:
        """Calculate integrity hash"""
        content_str = str(self.content)
        return hashlib.sha256(content_str.encode()).hexdigest()
    
    def verify_chain_of_custody(self) -> Tuple[bool, List[str]]:
        """Verify chain of custody integrity"""
        issues = []
        
        if not self.custody_chain:
            issues.append("No chain of custody recorded")
            return False, issues
        
        # Check chronological order
        timestamps = [entry.timestamp for entry in self.custody_chain]
        if timestamps != sorted(timestamps):
            issues.append("Chain of custody not in chronological order")
        
        # Check for gaps
        for i in range(len(self.custody_chain) - 1):
            time_gap = (self.custody_chain[i+1].timestamp - self.custody_chain[i].timestamp).total_seconds()
            if time_gap > 86400 * 7:  # 7 days
                issues.append(f"Significant time gap in custody ({time_gap/86400:.1f} days)")
        
        # Check hash consistency (if available)
        hashes = [entry.hash_value for entry in self.custody_chain if entry.hash_value]
        if len(hashes) > 1 and len(set(hashes)) > 1:
            issues.append("Hash values changed during custody")
        
        return len(issues) == 0, issues


class EvidenceChainAnalyzer:
    """
    Analyzes evidence chains for admissibility and strength
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Federal Rules of Evidence
        self.admissibility_rules = self._initialize_admissibility_rules()
        
        # Evidence registry
        self._evidence_items: Dict[str, EvidenceItem] = {}
        
        # Statistics
        self.stats = {
            'evidence_analyzed': 0,
            'admissible': 0,
            'inadmissible': 0,
            'conditional': 0,
            'chains_verified': 0
        }
    
    def _initialize_admissibility_rules(self) -> Dict[str, Dict[str, Any]]:
        """Initialize Federal Rules of Evidence"""
        return {
            'relevance': {
                'rule': 'FRE 401',
                'description': 'Evidence must be relevant to case',
                'test': self._test_relevance
            },
            'prejudice': {
                'rule': 'FRE 403',
                'description': 'Probative value must outweigh prejudice',
                'test': self._test_prejudice
            },
            'hearsay': {
                'rule': 'FRE 801-807',
                'description': 'Out-of-court statements',
                'test': self._test_hearsay
            },
            'authentication': {
                'rule': 'FRE 901',
                'description': 'Evidence must be authenticated',
                'test': self._test_authentication
            },
            'best_evidence': {
                'rule': 'FRE 1002',
                'description': 'Original documents preferred',
                'test': self._test_best_evidence
            }
        }
    
    def add_evidence(self, evidence: EvidenceItem) -> bool:
        """
        Add evidence to chain
        
        Args:
            evidence: Evidence item to add
        
        Returns:
            Success status
        """
        self._evidence_items[evidence.evidence_id] = evidence
        
        # Analyze admissibility
        self._analyze_admissibility(evidence)
        
        # Calculate reliability
        evidence.reliability_score = self._calculate_reliability(evidence)
        
        self.stats['evidence_analyzed'] += 1
        self.stats[evidence.admissibility_status.value] += 1
        
        logger.info(f"✓ Added evidence: {evidence.evidence_id} ({evidence.admissibility_status.value})")
        
        return True
    
    def verify_evidence_chain(self, evidence_id: str) -> Dict[str, Any]:
        """
        Verify complete evidence chain
        
        Args:
            evidence_id: Evidence identifier
        
        Returns:
            Verification report
        """
        if evidence_id not in self._evidence_items:
            return {'valid': False, 'error': 'Evidence not found'}
        
        evidence = self._evidence_items[evidence_id]
        self.stats['chains_verified'] += 1
        
        # Verify chain of custody
        custody_valid, custody_issues = evidence.verify_chain_of_custody()
        
        # Check integrity hash
        current_hash = evidence.get_integrity_hash()
        original_hash = evidence.custody_chain[0].hash_value if evidence.custody_chain else None
        hash_valid = (current_hash == original_hash) if original_hash else True
        
        # Check admissibility
        admissibility_valid = evidence.admissibility_status == AdmissibilityStatus.ADMISSIBLE
        
        report = {
            'evidence_id': evidence_id,
            'valid': custody_valid and hash_valid and admissibility_valid,
            'chain_of_custody': {
                'valid': custody_valid,
                'entries': len(evidence.custody_chain),
                'issues': custody_issues
            },
            'integrity': {
                'valid': hash_valid,
                'current_hash': current_hash,
                'original_hash': original_hash
            },
            'admissibility': {
                'status': evidence.admissibility_status.value,
                'issues': evidence.admissibility_issues
            },
            'reliability_score': evidence.reliability_score
        }
        
        return report
    
    def find_corroborating_evidence(
        self,
        evidence_id: str
    ) -> List[EvidenceItem]:
        """Find evidence that corroborates this evidence"""
        if evidence_id not in self._evidence_items:
            return []
        
        target = self._evidence_items[evidence_id]
        corroborating = []
        
        for eid, evidence in self._evidence_items.items():
            if eid == evidence_id:
                continue
            
            # Check if evidence corroborates target
            if self._evidences_corroborate(target, evidence):
                corroborating.append(evidence)
                
                # Update corroboration links
                if eid not in target.corroborates:
                    target.corroborates.append(eid)
                if evidence_id not in evidence.corroborates:
                    evidence.corroborates.append(evidence_id)
        
        # Update corroboration count
        target.corroboration_count = len(corroborating)
        
        return corroborating
    
    def build_evidence_graph(self) -> Dict[str, Any]:
        """
        Build evidence relationship graph
        
        Returns:
            Graph with nodes and edges
        """
        nodes = []
        edges = []
        
        for evidence in self._evidence_items.values():
            # Node
            nodes.append({
                'id': evidence.evidence_id,
                'type': evidence.evidence_type.value,
                'admissible': evidence.admissibility_status == AdmissibilityStatus.ADMISSIBLE,
                'reliability': evidence.reliability_score
            })
            
            # Corroboration edges
            for corr_id in evidence.corroborates:
                edges.append({
                    'from': evidence.evidence_id,
                    'to': corr_id,
                    'type': 'corroborates'
                })
            
            # Contradiction edges
            for contr_id in evidence.contradicts:
                edges.append({
                    'from': evidence.evidence_id,
                    'to': contr_id,
                    'type': 'contradicts'
                })
        
        return {
            'nodes': nodes,
            'edges': edges,
            'statistics': {
                'total_evidence': len(nodes),
                'admissible': sum(1 for n in nodes if n['admissible']),
                'corroboration_links': sum(1 for e in edges if e['type'] == 'corroborates'),
                'contradiction_links': sum(1 for e in edges if e['type'] == 'contradicts')
            }
        }
    
    def _analyze_admissibility(self, evidence: EvidenceItem):
        """Analyze evidence admissibility"""
        issues = []
        
        # Test each admissibility rule
        for rule_name, rule_info in self.admissibility_rules.items():
            test_func = rule_info['test']
            passed, issue = test_func(evidence)
            
            if not passed:
                issues.append(f"{rule_info['rule']}: {issue}")
        
        # Determine admissibility status
        if not issues:
            evidence.admissibility_status = AdmissibilityStatus.ADMISSIBLE
        elif len(issues) >= 3:
            evidence.admissibility_status = AdmissibilityStatus.INADMISSIBLE
        else:
            evidence.admissibility_status = AdmissibilityStatus.CONDITIONAL
        
        evidence.admissibility_issues = issues
    
    def _calculate_reliability(self, evidence: EvidenceItem) -> float:
        """Calculate evidence reliability score"""
        score = 0.5  # Base score
        
        # Chain of custody factor
        custody_valid, _ = evidence.verify_chain_of_custody()
        if custody_valid:
            score += 0.2
        
        # Evidence type reliability
        type_scores = {
            EvidenceType.DOCUMENTARY: 0.15,
            EvidenceType.DIGITAL: 0.15,
            EvidenceType.PHYSICAL: 0.10,
            EvidenceType.TESTIMONIAL: 0.05,
            EvidenceType.EXPERT: 0.10,
            EvidenceType.DEMONSTRATIVE: 0.05
        }
        score += type_scores.get(evidence.evidence_type, 0.0)
        
        # Corroboration bonus
        score += min(evidence.corroboration_count * 0.05, 0.15)
        
        # Admissibility penalty
        if evidence.admissibility_status == AdmissibilityStatus.INADMISSIBLE:
            score *= 0.5
        elif evidence.admissibility_status == AdmissibilityStatus.CONDITIONAL:
            score *= 0.8
        
        return min(score, 1.0)
    
    def _evidences_corroborate(self, e1: EvidenceItem, e2: EvidenceItem) -> bool:
        """Check if two pieces of evidence corroborate each other"""
        # Check if they support same charges
        common_charges = set(e1.supports_charges) & set(e2.supports_charges)
        if not common_charges:
            return False
        
        # Check if they're from different sources (more valuable)
        if e1.source == e2.source:
            return False
        
        # Check content similarity (simplified)
        content1 = str(e1.content).lower()
        content2 = str(e2.content).lower()
        
        # Simple overlap check
        words1 = set(content1.split())
        words2 = set(content2.split())
        overlap = len(words1 & words2) / max(len(words1), len(words2), 1)
        
        return overlap > 0.3
    
    # Admissibility test functions
    def _test_relevance(self, evidence: EvidenceItem) -> Tuple[bool, str]:
        """Test FRE 401 - Relevance"""
        # Evidence is relevant if it supports charges
        if evidence.supports_charges:
            return True, ""
        return False, "Evidence does not support any charges"
    
    def _test_prejudice(self, evidence: EvidenceItem) -> Tuple[bool, str]:
        """Test FRE 403 - Prejudice vs probative value"""
        # Simplified test - assume acceptable unless flagged
        if evidence.metadata.get('highly_prejudicial'):
            return False, "Unfair prejudice outweighs probative value"
        return True, ""
    
    def _test_hearsay(self, evidence: EvidenceItem) -> Tuple[bool, str]:
        """Test FRE 801-807 - Hearsay"""
        if evidence.evidence_type == EvidenceType.TESTIMONIAL:
            if evidence.metadata.get('hearsay') and not evidence.metadata.get('hearsay_exception'):
                return False, "Inadmissible hearsay"
        return True, ""
    
    def _test_authentication(self, evidence: EvidenceItem) -> Tuple[bool, str]:
        """Test FRE 901 - Authentication"""
        # Check if evidence has proper authentication
        if not evidence.custody_chain:
            return False, "Evidence not authenticated"
        return True, ""
    
    def _test_best_evidence(self, evidence: EvidenceItem) -> Tuple[bool, str]:
        """Test FRE 1002 - Best evidence rule"""
        if evidence.evidence_type == EvidenceType.DOCUMENTARY:
            if evidence.metadata.get('is_copy') and not evidence.metadata.get('original_unavailable'):
                return False, "Original document required"
        return True, ""
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get analyzer statistics"""
        return self.stats.copy()


if __name__ == "__main__":
    # Demo usage
    analyzer = EvidenceChainAnalyzer()
    
    # Create evidence
    evidence = EvidenceItem(
        evidence_id="E001",
        description="Email discussing insider trade",
        evidence_type=EvidenceType.DIGITAL,
        source="email_server",
        collected_date=datetime.now(),
        collected_by="Agent Smith",
        content="Email content here...",
        supports_charges=["insider_trading", "securities_fraud"]
    )
    
    # Add chain of custody
    evidence.custody_chain.append(ChainOfCustodyEntry(
        timestamp=datetime.now(),
        custodian="Agent Smith",
        action="collected",
        location="Server Room",
        condition="digital_copy",
        hash_value=evidence.get_integrity_hash()
    ))
    
    # Add evidence
    analyzer.add_evidence(evidence)
    
    # Verify chain
    report = analyzer.verify_evidence_chain("E001")
    print(f"Evidence verification: {report['valid']}")
    print(f"Reliability: {report['reliability_score']:.2%}")

