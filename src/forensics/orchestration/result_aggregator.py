"""
Result Aggregator - Cross-Phase Data Correlation
=================================================

Aggregates and correlates results from all investigation phases
to produce comprehensive analysis summaries.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import statistics

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk level classifications."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MINIMAL = "minimal"


class CaseStrength(Enum):
    """Case strength classifications."""
    VERY_STRONG = "very_strong"
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"
    INSUFFICIENT = "insufficient"


@dataclass
class PhaseContribution:
    """Contribution of a phase to overall findings."""
    phase_name: str
    findings_count: int
    violations_count: int
    risk_contribution: float
    key_findings: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AggregatedFindings:
    """Aggregated findings from all phases."""
    total_findings: int = 0
    total_violations: int = 0
    high_priority_findings: List[Dict[str, Any]] = field(default_factory=list)
    violations_by_type: Dict[str, int] = field(default_factory=dict)
    violations_by_severity: Dict[str, int] = field(default_factory=dict)
    cross_phase_correlations: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class RiskAssessment:
    """Comprehensive risk assessment."""
    overall_risk: RiskLevel
    risk_score: float
    risk_factors: List[Dict[str, Any]] = field(default_factory=list)
    mitigating_factors: List[str] = field(default_factory=list)
    risk_by_category: Dict[str, float] = field(default_factory=dict)


@dataclass
class ProsecutionAssessment:
    """Assessment of prosecution viability."""
    case_strength: CaseStrength
    conviction_probability: float
    recommended_actions: List[str] = field(default_factory=list)
    evidence_gaps: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)


@dataclass
class AggregatedResult:
    """Complete aggregated investigation result."""
    case_id: str
    target: str
    aggregated_at: datetime
    
    # Phase contributions
    phase_contributions: Dict[str, PhaseContribution] = field(default_factory=dict)
    
    # Findings
    findings: AggregatedFindings = field(default_factory=AggregatedFindings)
    
    # Assessments
    risk_assessment: Optional[RiskAssessment] = None
    prosecution_assessment: Optional[ProsecutionAssessment] = None
    
    # Summary metrics
    summary_metrics: Dict[str, Any] = field(default_factory=dict)
    
    # Recommendations
    recommendations: List[str] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "case_id": self.case_id,
            "target": self.target,
            "aggregated_at": self.aggregated_at.isoformat(),
            "findings": {
                "total_findings": self.findings.total_findings,
                "total_violations": self.findings.total_violations,
                "high_priority_count": len(self.findings.high_priority_findings),
                "violations_by_type": self.findings.violations_by_type,
                "correlations_found": len(self.findings.cross_phase_correlations)
            },
            "risk_assessment": {
                "overall_risk": self.risk_assessment.overall_risk.value if self.risk_assessment else None,
                "risk_score": self.risk_assessment.risk_score if self.risk_assessment else 0.0
            },
            "prosecution_assessment": {
                "case_strength": self.prosecution_assessment.case_strength.value if self.prosecution_assessment else None,
                "conviction_probability": self.prosecution_assessment.conviction_probability if self.prosecution_assessment else 0.0
            },
            "summary_metrics": self.summary_metrics,
            "recommendations": self.recommendations,
            "next_steps": self.next_steps
        }


class ResultAggregator:
    """
    Cross-Phase Result Aggregator
    
    Aggregates results from all investigation phases to produce
    comprehensive analysis summaries and correlations.
    
    Features:
    - Phase result aggregation
    - Cross-phase correlation detection
    - Risk scoring
    - Prosecution viability assessment
    - Recommendation generation
    
    Example:
        aggregator = ResultAggregator()
        
        # Add phase results
        aggregator.add_phase_result("document_parsing", doc_results)
        aggregator.add_phase_result("contradiction_detection", contradict_results)
        
        # Generate aggregated result
        result = aggregator.aggregate("CASE-001", "Company XYZ")
    """
    
    def __init__(self):
        """Initialize the Result Aggregator."""
        self._phase_results: Dict[str, Dict[str, Any]] = {}
        self._phase_weights = {
            "document_parsing": 0.10,
            "intelligence_gathering": 0.15,
            "legal_correlation": 0.20,
            "temporal_analysis": 0.15,
            "prosecution_path": 0.20,
            "contradiction_detection": 0.20
        }
        
        logger.info("ResultAggregator initialized")
    
    def add_phase_result(
        self,
        phase_name: str,
        results: Dict[str, Any]
    ) -> None:
        """
        Add results from a phase.
        
        Args:
            phase_name: Phase name
            results: Phase results dictionary
        """
        self._phase_results[phase_name] = results
        logger.debug(f"Added results for phase: {phase_name}")
    
    def clear(self) -> None:
        """Clear all phase results."""
        self._phase_results.clear()
    
    def aggregate(
        self,
        case_id: str,
        target: str
    ) -> AggregatedResult:
        """
        Aggregate all phase results.
        
        Args:
            case_id: Case identifier
            target: Investigation target
            
        Returns:
            Aggregated investigation result
        """
        logger.info(f"Aggregating results for case {case_id}")
        
        result = AggregatedResult(
            case_id=case_id,
            target=target,
            aggregated_at=datetime.now()
        )
        
        # Process each phase
        for phase_name, phase_results in self._phase_results.items():
            contribution = self._process_phase_results(phase_name, phase_results)
            result.phase_contributions[phase_name] = contribution
        
        # Aggregate findings
        result.findings = self._aggregate_findings()
        
        # Perform cross-phase correlation
        result.findings.cross_phase_correlations = self._detect_correlations()
        
        # Assess risk
        result.risk_assessment = self._assess_risk()
        
        # Assess prosecution viability
        result.prosecution_assessment = self._assess_prosecution()
        
        # Calculate summary metrics
        result.summary_metrics = self._calculate_summary_metrics(result)
        
        # Generate recommendations
        result.recommendations = self._generate_recommendations(result)
        result.next_steps = self._generate_next_steps(result)
        
        logger.info(f"Aggregation complete for case {case_id}")
        return result
    
    def _process_phase_results(
        self,
        phase_name: str,
        results: Dict[str, Any]
    ) -> PhaseContribution:
        """Process results from a single phase."""
        contribution = PhaseContribution(
            phase_name=phase_name,
            findings_count=0,
            violations_count=0,
            risk_contribution=0.0
        )
        
        # Extract findings count
        if "findings" in results:
            contribution.findings_count = len(results["findings"])
        elif "documents_processed" in results:
            contribution.findings_count = results.get("entities_extracted", 0)
        
        # Extract violations
        if "violations" in results:
            contribution.violations_count = len(results["violations"])
        elif "potential_violations" in results:
            contribution.violations_count = results["potential_violations"]
        elif "contradictions_detected" in results:
            contribution.violations_count = results["contradictions_detected"]
        
        # Calculate risk contribution
        weight = self._phase_weights.get(phase_name, 0.1)
        contribution.risk_contribution = weight * (
            contribution.violations_count * 0.1 + 
            contribution.findings_count * 0.05
        )
        
        # Store all metrics
        contribution.metrics = results
        
        return contribution
    
    def _aggregate_findings(self) -> AggregatedFindings:
        """Aggregate findings from all phases."""
        findings = AggregatedFindings(
            total_findings=0,
            total_violations=0
        )
        
        for phase_name, phase_results in self._phase_results.items():
            # Count findings
            if "findings" in phase_results:
                findings.total_findings += len(phase_results["findings"])
            elif "entities_extracted" in phase_results:
                findings.total_findings += phase_results["entities_extracted"]
            
            # Count violations
            if "violations" in phase_results:
                violations = phase_results["violations"]
                findings.total_violations += len(violations)
                
                # Categorize by type
                for v in violations:
                    v_type = v.get("type", "unknown")
                    findings.violations_by_type[v_type] = \
                        findings.violations_by_type.get(v_type, 0) + 1
                    
                    severity = v.get("severity", "medium")
                    findings.violations_by_severity[severity] = \
                        findings.violations_by_severity.get(severity, 0) + 1
            
            elif "potential_violations" in phase_results:
                findings.total_violations += phase_results["potential_violations"]
            
            elif "contradictions_detected" in phase_results:
                count = phase_results["contradictions_detected"]
                findings.total_violations += count
                findings.violations_by_type["contradiction"] = count
            
            # Track high priority findings
            if "high_severity_contradictions" in phase_results:
                findings.high_priority_findings.append({
                    "phase": phase_name,
                    "type": "contradictions",
                    "count": phase_results["high_severity_contradictions"]
                })
        
        return findings
    
    def _detect_correlations(self) -> List[Dict[str, Any]]:
        """Detect cross-phase correlations."""
        correlations = []
        
        # Check document-contradiction correlation
        doc_results = self._phase_results.get("document_parsing", {})
        contradict_results = self._phase_results.get("contradiction_detection", {})
        
        if doc_results and contradict_results:
            docs = doc_results.get("documents_processed", 0)
            contradictions = contradict_results.get("contradictions_detected", 0)
            
            if docs > 0 and contradictions > 0:
                ratio = contradictions / docs
                correlations.append({
                    "type": "document_contradiction_ratio",
                    "phases": ["document_parsing", "contradiction_detection"],
                    "value": ratio,
                    "significance": "high" if ratio > 0.5 else "medium"
                })
        
        # Check temporal-legal correlation
        temporal_results = self._phase_results.get("temporal_analysis", {})
        legal_results = self._phase_results.get("legal_correlation", {})
        
        if temporal_results and legal_results:
            temporal_contradictions = temporal_results.get("temporal_contradictions", 0)
            legal_violations = legal_results.get("potential_violations", 0)
            
            if temporal_contradictions > 0 and legal_violations > 0:
                correlations.append({
                    "type": "temporal_legal_overlap",
                    "phases": ["temporal_analysis", "legal_correlation"],
                    "temporal_issues": temporal_contradictions,
                    "legal_violations": legal_violations,
                    "significance": "high" if temporal_contradictions >= legal_violations else "medium"
                })
        
        return correlations
    
    def _assess_risk(self) -> RiskAssessment:
        """Assess overall risk level."""
        risk_factors = []
        risk_scores = []
        
        # Evaluate each phase's risk contribution
        for phase_name, results in self._phase_results.items():
            phase_risk = 0.0
            
            if "contradictions_detected" in results:
                count = results["contradictions_detected"]
                if count > 5:
                    phase_risk = 0.8
                    risk_factors.append({
                        "phase": phase_name,
                        "factor": "high_contradiction_count",
                        "count": count,
                        "severity": "high"
                    })
                elif count > 2:
                    phase_risk = 0.5
                    risk_factors.append({
                        "phase": phase_name,
                        "factor": "moderate_contradiction_count",
                        "count": count,
                        "severity": "medium"
                    })
            
            if "potential_violations" in results:
                count = results["potential_violations"]
                if count > 3:
                    phase_risk = max(phase_risk, 0.9)
                    risk_factors.append({
                        "phase": phase_name,
                        "factor": "multiple_violations",
                        "count": count,
                        "severity": "high"
                    })
            
            if "success_probability" in results:
                prob = results["success_probability"]
                if prob > 0.7:
                    phase_risk = max(phase_risk, 0.7)
            
            if phase_risk > 0:
                weight = self._phase_weights.get(phase_name, 0.1)
                risk_scores.append(phase_risk * weight)
        
        # Calculate overall risk score
        risk_score = sum(risk_scores) / max(sum(self._phase_weights.values()), 1.0)
        risk_score = min(1.0, risk_score * 1.5)  # Scale up
        
        # Determine risk level
        if risk_score >= 0.8:
            overall_risk = RiskLevel.CRITICAL
        elif risk_score >= 0.6:
            overall_risk = RiskLevel.HIGH
        elif risk_score >= 0.4:
            overall_risk = RiskLevel.MEDIUM
        elif risk_score >= 0.2:
            overall_risk = RiskLevel.LOW
        else:
            overall_risk = RiskLevel.MINIMAL
        
        return RiskAssessment(
            overall_risk=overall_risk,
            risk_score=risk_score,
            risk_factors=risk_factors
        )
    
    def _assess_prosecution(self) -> ProsecutionAssessment:
        """Assess prosecution viability."""
        strengths = []
        weaknesses = []
        evidence_gaps = []
        
        # Check prosecution path results
        prosecution_results = self._phase_results.get("prosecution_path", {})
        
        conviction_probability = prosecution_results.get("success_probability", 0.5)
        
        # Evaluate evidence
        legal_results = self._phase_results.get("legal_correlation", {})
        if legal_results:
            violations = legal_results.get("potential_violations", 0)
            if violations > 0:
                strengths.append(f"Identified {violations} potential legal violations")
            else:
                evidence_gaps.append("No clear legal violations identified")
        
        # Evaluate contradictions as evidence
        contradict_results = self._phase_results.get("contradiction_detection", {})
        if contradict_results:
            contradictions = contradict_results.get("contradictions_detected", 0)
            high_severity = contradict_results.get("high_severity_contradictions", 0)
            
            if high_severity > 0:
                strengths.append(f"{high_severity} high-severity contradictions found")
            if contradictions > 0:
                strengths.append(f"Total of {contradictions} contradictions detected")
        
        # Evaluate temporal evidence
        temporal_results = self._phase_results.get("temporal_analysis", {})
        if temporal_results:
            causal_chains = temporal_results.get("causal_chains_identified", 0)
            if causal_chains > 0:
                strengths.append(f"{causal_chains} causal chains established")
        
        # Determine case strength
        if conviction_probability >= 0.8:
            case_strength = CaseStrength.VERY_STRONG
        elif conviction_probability >= 0.65:
            case_strength = CaseStrength.STRONG
        elif conviction_probability >= 0.5:
            case_strength = CaseStrength.MODERATE
        elif conviction_probability >= 0.35:
            case_strength = CaseStrength.WEAK
        else:
            case_strength = CaseStrength.INSUFFICIENT
        
        # Generate recommended actions
        recommended_actions = []
        if conviction_probability >= 0.7:
            recommended_actions.append("Proceed with DOJ criminal referral")
            recommended_actions.append("Prepare SEC enforcement action")
        elif conviction_probability >= 0.5:
            recommended_actions.append("Consider SEC civil action")
            recommended_actions.append("Gather additional evidence")
        else:
            recommended_actions.append("Further investigation required")
            recommended_actions.append("Focus on evidence gaps")
        
        return ProsecutionAssessment(
            case_strength=case_strength,
            conviction_probability=conviction_probability,
            recommended_actions=recommended_actions,
            evidence_gaps=evidence_gaps,
            strengths=strengths,
            weaknesses=weaknesses
        )
    
    def _calculate_summary_metrics(
        self,
        result: AggregatedResult
    ) -> Dict[str, Any]:
        """Calculate summary metrics."""
        return {
            "total_phases_analyzed": len(self._phase_results),
            "total_findings": result.findings.total_findings,
            "total_violations": result.findings.total_violations,
            "cross_phase_correlations": len(result.findings.cross_phase_correlations),
            "risk_level": result.risk_assessment.overall_risk.value if result.risk_assessment else None,
            "risk_score": result.risk_assessment.risk_score if result.risk_assessment else 0.0,
            "case_strength": result.prosecution_assessment.case_strength.value if result.prosecution_assessment else None,
            "conviction_probability": result.prosecution_assessment.conviction_probability if result.prosecution_assessment else 0.0
        }
    
    def _generate_recommendations(
        self,
        result: AggregatedResult
    ) -> List[str]:
        """Generate recommendations based on aggregated results."""
        recommendations = []
        
        if result.risk_assessment:
            if result.risk_assessment.overall_risk in [RiskLevel.CRITICAL, RiskLevel.HIGH]:
                recommendations.append("Immediate escalation recommended due to high risk level")
            
            if len(result.risk_assessment.risk_factors) > 3:
                recommendations.append("Multiple risk factors identified - comprehensive review needed")
        
        if result.prosecution_assessment:
            if result.prosecution_assessment.case_strength == CaseStrength.VERY_STRONG:
                recommendations.append("Case ready for prosecution - strong evidence base")
            elif result.prosecution_assessment.case_strength == CaseStrength.WEAK:
                recommendations.append("Additional evidence gathering recommended before proceeding")
            
            recommendations.extend(result.prosecution_assessment.recommended_actions)
        
        return recommendations[:10]  # Limit to top 10 recommendations
    
    def _generate_next_steps(
        self,
        result: AggregatedResult
    ) -> List[str]:
        """Generate next steps based on aggregated results."""
        next_steps = []
        
        # Based on findings
        if result.findings.total_violations > 0:
            next_steps.append("Review identified violations with legal team")
        
        if result.findings.cross_phase_correlations:
            next_steps.append("Investigate cross-phase correlations")
        
        # Based on prosecution assessment
        if result.prosecution_assessment:
            if result.prosecution_assessment.evidence_gaps:
                next_steps.append("Address evidence gaps: " + 
                    ", ".join(result.prosecution_assessment.evidence_gaps[:3]))
        
        # Standard steps
        next_steps.append("Generate comprehensive report for stakeholders")
        next_steps.append("Archive evidence with chain of custody documentation")
        
        return next_steps[:7]  # Limit to top 7 steps
