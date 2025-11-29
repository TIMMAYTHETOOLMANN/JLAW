"""
Case Strength Evaluator - Multi-Factor Case Assessment
======================================================

Evaluates overall case strength using multiple factors:
- Evidence reliability
- Witness credibility
- Burden of proof status
- Timeline integrity
- Legal violation count
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CaseEvaluation:
    """Case strength evaluation result"""
    overall_strength: str  # 'strong', 'moderate', 'weak'
    probability_of_conviction: float
    evidence_score: float
    witness_score: float
    burden_score: float
    timeline_score: float
    recommendations: List[str]


class CaseStrengthEvaluator:
    """
    Evaluates overall case strength for prosecution decisions
    """
    
    # Weight factors for evaluation
    WEIGHTS = {
        'evidence': 0.35,
        'witnesses': 0.25,
        'burden': 0.25,
        'timeline': 0.15
    }
    
    # Strength thresholds
    STRENGTH_THRESHOLDS = {
        'strong': 0.80,
        'moderate': 0.60,
        'weak': 0.40
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize evaluator
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        
        self.stats = {
            'evaluations_performed': 0,
            'strong_cases': 0,
            'moderate_cases': 0,
            'weak_cases': 0
        }
        
        logger.info("📊 Case Strength Evaluator initialized")
    
    def evaluate_case_strength(
        self,
        evidence_scores: List[float],
        witness_credibilities: List[float],
        burden_met: bool,
        timeline_confidence: float = 0.85,
        legal_violations: int = 1
    ) -> Dict[str, Any]:
        """
        Evaluate overall case strength
        
        Args:
            evidence_scores: List of evidence reliability scores (0-1)
            witness_credibilities: List of witness credibility scores (0-1)
            burden_met: Whether burden of proof is met
            timeline_confidence: Confidence in timeline (0-1)
            legal_violations: Number of legal violations identified
        
        Returns:
            Case evaluation dictionary
        """
        self.stats['evaluations_performed'] += 1
        
        # Calculate component scores
        evidence_score = sum(evidence_scores) / len(evidence_scores) if evidence_scores else 0.0
        witness_score = sum(witness_credibilities) / len(witness_credibilities) if witness_credibilities else 0.0
        burden_score = 1.0 if burden_met else 0.5  # Partial credit if close
        timeline_score = timeline_confidence
        
        # Calculate weighted overall score
        overall_score = (
            self.WEIGHTS['evidence'] * evidence_score +
            self.WEIGHTS['witnesses'] * witness_score +
            self.WEIGHTS['burden'] * burden_score +
            self.WEIGHTS['timeline'] * timeline_score
        )
        
        # Bonus for multiple violations
        violation_bonus = min(0.1, (legal_violations - 1) * 0.02)
        overall_score = min(1.0, overall_score + violation_bonus)
        
        # Determine strength category
        if overall_score >= self.STRENGTH_THRESHOLDS['strong']:
            strength = 'strong'
            self.stats['strong_cases'] += 1
        elif overall_score >= self.STRENGTH_THRESHOLDS['moderate']:
            strength = 'moderate'
            self.stats['moderate_cases'] += 1
        else:
            strength = 'weak'
            self.stats['weak_cases'] += 1
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            evidence_score, witness_score, burden_met, timeline_score, strength
        )
        
        return {
            'overall_strength': strength,
            'probability_of_conviction': overall_score,
            'evidence_score': evidence_score,
            'witness_score': witness_score,
            'burden_score': burden_score,
            'timeline_score': timeline_score,
            'recommendations': recommendations
        }
    
    def _generate_recommendations(
        self,
        evidence_score: float,
        witness_score: float,
        burden_met: bool,
        timeline_score: float,
        strength: str
    ) -> List[str]:
        """Generate case improvement recommendations"""
        recommendations = []
        
        if evidence_score < 0.7:
            recommendations.append("Gather additional corroborating evidence to strengthen case")
        
        if witness_score < 0.6:
            recommendations.append("Consider deposing additional witnesses or expert witnesses")
        
        if not burden_met:
            recommendations.append("Focus on meeting all elements of burden of proof")
        
        if timeline_score < 0.8:
            recommendations.append("Verify and strengthen timeline with additional documentation")
        
        if strength == 'strong':
            recommendations.append("Case is prosecution-ready; proceed with charges")
        elif strength == 'moderate':
            recommendations.append("Consider additional investigation before prosecution")
        else:
            recommendations.append("Case may benefit from plea negotiation or further investigation")
        
        return recommendations
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get evaluator statistics"""
        return self.stats.copy()


if __name__ == "__main__":
    # Demo usage
    evaluator = CaseStrengthEvaluator()
    
    result = evaluator.evaluate_case_strength(
        evidence_scores=[0.9, 0.85, 0.95, 0.88],
        witness_credibilities=[0.8, 0.75, 0.9],
        burden_met=True,
        timeline_confidence=0.92,
        legal_violations=3
    )
    
    print(f"Strength: {result['overall_strength']}")
    print(f"Conviction Probability: {result['probability_of_conviction']:.1%}")
    print(f"Recommendations: {result['recommendations']}")
