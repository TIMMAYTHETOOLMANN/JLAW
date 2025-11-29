"""
Case Strength Evaluator
========================
Multi-factor evaluation of prosecution case strength.

Evaluation factors:
- Evidence quality and quantity
- Witness credibility
- Legal precedent
- Damages/harm
- Defendant culpability
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class CaseStrength(Enum):
    """Case strength ratings"""
    EXCEPTIONAL = "exceptional"  # 90-100%
    STRONG = "strong"  # 75-89%
    MODERATE = "moderate"  # 50-74%
    WEAK = "weak"  # 25-49%
    VERY_WEAK = "very_weak"  # 0-24%


@dataclass
class EvaluationFactor:
    """Individual factor in case evaluation"""
    factor_name: str
    description: str
    score: float  # 0.0-1.0
    weight: float = 1.0
    rationale: Optional[str] = None


@dataclass
class CaseEvaluation:
    """Result of case strength evaluation"""
    overall_score: float
    strength_rating: CaseStrength
    factors: List[EvaluationFactor]
    strong_points: List[str]
    weak_points: List[str]
    success_probability: float
    recommendation: str


class CaseStrengthEvaluator:
    """
    Evaluates the overall strength of a prosecution case.
    
    Features:
    - Multi-factor weighted analysis
    - Evidence quality assessment
    - Witness credibility scoring
    - Success probability estimation
    """
    
    # Default factor weights
    DEFAULT_WEIGHTS = {
        'evidence_quality': 0.30,
        'evidence_quantity': 0.15,
        'witness_credibility': 0.20,
        'legal_precedent': 0.15,
        'damages_severity': 0.10,
        'defendant_culpability': 0.10
    }
    
    def __init__(self, weights: Optional[Dict[str, float]] = None):
        """
        Initialize case evaluator.
        
        Args:
            weights: Optional custom factor weights (must sum to 1.0)
        """
        self.weights = weights or self.DEFAULT_WEIGHTS
        self.evaluations: List[CaseEvaluation] = []
    
    def evaluate_case(
        self,
        evidence_quality: float,
        evidence_quantity: float,
        witness_credibility: float,
        legal_precedent: float,
        damages_severity: float,
        defendant_culpability: float,
        additional_factors: Optional[List[EvaluationFactor]] = None
    ) -> CaseEvaluation:
        """
        Evaluate overall case strength.
        
        Args:
            evidence_quality: Quality of evidence (0.0-1.0)
            evidence_quantity: Quantity of evidence (0.0-1.0)
            witness_credibility: Witness credibility (0.0-1.0)
            legal_precedent: Strength of legal precedent (0.0-1.0)
            damages_severity: Severity of damages (0.0-1.0)
            defendant_culpability: Defendant culpability level (0.0-1.0)
            additional_factors: Optional additional factors
        
        Returns:
            Comprehensive case evaluation
        """
        # Core factors
        factors = [
            EvaluationFactor(
                "evidence_quality",
                "Quality and reliability of evidence",
                evidence_quality,
                self.weights['evidence_quality']
            ),
            EvaluationFactor(
                "evidence_quantity",
                "Sufficiency of evidence",
                evidence_quantity,
                self.weights['evidence_quantity']
            ),
            EvaluationFactor(
                "witness_credibility",
                "Credibility of witnesses",
                witness_credibility,
                self.weights['witness_credibility']
            ),
            EvaluationFactor(
                "legal_precedent",
                "Strength of legal precedent",
                legal_precedent,
                self.weights['legal_precedent']
            ),
            EvaluationFactor(
                "damages_severity",
                "Severity of damages/harm",
                damages_severity,
                self.weights['damages_severity']
            ),
            EvaluationFactor(
                "defendant_culpability",
                "Defendant culpability level",
                defendant_culpability,
                self.weights['defendant_culpability']
            )
        ]
        
        # Add additional factors if provided
        if additional_factors:
            factors.extend(additional_factors)
        
        # Calculate weighted score
        overall_score = sum(
            factor.score * factor.weight 
            for factor in factors
        )
        
        # Normalize if weights don't sum to 1.0
        total_weight = sum(factor.weight for factor in factors)
        if total_weight != 1.0:
            overall_score = overall_score / total_weight
        
        # Determine strength rating
        strength_rating = self._calculate_strength_rating(overall_score)
        
        # Identify strong and weak points
        strong_points = [
            f"{f.factor_name}: {f.score:.2f}"
            for f in factors if f.score >= 0.75
        ]
        weak_points = [
            f"{f.factor_name}: {f.score:.2f}"
            for f in factors if f.score < 0.50
        ]
        
        # Estimate success probability
        success_probability = self._estimate_success_probability(
            overall_score,
            factors
        )
        
        # Generate recommendation
        recommendation = self._generate_recommendation(
            strength_rating,
            success_probability
        )
        
        evaluation = CaseEvaluation(
            overall_score=overall_score,
            strength_rating=strength_rating,
            factors=factors,
            strong_points=strong_points,
            weak_points=weak_points,
            success_probability=success_probability,
            recommendation=recommendation
        )
        
        self.evaluations.append(evaluation)
        return evaluation
    
    def _calculate_strength_rating(self, score: float) -> CaseStrength:
        """Convert numeric score to case strength rating"""
        if score >= 0.90:
            return CaseStrength.EXCEPTIONAL
        elif score >= 0.75:
            return CaseStrength.STRONG
        elif score >= 0.50:
            return CaseStrength.MODERATE
        elif score >= 0.25:
            return CaseStrength.WEAK
        else:
            return CaseStrength.VERY_WEAK
    
    def _estimate_success_probability(
        self,
        overall_score: float,
        factors: List[EvaluationFactor]
    ) -> float:
        """
        Estimate probability of successful prosecution.
        
        Uses a conservative model that penalizes weak factors.
        """
        # Base probability from overall score
        base_prob = overall_score
        
        # Penalty for any critically weak factors (< 0.25)
        weak_factor_penalty = sum(
            0.10 for f in factors if f.score < 0.25
        )
        
        # Bonus for consistently strong factors (all > 0.75)
        all_strong = all(f.score >= 0.75 for f in factors)
        strong_bonus = 0.10 if all_strong else 0.0
        
        # Calculate adjusted probability
        probability = max(0.0, min(1.0, 
            base_prob - weak_factor_penalty + strong_bonus
        ))
        
        return probability
    
    def _generate_recommendation(
        self,
        strength: CaseStrength,
        success_prob: float
    ) -> str:
        """Generate prosecution recommendation"""
        if strength == CaseStrength.EXCEPTIONAL:
            return "Proceed with prosecution - exceptional case strength"
        elif strength == CaseStrength.STRONG:
            return "Proceed with prosecution - strong likelihood of success"
        elif strength == CaseStrength.MODERATE:
            if success_prob >= 0.60:
                return "Proceed with caution - moderate case strength"
            else:
                return "Consider strengthening case before prosecution"
        elif strength == CaseStrength.WEAK:
            return "Do not proceed - insufficient case strength"
        else:  # VERY_WEAK
            return "Do not proceed - case unlikely to succeed"
    
    def compare_cases(
        self,
        evaluation1: CaseEvaluation,
        evaluation2: CaseEvaluation
    ) -> Dict[str, any]:
        """
        Compare two case evaluations.
        
        Args:
            evaluation1: First case evaluation
            evaluation2: Second case evaluation
        
        Returns:
            Comparison analysis
        """
        return {
            'stronger_case': 1 if evaluation1.overall_score > evaluation2.overall_score else 2,
            'score_difference': abs(evaluation1.overall_score - evaluation2.overall_score),
            'case1_score': evaluation1.overall_score,
            'case2_score': evaluation2.overall_score,
            'case1_success_prob': evaluation1.success_probability,
            'case2_success_prob': evaluation2.success_probability
        }


__all__ = [
    'CaseStrengthEvaluator',
    'CaseEvaluation',
    'CaseStrength',
    'EvaluationFactor'
]

