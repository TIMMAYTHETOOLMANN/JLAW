"""
Case Evaluator - Prosecution Case Assessment
=============================================

Evaluates the overall strength and viability of prosecution cases.
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class ProsecutionDecision(Enum):
    """Prosecution decision types."""
    PROSECUTE = "prosecute"
    DECLINE = "decline"
    DEFER = "defer"
    REFER = "refer"
    SETTLEMENT = "settlement"


class CaseStrength(Enum):
    """Case strength classifications."""
    VERY_STRONG = "very_strong"
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"
    INSUFFICIENT = "insufficient"


class CaseCategory(Enum):
    """Categories of prosecution cases."""
    SECURITIES_FRAUD = "securities_fraud"
    WIRE_FRAUD = "wire_fraud"
    TAX_FRAUD = "tax_fraud"
    ACCOUNTING_FRAUD = "accounting_fraud"
    INSIDER_TRADING = "insider_trading"
    MARKET_MANIPULATION = "market_manipulation"
    BRIBERY = "bribery"
    MONEY_LAUNDERING = "money_laundering"


class CaseRisk(Enum):
    """Risk factors for prosecution."""
    STATUTE_OF_LIMITATIONS = "statute_of_limitations"
    WITNESS_RELIABILITY = "witness_reliability"
    EVIDENCE_ADMISSIBILITY = "evidence_admissibility"
    JURY_APPEAL = "jury_appeal"
    POLITICAL_SENSITIVITY = "political_sensitivity"
    RESOURCE_REQUIREMENTS = "resource_requirements"
    DEFENDANT_RESOURCES = "defendant_resources"


@dataclass
class CaseFactor:
    """A factor affecting case evaluation."""
    factor_id: str
    name: str
    score: float  # 0.0 - 1.0
    weight: float  # Weight in overall calculation
    notes: str = ""


@dataclass
class CaseRiskItem:
    """A risk item for the case."""
    risk_type: CaseRisk
    severity: float  # 0.0 - 1.0
    description: str
    mitigation: str = ""


@dataclass
class CaseEvaluation:
    """Complete case evaluation."""
    case_id: str
    target: str
    category: CaseCategory
    evaluated_at: datetime
    
    # Strength assessment
    overall_strength: CaseStrength = CaseStrength.MODERATE
    strength_score: float = 0.5
    
    # Factor analysis
    factors: List[CaseFactor] = field(default_factory=list)
    
    # Risk analysis
    risks: List[CaseRiskItem] = field(default_factory=list)
    risk_score: float = 0.0
    
    # Probability estimates
    conviction_probability: float = 0.5
    settlement_probability: float = 0.3
    dismissal_probability: float = 0.2
    
    # Resource estimates
    estimated_duration_months: int = 12
    estimated_cost: float = 0.0
    
    # Recommendations
    proceed_recommendation: bool = True
    recommendations: List[str] = field(default_factory=list)


@dataclass
class ProsecutionRecommendation:
    """Prosecution recommendation with supporting analysis."""
    recommendation: ProsecutionDecision
    confidence_score: float  # 0.0 - 1.0
    reasoning: str
    case_evaluation: Optional[CaseEvaluation] = None
    alternative_strategies: List[str] = field(default_factory=list)


class CaseEvaluator:
    """
    Prosecution Case Evaluator
    
    Comprehensively evaluates prosecution case strength and viability.
    
    Features:
    - Multi-factor strength assessment
    - Risk analysis
    - Probability estimation
    - Resource requirements
    - Go/no-go recommendations
    
    Example:
        evaluator = CaseEvaluator()
        
        # Add factors
        evaluator.add_factor("evidence_quality", 0.8, "Documentary evidence is strong")
        evaluator.add_factor("witness_strength", 0.6, "Cooperating witness available")
        
        # Add risks
        evaluator.add_risk(CaseRisk.STATUTE_OF_LIMITATIONS, 0.3, "2 years remaining")
        
        # Evaluate
        evaluation = evaluator.evaluate(
            case_id="CASE-001",
            target="Company XYZ",
            category=CaseCategory.SECURITIES_FRAUD
        )
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the case evaluator.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self._factors: Dict[str, CaseFactor] = {}
        self._risks: List[CaseRiskItem] = []
        
        # Default factor weights
        self._default_weights = {
            "evidence_quality": 0.25,
            "witness_strength": 0.15,
            "legal_theory": 0.20,
            "defendant_culpability": 0.15,
            "damages_quantification": 0.10,
            "procedural_compliance": 0.15,
        }
        
        logger.info("CaseEvaluator initialized")
    
    def add_factor(
        self,
        factor_id: str,
        score: float,
        notes: str = "",
        weight: Optional[float] = None
    ) -> CaseFactor:
        """
        Add an evaluation factor.
        
        Args:
            factor_id: Factor identifier
            score: Factor score (0.0 - 1.0)
            notes: Factor notes
            weight: Optional weight override
            
        Returns:
            Created factor
        """
        weight = weight or self._default_weights.get(factor_id, 0.1)
        
        factor = CaseFactor(
            factor_id=factor_id,
            name=factor_id.replace("_", " ").title(),
            score=min(1.0, max(0.0, score)),
            weight=weight,
            notes=notes
        )
        
        self._factors[factor_id] = factor
        return factor
    
    def add_risk(
        self,
        risk_type: CaseRisk,
        severity: float,
        description: str,
        mitigation: str = ""
    ) -> CaseRiskItem:
        """
        Add a risk factor.
        
        Args:
            risk_type: Type of risk
            severity: Severity (0.0 - 1.0)
            description: Risk description
            mitigation: Mitigation strategy
            
        Returns:
            Created risk item
        """
        risk = CaseRiskItem(
            risk_type=risk_type,
            severity=min(1.0, max(0.0, severity)),
            description=description,
            mitigation=mitigation
        )
        
        self._risks.append(risk)
        return risk
    
    def evaluate(
        self,
        case_id: str,
        target: str,
        category: CaseCategory
    ) -> CaseEvaluation:
        """
        Perform case evaluation.
        
        Args:
            case_id: Case identifier
            target: Target entity
            category: Case category
            
        Returns:
            Complete case evaluation
        """
        evaluation = CaseEvaluation(
            case_id=case_id,
            target=target,
            category=category,
            evaluated_at=datetime.now()
        )
        
        # Copy factors and risks
        evaluation.factors = list(self._factors.values())
        evaluation.risks = list(self._risks)
        
        # Calculate strength score
        evaluation.strength_score = self._calculate_strength_score()
        evaluation.overall_strength = self._classify_strength(evaluation.strength_score)
        
        # Calculate risk score
        evaluation.risk_score = self._calculate_risk_score()
        
        # Calculate probabilities
        self._calculate_probabilities(evaluation)
        
        # Estimate resources
        self._estimate_resources(evaluation)
        
        # Generate recommendations
        evaluation.recommendations = self._generate_recommendations(evaluation)
        evaluation.proceed_recommendation = self._should_proceed(evaluation)
        
        logger.info(
            f"Evaluated case {case_id}: "
            f"strength={evaluation.overall_strength.value}, "
            f"conviction_prob={evaluation.conviction_probability:.0%}"
        )
        
        return evaluation
    
    def _calculate_strength_score(self) -> float:
        """Calculate overall strength score from factors."""
        if not self._factors:
            return 0.5
        
        total_weight = sum(f.weight for f in self._factors.values())
        if total_weight == 0:
            return 0.5
        
        weighted_sum = sum(f.score * f.weight for f in self._factors.values())
        return weighted_sum / total_weight
    
    def _classify_strength(self, score: float) -> CaseStrength:
        """Classify strength score into category."""
        if score >= 0.85:
            return CaseStrength.VERY_STRONG
        elif score >= 0.70:
            return CaseStrength.STRONG
        elif score >= 0.50:
            return CaseStrength.MODERATE
        elif score >= 0.30:
            return CaseStrength.WEAK
        else:
            return CaseStrength.INSUFFICIENT
    
    def _calculate_risk_score(self) -> float:
        """Calculate overall risk score."""
        if not self._risks:
            return 0.0
        
        # Use maximum risk as the driver, with adjustment for count
        max_severity = max(r.severity for r in self._risks)
        avg_severity = sum(r.severity for r in self._risks) / len(self._risks)
        
        return 0.6 * max_severity + 0.4 * avg_severity
    
    def _calculate_probabilities(self, evaluation: CaseEvaluation) -> None:
        """Calculate outcome probabilities."""
        strength = evaluation.strength_score
        risk = evaluation.risk_score
        
        # Base conviction probability from strength
        base_conviction = strength * 0.9
        
        # Adjust for risk
        risk_adjustment = risk * 0.3
        
        evaluation.conviction_probability = max(0.0, min(1.0, base_conviction - risk_adjustment))
        
        # Settlement more likely for moderate cases
        if 0.4 <= strength <= 0.7:
            evaluation.settlement_probability = 0.4
        elif strength > 0.7:
            evaluation.settlement_probability = 0.25
        else:
            evaluation.settlement_probability = 0.2
        
        # Dismissal probability
        evaluation.dismissal_probability = max(
            0.0,
            1.0 - evaluation.conviction_probability - evaluation.settlement_probability
        )
    
    def _estimate_resources(self, evaluation: CaseEvaluation) -> None:
        """Estimate resource requirements."""
        base_months = 12
        
        # Adjust for case complexity
        if evaluation.category in [CaseCategory.SECURITIES_FRAUD, CaseCategory.MONEY_LAUNDERING]:
            base_months += 12
        
        # Adjust for case strength (weaker cases take longer)
        if evaluation.overall_strength == CaseStrength.WEAK:
            base_months += 6
        elif evaluation.overall_strength == CaseStrength.MODERATE:
            base_months += 3
        
        evaluation.estimated_duration_months = base_months
        
        # Rough cost estimate (in thousands)
        evaluation.estimated_cost = base_months * 50_000
    
    def _generate_recommendations(self, evaluation: CaseEvaluation) -> List[str]:
        """Generate recommendations based on evaluation."""
        recommendations = []
        
        # Strength-based recommendations
        if evaluation.overall_strength == CaseStrength.VERY_STRONG:
            recommendations.append("Case strength is exceptional. Proceed with confidence.")
        elif evaluation.overall_strength == CaseStrength.STRONG:
            recommendations.append("Case is strong. Recommended to proceed with prosecution.")
        elif evaluation.overall_strength == CaseStrength.MODERATE:
            recommendations.append("Case is moderate. Consider settlement or additional evidence.")
        elif evaluation.overall_strength == CaseStrength.WEAK:
            recommendations.append("Case is weak. Significant additional evidence needed.")
        else:
            recommendations.append("Case is insufficient. Do not proceed without major developments.")
        
        # Factor-specific recommendations
        for factor in evaluation.factors:
            if factor.score < 0.5:
                recommendations.append(
                    f"Address weakness in {factor.name.lower()}: {factor.notes or 'needs improvement'}"
                )
        
        # Risk-based recommendations
        high_risks = [r for r in evaluation.risks if r.severity > 0.7]
        for risk in high_risks:
            recommendations.append(
                f"High risk: {risk.description}. "
                f"Mitigation: {risk.mitigation or 'Develop mitigation strategy'}"
            )
        
        # Probability-based recommendations
        if evaluation.settlement_probability > 0.4:
            recommendations.append("Settlement may be a viable alternative.")
        
        return recommendations[:10]
    
    def _should_proceed(self, evaluation: CaseEvaluation) -> bool:
        """Determine if case should proceed."""
        # Must have at least moderate strength
        if evaluation.overall_strength in [CaseStrength.WEAK, CaseStrength.INSUFFICIENT]:
            return False
        
        # Risk must not be too high
        if evaluation.risk_score > 0.8:
            return False
        
        # Conviction probability threshold
        if evaluation.conviction_probability < 0.3:
            return False
        
        return True
    
    def reset(self) -> None:
        """Reset evaluator state."""
        self._factors.clear()
        self._risks.clear()
    
    def get_factor_summary(self) -> Dict[str, float]:
        """Get summary of factor scores."""
        return {f.factor_id: f.score for f in self._factors.values()}
    
    async def evaluate_prosecution_viability(self, forensic_case: Any) -> ProsecutionRecommendation:
        """
        Evaluate prosecution viability from forensic case.
        
        Args:
            forensic_case: ForensicCase object with investigation results
            
        Returns:
            ProsecutionRecommendation with decision and analysis
        """
        # Reset state
        self.reset()
        
        # Analyze evidence strength
        violations_count = len(forensic_case.violations_detected) if hasattr(forensic_case, 'violations_detected') else 0
        evidence_score = min(1.0, violations_count / 20.0)  # Scale to 0-1
        
        self.add_factor("evidence_quality", evidence_score, f"{violations_count} violations documented")
        
        # Analyze risk score
        risk_factor = forensic_case.risk_score if hasattr(forensic_case, 'risk_score') else 0.5
        self.add_factor("defendant_culpability", risk_factor, f"Risk score: {risk_factor}")
        
        # Legal theory strength
        self.add_factor("legal_theory", 0.8, "Securities fraud theory well-established")
        
        # Evaluate
        evaluation = self.evaluate(
            case_id=forensic_case.case_id if hasattr(forensic_case, 'case_id') else "UNKNOWN",
            target=forensic_case.target_company if hasattr(forensic_case, 'target_company') else "Unknown",
            category=CaseCategory.SECURITIES_FRAUD
        )
        
        # Generate recommendation
        if evaluation.overall_strength in [CaseStrength.VERY_STRONG, CaseStrength.STRONG]:
            decision = ProsecutionDecision.PROSECUTE
            confidence = 0.85
            reasoning = "Strong evidence of securities violations warrants prosecution"
        elif evaluation.overall_strength == CaseStrength.MODERATE:
            decision = ProsecutionDecision.SETTLEMENT
            confidence = 0.65
            reasoning = "Moderate case strength suggests settlement negotiations"
        else:
            decision = ProsecutionDecision.DEFER
            confidence = 0.40
            reasoning = "Insufficient evidence strength for immediate prosecution"
        
        return ProsecutionRecommendation(
            recommendation=decision,
            confidence_score=confidence,
            reasoning=reasoning,
            case_evaluation=evaluation
        )

    def evaluate_case_strength(
        self,
        evidence_scores: List[float],
        witness_credibilities: List[float],
        burden_met: bool,
        timeline_confidence: float,
        legal_violations: int
    ) -> Dict[str, Any]:
        """
        Evaluate case strength based on multiple factors.
        
        Args:
            evidence_scores: List of evidence reliability scores (0.0-1.0)
            witness_credibilities: List of witness credibility scores (0.0-1.0)
            burden_met: Whether burden of proof is met
            timeline_confidence: Confidence in timeline reconstruction (0.0-1.0)
            legal_violations: Number of legal violations identified
            
        Returns:
            Dictionary with overall_strength, probability_of_conviction, and recommendations
        """
        self.reset()
        
        # Calculate average scores
        avg_evidence = sum(evidence_scores) / len(evidence_scores) if evidence_scores else 0.5
        avg_witness = sum(witness_credibilities) / len(witness_credibilities) if witness_credibilities else 0.5
        
        # Add factors based on inputs
        self.add_factor("evidence_quality", avg_evidence, f"Avg evidence score: {avg_evidence:.2f}")
        self.add_factor("witness_strength", avg_witness, f"Avg witness credibility: {avg_witness:.2f}")
        self.add_factor("legal_theory", min(1.0, legal_violations / 10), f"{legal_violations} violations")
        self.add_factor("procedural_compliance", timeline_confidence, f"Timeline confidence: {timeline_confidence:.2f}")
        
        # Burden met gives a significant boost
        burden_score = 0.9 if burden_met else 0.3
        self.add_factor("defendant_culpability", burden_score, "Burden of proof met" if burden_met else "Burden not met")
        
        # Calculate strength
        strength_score = self._calculate_strength_score()
        strength = self._classify_strength(strength_score)
        
        # Calculate conviction probability
        base_prob = strength_score * 0.9
        if burden_met:
            base_prob = min(1.0, base_prob * 1.15)
        
        # Generate recommendations
        recommendations = []
        if strength == CaseStrength.VERY_STRONG:
            recommendations.append("Case strength is exceptional. Proceed with confidence.")
        elif strength == CaseStrength.STRONG:
            recommendations.append("Case is strong. Recommended to proceed with prosecution.")
        elif strength == CaseStrength.MODERATE:
            recommendations.append("Case is moderate. Consider settlement or additional evidence.")
        elif strength == CaseStrength.WEAK:
            recommendations.append("Case is weak. Significant additional evidence needed.")
        else:
            recommendations.append("Case is insufficient. Do not proceed without major developments.")
        
        if avg_evidence < 0.6:
            recommendations.append("Consider strengthening documentary evidence.")
        if avg_witness < 0.6:
            recommendations.append("Witness credibility could be improved.")
        if not burden_met:
            recommendations.append("Work to establish elements that meet burden of proof.")
        
        return {
            "overall_strength": strength.value,
            "probability_of_conviction": min(0.99, base_prob),
            "recommendations": recommendations
        }


# Alias for backward compatibility
CaseStrengthEvaluator = CaseEvaluator
