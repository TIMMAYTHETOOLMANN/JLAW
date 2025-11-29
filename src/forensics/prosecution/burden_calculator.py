"""
Burden of Proof Calculator
==========================
Calculates legal burden standards for different charge types.

Legal burden standards:
- Beyond Reasonable Doubt (criminal): ~95-99%
- Clear and Convincing Evidence: ~75%
- Preponderance of Evidence (civil): ~51%
"""

from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass


class BurdenStandard(Enum):
    """Legal burden of proof standards"""
    BEYOND_REASONABLE_DOUBT = "beyond_reasonable_doubt"  # Criminal: 95-99%
    CLEAR_AND_CONVINCING = "clear_and_convincing"  # Civil fraud: 75%
    PREPONDERANCE = "preponderance"  # Civil: 51%


@dataclass
class ChargeElement:
    """Individual element of a criminal or civil charge"""
    element_name: str
    description: str
    evidence_strength: float  # 0.0-1.0
    required: bool = True
    statute_reference: Optional[str] = None


@dataclass
class BurdenAnalysis:
    """Result of burden of proof analysis"""
    standard: BurdenStandard
    required_confidence: float
    actual_confidence: float
    meets_burden: bool
    elements_met: int
    elements_total: int
    weakest_element: Optional[ChargeElement]


class BurdenOfProofCalculator:
    """
    Calculates whether evidence meets legal burden of proof standards.
    
    Features:
    - Multiple burden standards (criminal, civil)
    - Element-by-element analysis
    - Confidence scoring
    - Weakness identification
    """
    
    # Burden thresholds
    BURDEN_THRESHOLDS = {
        BurdenStandard.BEYOND_REASONABLE_DOUBT: 0.95,
        BurdenStandard.CLEAR_AND_CONVINCING: 0.75,
        BurdenStandard.PREPONDERANCE: 0.51
    }
    
    def __init__(self):
        """Initialize burden calculator"""
        self.analyses: List[BurdenAnalysis] = []
    
    def calculate_burden(
        self,
        standard: BurdenStandard,
        elements: List[ChargeElement]
    ) -> BurdenAnalysis:
        """
        Calculate whether elements meet burden of proof.
        
        Args:
            standard: Legal burden standard to apply
            elements: List of charge elements to evaluate
        
        Returns:
            BurdenAnalysis with detailed assessment
        """
        required_confidence = self.BURDEN_THRESHOLDS[standard]
        
        # Count elements that meet threshold
        elements_met = sum(
            1 for e in elements 
            if e.required and e.evidence_strength >= required_confidence
        )
        elements_total = sum(1 for e in elements if e.required)
        
        # Calculate overall confidence (geometric mean for conservative estimate)
        if elements:
            strengths = [e.evidence_strength for e in elements if e.required]
            # Geometric mean is more conservative than arithmetic mean
            actual_confidence = (
                sum(strengths) / len(strengths)  # Simple average for now
            ) if strengths else 0.0
        else:
            actual_confidence = 0.0
        
        # Find weakest element
        weakest_element = min(
            (e for e in elements if e.required),
            key=lambda e: e.evidence_strength,
            default=None
        )
        
        # Determine if burden is met (ALL required elements must meet threshold)
        meets_burden = (
            elements_met == elements_total and
            actual_confidence >= required_confidence
        )
        
        analysis = BurdenAnalysis(
            standard=standard,
            required_confidence=required_confidence,
            actual_confidence=actual_confidence,
            meets_burden=meets_burden,
            elements_met=elements_met,
            elements_total=elements_total,
            weakest_element=weakest_element
        )
        
        self.analyses.append(analysis)
        return analysis
    
    def calculate_criminal_burden(
        self,
        elements: List[ChargeElement]
    ) -> BurdenAnalysis:
        """
        Calculate criminal burden (beyond reasonable doubt).
        
        Args:
            elements: Criminal charge elements
        
        Returns:
            BurdenAnalysis for criminal prosecution
        """
        return self.calculate_burden(
            BurdenStandard.BEYOND_REASONABLE_DOUBT,
            elements
        )
    
    def calculate_civil_fraud_burden(
        self,
        elements: List[ChargeElement]
    ) -> BurdenAnalysis:
        """
        Calculate civil fraud burden (clear and convincing).
        
        Args:
            elements: Civil fraud elements
        
        Returns:
            BurdenAnalysis for civil fraud case
        """
        return self.calculate_burden(
            BurdenStandard.CLEAR_AND_CONVINCING,
            elements
        )
    
    def calculate_civil_burden(
        self,
        elements: List[ChargeElement]
    ) -> BurdenAnalysis:
        """
        Calculate standard civil burden (preponderance).
        
        Args:
            elements: Civil charge elements
        
        Returns:
            BurdenAnalysis for civil case
        """
        return self.calculate_burden(
            BurdenStandard.PREPONDERANCE,
            elements
        )
    
    def get_prosecution_strategy(
        self,
        analysis: BurdenAnalysis
    ) -> Dict[str, any]:
        """
        Generate prosecution strategy based on burden analysis.
        
        Args:
            analysis: Burden analysis result
        
        Returns:
            Strategy recommendations
        """
        strategy = {
            'meets_burden': analysis.meets_burden,
            'confidence_gap': analysis.required_confidence - analysis.actual_confidence,
            'recommendations': []
        }
        
        if not analysis.meets_burden:
            strategy['recommendations'].append(
                "Case does not meet required burden of proof"
            )
            
            if analysis.weakest_element:
                strategy['recommendations'].append(
                    f"Strengthen evidence for: {analysis.weakest_element.element_name}"
                )
            
            if analysis.elements_met < analysis.elements_total:
                strategy['recommendations'].append(
                    f"Prove remaining {analysis.elements_total - analysis.elements_met} "
                    f"required elements"
                )
        else:
            strategy['recommendations'].append(
                "Case meets required burden of proof"
            )
            strategy['recommendations'].append(
                "Proceed with prosecution"
            )
        
        return strategy


__all__ = [
    'BurdenOfProofCalculator',
    'BurdenStandard',
    'ChargeElement',
    'BurdenAnalysis'
]

