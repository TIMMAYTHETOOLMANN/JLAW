"""
Burden of Proof Calculator - Legal Burden Analysis
==================================================

Calculates and tracks burden of proof for criminal prosecutions.
Supports multiple burden standards (beyond reasonable doubt, preponderance, etc.)
"""

import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class BurdenStandard(Enum):
    """Legal burden of proof standards"""
    BEYOND_REASONABLE_DOUBT = "beyond_reasonable_doubt"  # Criminal (95%+)
    CLEAR_AND_CONVINCING = "clear_and_convincing"  # Civil fraud (75%+)
    PREPONDERANCE_OF_EVIDENCE = "preponderance"  # Civil (50.1%+)
    REASONABLE_SUSPICION = "reasonable_suspicion"  # Investigation (30%+)


@dataclass
class ChargeElement:
    """Element of a criminal charge that must be proven"""
    element_id: str
    charge_id: str
    description: str
    supporting_evidence: List[str] = field(default_factory=list)
    element_met: bool = False
    confidence: float = 0.0


class BurdenOfProofCalculator:
    """
    Calculates burden of proof for criminal charges
    """
    
    # Threshold for each burden standard
    BURDEN_THRESHOLDS = {
        BurdenStandard.BEYOND_REASONABLE_DOUBT: 0.95,
        BurdenStandard.CLEAR_AND_CONVINCING: 0.75,
        BurdenStandard.PREPONDERANCE_OF_EVIDENCE: 0.51,
        BurdenStandard.REASONABLE_SUSPICION: 0.30,
    }
    
    def __init__(self, standard: BurdenStandard = BurdenStandard.BEYOND_REASONABLE_DOUBT):
        """
        Initialize calculator with burden standard
        
        Args:
            standard: Legal burden of proof standard to apply
        """
        self.standard = standard
        self.threshold = self.BURDEN_THRESHOLDS[standard]
        
        self.stats = {
            'calculations_performed': 0,
            'burdens_met': 0,
            'burdens_not_met': 0
        }
        
        logger.info(f"⚖️ Burden of Proof Calculator initialized")
        logger.info(f"   Standard: {standard.value}")
        logger.info(f"   Threshold: {self.threshold:.0%}")
    
    def calculate_charge_burden(
        self,
        elements: List[ChargeElement],
        evidence_scores: Dict[str, float]
    ) -> Tuple[bool, float, Dict[str, Any]]:
        """
        Calculate whether burden of proof is met for a charge
        
        Args:
            elements: Charge elements to evaluate
            evidence_scores: Evidence ID -> reliability score mapping
        
        Returns:
            Tuple of (burden_met, overall_score, detailed_analysis)
        """
        self.stats['calculations_performed'] += 1
        
        if not elements:
            return False, 0.0, {'error': 'No elements provided'}
        
        element_scores = []
        element_details = []
        
        for element in elements:
            # Calculate element strength based on supporting evidence
            if element.supporting_evidence:
                scores = [
                    evidence_scores.get(eid, 0.0) 
                    for eid in element.supporting_evidence
                ]
                element_score = max(scores) if scores else 0.0
            else:
                element_score = 0.0
            
            element_met = element_score >= self.threshold
            element.element_met = element_met
            element.confidence = element_score
            
            element_scores.append(element_score)
            element_details.append({
                'element_id': element.element_id,
                'description': element.description,
                'score': element_score,
                'met': element_met,
                'supporting_evidence': len(element.supporting_evidence)
            })
        
        # All elements must meet the configured burden threshold
        overall_score = min(element_scores) if element_scores else 0.0
        burden_met = all(e.element_met for e in elements)
        
        if burden_met:
            self.stats['burdens_met'] += 1
        else:
            self.stats['burdens_not_met'] += 1
        
        return burden_met, overall_score, {
            'standard': self.standard.value,
            'threshold': self.threshold,
            'overall_score': overall_score,
            'burden_met': burden_met,
            'elements_analyzed': len(elements),
            'elements_met': sum(1 for e in elements if e.element_met),
            'element_details': element_details
        }
    
    def set_standard(self, standard: BurdenStandard) -> None:
        """Change the burden standard"""
        self.standard = standard
        self.threshold = self.BURDEN_THRESHOLDS[standard]
        logger.info(f"Burden standard changed to: {standard.value} ({self.threshold:.0%})")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get calculator statistics"""
        return self.stats.copy()


if __name__ == "__main__":
    # Demo usage
    calc = BurdenOfProofCalculator()
    
    elements = [
        ChargeElement(
            element_id="E1",
            charge_id="securities_fraud",
            description="Material misstatement",
            supporting_evidence=["EV001", "EV002"]
        ),
        ChargeElement(
            element_id="E2",
            charge_id="securities_fraud",
            description="Scienter (knowledge)",
            supporting_evidence=["EV003"]
        )
    ]
    
    evidence_scores = {
        "EV001": 0.95,
        "EV002": 0.90,
        "EV003": 0.85
    }
    
    met, score, details = calc.calculate_charge_burden(elements, evidence_scores)
    print(f"Burden Met: {met}")
    print(f"Score: {score:.1%}")
    print(f"Details: {details}")
