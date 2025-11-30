"""
Burden Calculator - Legal Burden of Proof Analysis
===================================================

Calculates burden of proof requirements for prosecution strategies.
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class BurdenStandard(Enum):
    """Legal burden of proof standards."""
    BEYOND_REASONABLE_DOUBT = "beyond_reasonable_doubt"  # Criminal
    CLEAR_AND_CONVINCING = "clear_and_convincing"  # Civil (heightened)
    PREPONDERANCE_OF_EVIDENCE = "preponderance_of_evidence"  # Civil
    PROBABLE_CAUSE = "probable_cause"  # Investigative
    REASONABLE_SUSPICION = "reasonable_suspicion"  # Initial


class EvidenceCategory(Enum):
    """Categories of evidence."""
    DOCUMENTARY = "documentary"
    TESTIMONIAL = "testimonial"
    PHYSICAL = "physical"
    DIGITAL = "digital"
    CIRCUMSTANTIAL = "circumstantial"
    EXPERT = "expert"


@dataclass
class EvidenceItem:
    """A piece of evidence for burden calculation."""
    evidence_id: str
    category: EvidenceCategory
    description: str
    strength: float  # 0.0 - 1.0
    reliability: float  # 0.0 - 1.0
    relevance: float  # 0.0 - 1.0
    corroborating_items: List[str] = field(default_factory=list)


@dataclass
class BurdenElement:
    """An element that must be proven."""
    element_id: str
    description: str
    required: bool = True
    evidence_items: List[str] = field(default_factory=list)
    current_strength: float = 0.0
    threshold: float = 0.5


@dataclass
class BurdenAnalysis:
    """Complete burden of proof analysis."""
    case_id: str
    standard: BurdenStandard
    elements: List[BurdenElement] = field(default_factory=list)
    overall_burden_met: bool = False
    overall_strength: float = 0.0
    weak_elements: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


# Alias for compatibility
ProofBurden = BurdenAnalysis


class BurdenCalculator:
    """
    Burden of Proof Calculator
    
    Analyzes evidence against legal burden of proof standards.
    
    Features:
    - Multiple burden standards
    - Element-by-element analysis
    - Evidence strength calculation
    - Gap identification
    
    Example:
        calculator = BurdenCalculator()
        
        # Set case elements
        calculator.add_element("scienter", "Defendant acted with intent")
        calculator.add_element("materiality", "Misstatement was material")
        
        # Add evidence
        calculator.add_evidence(evidence_item, ["scienter"])
        
        # Calculate burden
        analysis = calculator.calculate_burden(
            "CASE-001",
            BurdenStandard.BEYOND_REASONABLE_DOUBT
        )
    """
    
    def __init__(self):
        """Initialize the burden calculator."""
        self._evidence: Dict[str, EvidenceItem] = {}
        self._elements: Dict[str, BurdenElement] = {}
        
        # Threshold requirements for each standard
        self._thresholds = {
            BurdenStandard.BEYOND_REASONABLE_DOUBT: 0.95,
            BurdenStandard.CLEAR_AND_CONVINCING: 0.75,
            BurdenStandard.PREPONDERANCE_OF_EVIDENCE: 0.51,
            BurdenStandard.PROBABLE_CAUSE: 0.40,
            BurdenStandard.REASONABLE_SUSPICION: 0.25,
        }
        
        logger.info("BurdenCalculator initialized")
    
    def add_element(
        self,
        element_id: str,
        description: str,
        required: bool = True
    ) -> BurdenElement:
        """
        Add an element that must be proven.
        
        Args:
            element_id: Element identifier
            description: Element description
            required: Whether element is required
            
        Returns:
            Created element
        """
        element = BurdenElement(
            element_id=element_id,
            description=description,
            required=required
        )
        
        self._elements[element_id] = element
        return element
    
    def add_evidence(
        self,
        evidence: EvidenceItem,
        element_ids: List[str]
    ) -> None:
        """
        Add evidence linked to elements.
        
        Args:
            evidence: Evidence item
            element_ids: List of element IDs this evidence supports
        """
        self._evidence[evidence.evidence_id] = evidence
        
        for element_id in element_ids:
            if element_id in self._elements:
                self._elements[element_id].evidence_items.append(evidence.evidence_id)
    
    def calculate_burden_analysis(
        self,
        case_id: str,
        standard: BurdenStandard
    ) -> BurdenAnalysis:
        """
        Calculate burden of proof analysis.
        
        Args:
            case_id: Case identifier
            standard: Burden of proof standard
            
        Returns:
            Burden analysis
        """
        threshold = self._thresholds[standard]
        
        analysis = BurdenAnalysis(
            case_id=case_id,
            standard=standard
        )
        
        element_strengths = []
        
        for element_id, element in self._elements.items():
            element.threshold = threshold
            element.current_strength = self._calculate_element_strength(element)
            
            analysis.elements.append(element)
            element_strengths.append(element.current_strength)
            
            if element.required and element.current_strength < threshold:
                analysis.weak_elements.append(element_id)
        
        # Calculate overall strength
        if element_strengths:
            analysis.overall_strength = min(element_strengths)  # Weakest link
        
        # Determine if burden is met
        analysis.overall_burden_met = (
            analysis.overall_strength >= threshold and
            len(analysis.weak_elements) == 0
        )
        
        # Generate recommendations
        analysis.recommendations = self._generate_recommendations(analysis, threshold)
        
        logger.info(f"Calculated burden for case {case_id}: {analysis.overall_strength:.2f}")
        return analysis
    
    def _calculate_element_strength(self, element: BurdenElement) -> float:
        """Calculate strength of evidence for an element."""
        if not element.evidence_items:
            return 0.0
        
        strengths = []
        
        for evidence_id in element.evidence_items:
            evidence = self._evidence.get(evidence_id)
            if not evidence:
                continue
            
            # Calculate evidence score
            score = (
                evidence.strength * 0.4 +
                evidence.reliability * 0.3 +
                evidence.relevance * 0.3
            )
            
            # Boost for corroboration
            if evidence.corroborating_items:
                corroboration_count = len(evidence.corroborating_items)
                corroboration_boost = min(0.2, corroboration_count * 0.05)
                score = min(1.0, score + corroboration_boost)
            
            strengths.append(score)
        
        if not strengths:
            return 0.0
        
        # Use weighted average with emphasis on strongest evidence
        strengths.sort(reverse=True)
        
        # Primary evidence (strongest) counts more
        if len(strengths) == 1:
            return strengths[0]
        
        primary_weight = 0.6
        secondary_weight = 0.4 / (len(strengths) - 1)
        
        total = strengths[0] * primary_weight
        for s in strengths[1:]:
            total += s * secondary_weight
        
        return min(1.0, total)
    
    def _generate_recommendations(
        self,
        analysis: BurdenAnalysis,
        threshold: float
    ) -> List[str]:
        """Generate recommendations based on analysis."""
        recommendations = []
        
        if analysis.overall_burden_met:
            recommendations.append("Burden of proof appears to be met for all elements.")
            recommendations.append("Consider proceeding with prosecution strategy.")
        else:
            recommendations.append("Burden of proof not currently met.")
            
            for weak_element_id in analysis.weak_elements:
                element = self._elements.get(weak_element_id)
                if element:
                    gap = threshold - element.current_strength
                    recommendations.append(
                        f"Element '{weak_element_id}' needs additional evidence. "
                        f"Current: {element.current_strength:.0%}, Required: {threshold:.0%}, "
                        f"Gap: {gap:.0%}"
                    )
        
        # Evidence category recommendations
        categories_used = set()
        for evidence in self._evidence.values():
            categories_used.add(evidence.category)
        
        if EvidenceCategory.EXPERT not in categories_used:
            recommendations.append("Consider obtaining expert testimony to strengthen case.")
        
        if EvidenceCategory.DOCUMENTARY not in categories_used:
            recommendations.append("Seek additional documentary evidence.")
        
        return recommendations
    
    def get_standard_threshold(self, standard: BurdenStandard) -> float:
        """Get threshold for a burden standard."""
        return self._thresholds.get(standard, 0.5)
    
    def reset(self) -> None:
        """Reset calculator state."""
        self._evidence.clear()
        self._elements.clear()
    
    def get_element_summary(self) -> Dict[str, Dict[str, Any]]:
        """Get summary of all elements."""
        return {
            element_id: {
                "description": element.description,
                "required": element.required,
                "evidence_count": len(element.evidence_items),
                "current_strength": element.current_strength
            }
            for element_id, element in self._elements.items()
        }
    
    async def calculate_burden(
        self,
        violations: List[Any],
        evidence_catalog: List[Any]
    ) -> ProofBurden:
        """
        Calculate burden of proof from violations and evidence.
        
        Args:
            violations: List of violations detected
            evidence_catalog: List of evidence items
            
        Returns:
            ProofBurden analysis
        """
        # Reset state
        self.reset()
        
        # Define criminal elements for securities fraud
        self.add_element("materiality", "Material misstatement or omission", required=True)
        self.add_element("scienter", "Intent to deceive or knowledge of falsity", required=True)
        self.add_element("reliance", "Investor reliance on misstatements", required=True)
        self.add_element("damages", "Quantifiable investor damages", required=True)
        
        # Add evidence from catalog
        for i, evidence_item in enumerate(evidence_catalog):
            evidence = EvidenceItem(
                evidence_id=f"EV-{i:03d}",
                category=EvidenceCategory.DOCUMENTARY,
                description=str(evidence_item),
                strength=0.8,
                reliability=0.85,
                relevance=0.9
            )
            
            # Link to elements
            self.add_evidence(evidence, ["materiality", "damages"])
        
        # Calculate burden analysis (call synchronous method)
        analysis = self.calculate_burden_analysis(
            case_id="DOJ-CASE",
            standard=BurdenStandard.BEYOND_REASONABLE_DOUBT
        )
        
        return analysis
