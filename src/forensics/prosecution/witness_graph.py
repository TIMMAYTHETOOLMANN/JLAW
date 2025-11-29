"""
Witness Graph - Witness Relationship and Credibility Analysis
============================================================

Maps witness relationships and evaluates testimony:
- Witness relationship graphs
- Credibility scoring
- Testimony consistency analysis
- Bias detection
- Corroboration identification
"""

import logging
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class WitnessType(Enum):
    """Types of witnesses"""
    FACT_WITNESS = "fact_witness"
    EXPERT_WITNESS = "expert_witness"
    CHARACTER_WITNESS = "character_witness"
    COOPERATING_WITNESS = "cooperating_witness"


class RelationshipType(Enum):
    """Types of witness relationships"""
    FAMILY = "family"
    COLLEAGUE = "colleague"
    BUSINESS_PARTNER = "business_partner"
    SUBORDINATE = "subordinate"
    SUPERVISOR = "supervisor"
    FRIEND = "friend"
    ADVERSARY = "adversary"
    NEUTRAL = "neutral"


@dataclass
class Testimony:
    """Witness testimony"""
    testimony_id: str
    witness_id: str
    date: datetime
    content: str
    
    # Consistency
    consistency_score: float = 0.0
    contradictions: List[str] = field(default_factory=list)
    
    # Corroboration
    corroborated_by: List[str] = field(default_factory=list)  # Testimony IDs
    
    # Metadata
    under_oath: bool = True
    cross_examined: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Witness:
    """Witness with credibility assessment"""
    witness_id: str
    name: str
    witness_type: WitnessType
    
    # Background
    occupation: str = ""
    relationship_to_defendant: str = ""
    
    # Credibility factors
    credibility_score: float = 0.5
    bias_indicators: List[str] = field(default_factory=list)
    credibility_factors: Dict[str, float] = field(default_factory=dict)
    
    # Testimony
    testimonies: List[Testimony] = field(default_factory=list)
    
    # Relationships
    relationships: Dict[str, RelationshipType] = field(default_factory=dict)
    
    # History
    prior_convictions: List[str] = field(default_factory=list)
    prior_inconsistent_statements: int = 0
    
    def add_testimony(self, testimony: Testimony):
        """Add testimony"""
        self.testimonies.append(testimony)
    
    def calculate_credibility(self) -> float:
        """Calculate overall credibility score"""
        factors = {
            'base': 0.5,
            'expert': 0.2 if self.witness_type == WitnessType.EXPERT_WITNESS else 0.0,
            'oath': 0.1 if any(t.under_oath for t in self.testimonies) else 0.0,
            'cross_examined': 0.1 if any(t.cross_examined for t in self.testimonies) else 0.0,
            'consistency': sum(t.consistency_score for t in self.testimonies) / len(self.testimonies) * 0.2 if self.testimonies else 0.0,
            'bias_penalty': -len(self.bias_indicators) * 0.05,
            'conviction_penalty': -len(self.prior_convictions) * 0.1,
            'inconsistency_penalty': -self.prior_inconsistent_statements * 0.02
        }
        
        self.credibility_factors = factors
        self.credibility_score = max(0.0, min(1.0, sum(factors.values())))
        
        return self.credibility_score


class WitnessGraph:
    """
    Witness relationship graph and credibility analyzer
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Witness registry
        self._witnesses: Dict[str, Witness] = {}
        
        # Testimony registry
        self._testimonies: Dict[str, Testimony] = {}
        
        # Statistics
        self.stats = {
            'witnesses_analyzed': 0,
            'testimonies_analyzed': 0,
            'relationships_mapped': 0,
            'credibility_assessments': 0
        }
    
    def add_witness(self, witness: Witness) -> bool:
        """
        Add witness to graph
        
        Args:
            witness: Witness to add
        
        Returns:
            Success status
        """
        self._witnesses[witness.witness_id] = witness
        self.stats['witnesses_analyzed'] += 1
        
        # Calculate initial credibility
        witness.calculate_credibility()
        self.stats['credibility_assessments'] += 1
        
        logger.info(f"✓ Added witness: {witness.name} (credibility: {witness.credibility_score:.2%})")
        
        return True
    
    def add_testimony(self, testimony: Testimony) -> bool:
        """Add testimony to graph"""
        if testimony.witness_id not in self._witnesses:
            logger.warning(f"⚠️ Witness {testimony.witness_id} not found")
            return False
        
        self._testimonies[testimony.testimony_id] = testimony
        witness = self._witnesses[testimony.witness_id]
        witness.add_testimony(testimony)
        
        self.stats['testimonies_analyzed'] += 1
        
        # Analyze testimony consistency
        self._analyze_testimony_consistency(testimony)
        
        # Recalculate witness credibility
        witness.calculate_credibility()
        
        return True
    
    def add_relationship(
        self,
        witness1_id: str,
        witness2_id: str,
        relationship: RelationshipType
    ) -> bool:
        """Add relationship between witnesses"""
        if witness1_id not in self._witnesses or witness2_id not in self._witnesses:
            return False
        
        w1 = self._witnesses[witness1_id]
        w2 = self._witnesses[witness2_id]
        
        w1.relationships[witness2_id] = relationship
        w2.relationships[witness1_id] = relationship
        
        self.stats['relationships_mapped'] += 1
        
        # Check for bias indicators
        self._detect_bias(w1)
        self._detect_bias(w2)
        
        return True
    
    def find_corroborating_witnesses(
        self,
        testimony_id: str
    ) -> List[Witness]:
        """Find witnesses whose testimony corroborates this testimony"""
        if testimony_id not in self._testimonies:
            return []
        
        target = self._testimonies[testimony_id]
        corroborating = []
        
        for tid, testimony in self._testimonies.items():
            if tid == testimony_id:
                continue
            
            if self._testimonies_corroborate(target, testimony):
                corroborating.append(self._witnesses[testimony.witness_id])
                
                # Update corroboration links
                if tid not in target.corroborated_by:
                    target.corroborated_by.append(tid)
                if testimony_id not in testimony.corroborated_by:
                    testimony.corroborated_by.append(testimony_id)
        
        return corroborating
    
    def detect_testimony_conflicts(self) -> List[Dict[str, Any]]:
        """Detect conflicting testimonies"""
        conflicts = []
        
        testimonies = list(self._testimonies.values())
        
        for i in range(len(testimonies)):
            for j in range(i + 1, len(testimonies)):
                t1 = testimonies[i]
                t2 = testimonies[j]
                
                if self._testimonies_conflict(t1, t2):
                    conflicts.append({
                        'testimony1_id': t1.testimony_id,
                        'testimony2_id': t2.testimony_id,
                        'witness1': self._witnesses[t1.witness_id].name,
                        'witness2': self._witnesses[t2.witness_id].name,
                        'credibility1': self._witnesses[t1.witness_id].credibility_score,
                        'credibility2': self._witnesses[t2.witness_id].credibility_score
                    })
        
        return conflicts
    
    def build_witness_network(self) -> Dict[str, Any]:
        """
        Build witness relationship network
        
        Returns:
            Network graph with nodes and edges
        """
        nodes = []
        edges = []
        
        for witness in self._witnesses.values():
            nodes.append({
                'id': witness.witness_id,
                'name': witness.name,
                'type': witness.witness_type.value,
                'credibility': witness.credibility_score,
                'testimonies': len(witness.testimonies)
            })
            
            # Relationship edges
            for other_id, relationship in witness.relationships.items():
                # Avoid duplicate edges
                if witness.witness_id < other_id:
                    edges.append({
                        'from': witness.witness_id,
                        'to': other_id,
                        'relationship': relationship.value
                    })
        
        return {
            'nodes': nodes,
            'edges': edges,
            'statistics': {
                'total_witnesses': len(nodes),
                'total_relationships': len(edges),
                'avg_credibility': sum(n['credibility'] for n in nodes) / len(nodes) if nodes else 0.0
            }
        }
    
    def identify_key_witnesses(self, top_n: int = 5) -> List[Witness]:
        """Identify most important witnesses"""
        # Score based on credibility and testimony count
        scored = []
        
        for witness in self._witnesses.values():
            score = witness.credibility_score * len(witness.testimonies)
            scored.append((score, witness))
        
        scored.sort(reverse=True, key=lambda x: x[0])
        
        return [w for _, w in scored[:top_n]]
    
    def _analyze_testimony_consistency(self, testimony: Testimony):
        """Analyze testimony internal consistency"""
        # Simplified consistency check
        witness = self._witnesses[testimony.witness_id]
        
        # Compare with previous testimonies
        contradictions = []
        
        for prev_testimony in witness.testimonies:
            if prev_testimony.testimony_id == testimony.testimony_id:
                continue
            
            if self._testimonies_conflict(testimony, prev_testimony):
                contradictions.append(prev_testimony.testimony_id)
        
        testimony.contradictions = contradictions
        
        # Calculate consistency score
        if witness.testimonies:
            testimony.consistency_score = 1.0 - (len(contradictions) / max(len(witness.testimonies), 1))
        else:
            testimony.consistency_score = 1.0
    
    def _detect_bias(self, witness: Witness):
        """Detect bias indicators"""
        bias_indicators = []
        
        # Family relationship
        for other_id, rel_type in witness.relationships.items():
            if rel_type == RelationshipType.FAMILY:
                bias_indicators.append(f"Family relationship with {other_id}")
        
        # Business interests
        if any(rel_type == RelationshipType.BUSINESS_PARTNER for rel_type in witness.relationships.values()):
            bias_indicators.append("Business partner relationship")
        
        # Adversarial relationship
        if any(rel_type == RelationshipType.ADVERSARY for rel_type in witness.relationships.values()):
            bias_indicators.append("Adversarial relationship")
        
        # Cooperating witness (potential bias for leniency)
        if witness.witness_type == WitnessType.COOPERATING_WITNESS:
            bias_indicators.append("Cooperating witness seeking leniency")
        
        witness.bias_indicators = bias_indicators
    
    def _testimonies_corroborate(self, t1: Testimony, t2: Testimony) -> bool:
        """Check if testimonies corroborate each other"""
        # Simplified - check content overlap
        words1 = set(t1.content.lower().split())
        words2 = set(t2.content.lower().split())
        
        overlap = len(words1 & words2) / max(len(words1), len(words2), 1)
        
        return overlap > 0.4
    
    def _testimonies_conflict(self, t1: Testimony, t2: Testimony) -> bool:
        """Check if testimonies conflict"""
        # Simplified - look for negation patterns
        content1 = t1.content.lower()
        content2 = t2.content.lower()
        
        # Look for direct contradictions (simplified)
        negations = ['not', 'never', 'no', 'false', 'incorrect']
        
        words1 = set(content1.split())
        words2 = set(content2.split())
        
        # If one has negation and they share content, might conflict
        has_negation1 = any(neg in words1 for neg in negations)
        has_negation2 = any(neg in words2 for neg in negations)
        
        if has_negation1 != has_negation2:
            overlap = len(words1 & words2) / max(len(words1), len(words2), 1)
            return overlap > 0.3
        
        return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get graph statistics"""
        return self.stats.copy()


if __name__ == "__main__":
    # Demo usage
    graph = WitnessGraph()
    
    # Create witnesses
    witness1 = Witness(
        witness_id="W001",
        name="John Doe",
        witness_type=WitnessType.FACT_WITNESS,
        occupation="Accountant"
    )
    
    witness2 = Witness(
        witness_id="W002",
        name="Jane Smith",
        witness_type=WitnessType.EXPERT_WITNESS,
        occupation="Forensic Accountant"
    )
    
    # Add witnesses
    graph.add_witness(witness1)
    graph.add_witness(witness2)
    
    # Add relationship
    graph.add_relationship("W001", "W002", RelationshipType.COLLEAGUE)
    
    # Add testimony
    testimony = Testimony(
        testimony_id="T001",
        witness_id="W001",
        date=datetime.now(),
        content="I witnessed the transaction on January 15, 2024"
    )
    
    graph.add_testimony(testimony)
    
    # Get network
    network = graph.build_witness_network()
    print(f"Witness network: {network['statistics']}")

