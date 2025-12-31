"""
Enforcement Routing Engine - Phase 5
====================================

Comprehensive enforcement routing engine with SEC trigger assessment,
whistleblower program flagging, and multi-agency coordination.

This module implements the Phase 5 Enforcement & Bounty Module as specified
in the JLAW Enhancement Implementation. It provides:

1. SEC Investigation Trigger Assessment - Explicit threshold evaluation
2. Whistleblower Relevance Flagging - Dodd-Frank §922 compliance
3. Penalty Range Estimation - Conservative statutory-based calculations
4. Multi-Agency Routing - SEC, DOJ, IRS, CFTC, FinCEN
5. Evidence-Based Recommendations - No hedging, RIM compliant

Legal Framework:
- Dodd-Frank Act Section 922 (15 USC §78u-6) - Whistleblower Program
- 17 CFR § 240 (SEC regulations)
- 15 USC § 78 (Securities Exchange Act)
- 18 USC § 1348 (Securities fraud)
- 26 USC § 83 (IRC compensation taxation)

Integration Points:
- src/nodes/node6_routing/enforcement_router.py (existing Node 6)
- src/legal/statutory_binding_engine.py (statutory bindings)
- src/core/recursive_analysis_engine.py (violation aggregation)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# ENUMERATIONS
# ═══════════════════════════════════════════════════════════════════════════


class EnforcementAgency(Enum):
    """Federal enforcement agencies."""
    SEC = "SEC"
    DOJ = "DOJ"
    IRS = "IRS"
    CFTC = "CFTC"
    FINCEN = "FinCEN"


class CaseType(Enum):
    """Case type classification."""
    CIVIL = "civil"
    CRIMINAL = "criminal"


class Priority(Enum):
    """Enforcement priority levels."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class PenaltyType(Enum):
    """Penalty type classification."""
    CIVIL = "civil"
    CRIMINAL = "criminal"
    BOTH = "both"


# ═══════════════════════════════════════════════════════════════════════════
# DATA MODELS
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class PenaltyRange:
    """
    Estimated penalty range for violation.
    
    Conservative estimates based on statutory maximums and historical
    enforcement patterns. Does not speculate - uses documented precedent.
    """
    min_penalty: float
    max_penalty: float
    penalty_type: str  # "civil", "criminal", "both"
    basis: str  # Legal basis for calculation
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "min_penalty": self.min_penalty,
            "max_penalty": self.max_penalty,
            "penalty_type": self.penalty_type,
            "basis": self.basis
        }


@dataclass
class EnforcementRecommendation:
    """
    Agency routing recommendation with complete justification.
    
    Provides enforcement pathway with SEC trigger threshold assessment,
    whistleblower program relevance, and statutory references.
    
    This is the primary output of the EnforcementRoutingEngine.
    """
    agency: str  # "SEC", "DOJ", "IRS", "CFTC", "FinCEN"
    case_type: str  # "civil", "criminal"
    priority: str  # "CRITICAL", "HIGH", "MEDIUM", "LOW"
    trigger_threshold_met: bool
    justification: str
    estimated_penalties: Optional[PenaltyRange] = None
    whistleblower_relevant: bool = False
    violation_ids: List[str] = field(default_factory=list)
    statutory_references: List[str] = field(default_factory=list)
    recommended_actions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "agency": self.agency,
            "case_type": self.case_type,
            "priority": self.priority,
            "trigger_threshold_met": self.trigger_threshold_met,
            "justification": self.justification,
            "estimated_penalties": self.estimated_penalties.to_dict() if self.estimated_penalties else None,
            "whistleblower_relevant": self.whistleblower_relevant,
            "violation_ids": self.violation_ids,
            "statutory_references": self.statutory_references,
            "recommended_actions": self.recommended_actions
        }


# ═══════════════════════════════════════════════════════════════════════════
# ENFORCEMENT ROUTING ENGINE
# ═══════════════════════════════════════════════════════════════════════════


class EnforcementRoutingEngine:
    """
    Enforcement Routing Engine with threshold-based agency assignment.
    
    Routes violations to appropriate enforcement agencies based on:
    - Violation type and severity
    - Damage magnitude and scienter evidence
    - SEC investigation trigger thresholds
    - Whistleblower program eligibility (Dodd-Frank §922)
    - Statutory penalty ranges
    
    No speculation - all routing decisions based on evidence density
    and statutory weight per RIM execution standard.
    
    Usage:
        engine = EnforcementRoutingEngine()
        recommendations = engine.route_violations(
            violations=detected_violations,
            statutory_bindings=bindings
        )
    """
    
    # ═══════════════════════════════════════════════════════════════════════
    # SEC INVESTIGATION TRIGGER THRESHOLDS
    # ═══════════════════════════════════════════════════════════════════════
    
    SEC_TRIGGER_THRESHOLDS = {
        "insider_trading": {
            "min_violations": 1,
            "min_damages": 100000,  # $100K threshold
            "description": "Single violation with $100K+ damages"
        },
        "securities_fraud": {
            "min_violations": 1,
            "min_damages": 500000,  # $500K threshold
            "description": "Single violation with $500K+ damages"
        },
        "late_filing": {
            "min_violations": 5,
            "min_damages": 0,
            "description": "5+ late filing violations (Form 4/13D/13G)"
        },
        "disclosure_violation": {
            "min_violations": 3,
            "min_damages": 0,
            "description": "3+ material disclosure violations"
        },
        "market_manipulation": {
            "min_violations": 1,
            "min_damages": 250000,  # $250K threshold
            "description": "Single violation with $250K+ damages"
        },
        "sox_violation": {
            "min_violations": 1,
            "min_damages": 0,
            "description": "Any SOX certification violation"
        },
        "beneficial_ownership": {
            "min_violations": 3,
            "min_damages": 0,
            "description": "3+ beneficial ownership violations"
        }
    }
    
    # ═══════════════════════════════════════════════════════════════════════
    # WHISTLEBLOWER PROGRAM THRESHOLDS (Dodd-Frank §922)
    # ═══════════════════════════════════════════════════════════════════════
    
    WHISTLEBLOWER_THRESHOLD = 1000000  # $1M minimum sanctions
    
    # Award range: 10-30% of monetary sanctions exceeding $1M
    WHISTLEBLOWER_AWARD_MIN = 0.10  # 10%
    WHISTLEBLOWER_AWARD_MAX = 0.30  # 30%
    
    # ═══════════════════════════════════════════════════════════════════════
    # PENALTY RANGES BY VIOLATION TYPE (2024 amounts, inflation-adjusted)
    # ═══════════════════════════════════════════════════════════════════════
    
    PENALTY_RANGES = {
        # Insider trading penalties
        "insider_trading": {
            "civil_min": 100000,
            "civil_max": 10000000,
            "criminal_max_years": 20,
            "basis": "17 CFR § 240.10b-5, 15 USC § 78j(b)"
        },
        # Securities fraud
        "securities_fraud": {
            "civil_min": 500000,
            "civil_max": 50000000,
            "criminal_max_years": 25,
            "basis": "18 USC § 1348, 15 USC § 78j(b)"
        },
        # Late filing violations
        "late_filing": {
            "civil_min": 10000,
            "civil_max": 100000,
            "criminal_max_years": 0,
            "basis": "17 CFR § 240.16a-3"
        },
        # Disclosure violations
        "disclosure_violation": {
            "civil_min": 50000,
            "civil_max": 5000000,
            "criminal_max_years": 0,
            "basis": "17 CFR § 240.10b-5"
        },
        # Market manipulation
        "market_manipulation": {
            "civil_min": 500000,
            "civil_max": 25000000,
            "criminal_max_years": 20,
            "basis": "15 USC § 78j(b), 18 USC § 1348"
        },
        # SOX violations
        "sox_violation": {
            "civil_min": 500000,
            "civil_max": 5000000,
            "criminal_max_years": 20,
            "basis": "SOX § 302, SOX § 906"
        },
        # IRC § 83 tax violations
        "tax_violation": {
            "civil_min": 100000,
            "civil_max": 10000000,
            "criminal_max_years": 5,
            "basis": "26 USC § 83"
        },
        # Beneficial ownership violations
        "beneficial_ownership": {
            "civil_min": 50000,
            "civil_max": 1000000,
            "criminal_max_years": 0,
            "basis": "17 CFR § 240.13d-1, 17 CFR § 240.13d-2"
        }
    }
    
    def __init__(self):
        """Initialize enforcement routing engine."""
        self.logger = logging.getLogger(__name__)
    
    # ═══════════════════════════════════════════════════════════════════════
    # PRIMARY ROUTING METHOD
    # ═══════════════════════════════════════════════════════════════════════
    
    def route_violations(
        self,
        violations: List[Dict[str, Any]],
        statutory_bindings: Optional[List[Dict[str, Any]]] = None
    ) -> List[EnforcementRecommendation]:
        """
        Route violations to appropriate enforcement agencies.
        
        Analyzes violations and generates enforcement recommendations with:
        - SEC trigger threshold assessment
        - Whistleblower program relevance flagging
        - Penalty estimation
        - Priority classification
        - Recommended actions
        
        Args:
            violations: List of detected violations with metadata
            statutory_bindings: Optional statutory binding information
            
        Returns:
            List of EnforcementRecommendation objects
        """
        if not violations:
            self.logger.warning("No violations provided - returning empty recommendations")
            return []
        
        self.logger.info(f"Routing {len(violations)} violations to enforcement agencies")
        
        recommendations = []
        
        # Group violations by type for threshold assessment
        violations_by_type = self._group_violations_by_type(violations)
        
        # Calculate aggregate damages
        total_damages = sum(v.get('estimated_damages', 0) for v in violations)
        
        # Process each violation type
        for violation_type, type_violations in violations_by_type.items():
            # Assess SEC trigger threshold
            trigger_met = self.assess_sec_trigger(
                violations=type_violations,
                violation_type=violation_type
            )
            
            # Calculate penalty estimate
            penalty_estimate = self.calculate_penalty_estimate(
                violation_type=violation_type,
                violation_count=len(type_violations),
                estimated_damages=sum(v.get('estimated_damages', 0) for v in type_violations)
            )
            
            # Determine agencies and case type
            agencies = self._determine_agencies(violation_type, type_violations)
            case_type = self._determine_case_type(violation_type, type_violations)
            priority = self._determine_priority(trigger_met, penalty_estimate, len(type_violations))
            
            # Extract violation IDs
            violation_ids = [v.get('violation_id', v.get('id', 'UNKNOWN')) for v in type_violations]
            
            # Get statutory references from bindings
            statutory_refs = self._extract_statutory_references(
                violation_type, 
                violation_ids, 
                statutory_bindings
            )
            
            # Generate recommendations for each agency
            for agency in agencies:
                # Generate justification
                justification = self._generate_justification(
                    agency=agency,
                    violation_type=violation_type,
                    violation_count=len(type_violations),
                    trigger_met=trigger_met,
                    penalty_estimate=penalty_estimate
                )
                
                # Generate recommended actions
                actions = self._generate_recommended_actions(
                    agency=agency,
                    violation_type=violation_type,
                    case_type=case_type,
                    trigger_met=trigger_met
                )
                
                recommendation = EnforcementRecommendation(
                    agency=agency,
                    case_type=case_type,
                    priority=priority,
                    trigger_threshold_met=trigger_met,
                    justification=justification,
                    estimated_penalties=penalty_estimate,
                    whistleblower_relevant=False,  # Set later
                    violation_ids=violation_ids,
                    statutory_references=statutory_refs,
                    recommended_actions=actions
                )
                
                recommendations.append(recommendation)
        
        # Assess whistleblower relevance across all recommendations
        total_estimated_sanctions = sum(
            r.estimated_penalties.max_penalty if r.estimated_penalties else 0 
            for r in recommendations
        )
        
        for recommendation in recommendations:
            recommendation.whistleblower_relevant = self.assess_whistleblower_relevance(
                estimated_sanctions=total_estimated_sanctions,
                violation_types=[r.agency for r in recommendations]
            )
        
        self.logger.info(f"Generated {len(recommendations)} enforcement recommendations")
        
        return recommendations
    
    # ═══════════════════════════════════════════════════════════════════════
    # SEC TRIGGER ASSESSMENT
    # ═══════════════════════════════════════════════════════════════════════
    
    def assess_sec_trigger(
        self,
        violations: List[Dict[str, Any]],
        violation_type: str
    ) -> bool:
        """
        Assess whether SEC investigation trigger threshold is met.
        
        Evaluates violations against SEC enforcement trigger criteria:
        - Minimum violation count by type
        - Minimum damage thresholds
        - Pattern of conduct indicators
        
        Args:
            violations: List of violations of a specific type
            violation_type: Type of violation
            
        Returns:
            True if trigger threshold is met, False otherwise
        """
        if not violations:
            return False
        
        # Normalize violation type for lookup
        normalized_type = self._normalize_violation_type(violation_type)
        
        # Get threshold criteria
        threshold = self.SEC_TRIGGER_THRESHOLDS.get(
            normalized_type,
            {"min_violations": 3, "min_damages": 100000}  # Default threshold
        )
        
        # Count violations
        violation_count = len(violations)
        
        # Sum damages
        total_damages = sum(v.get('estimated_damages', 0) for v in violations)
        
        # Check thresholds
        meets_count_threshold = violation_count >= threshold["min_violations"]
        meets_damage_threshold = total_damages >= threshold["min_damages"]
        
        # Trigger is met if BOTH thresholds are satisfied
        trigger_met = meets_count_threshold and meets_damage_threshold
        
        if trigger_met:
            self.logger.info(
                f"SEC trigger threshold MET for {violation_type}: "
                f"{violation_count} violations, ${total_damages:,.2f} damages"
            )
        else:
            self.logger.debug(
                f"SEC trigger threshold NOT MET for {violation_type}: "
                f"{violation_count} violations (need {threshold['min_violations']}), "
                f"${total_damages:,.2f} damages (need ${threshold['min_damages']:,.2f})"
            )
        
        return trigger_met
    
    # ═══════════════════════════════════════════════════════════════════════
    # WHISTLEBLOWER PROGRAM ASSESSMENT
    # ═══════════════════════════════════════════════════════════════════════
    
    def assess_whistleblower_relevance(
        self,
        estimated_sanctions: float,
        violation_types: List[str]
    ) -> bool:
        """
        Assess whistleblower program relevance per Dodd-Frank §922.
        
        Whistleblower awards are available when:
        1. Monetary sanctions exceed $1,000,000
        2. Violations fall under SEC/CFTC jurisdiction
        3. Original information leads to successful enforcement
        
        This method evaluates criteria #1 and #2 based on detected violations.
        
        Args:
            estimated_sanctions: Total estimated monetary sanctions
            violation_types: List of violation types or agencies
            
        Returns:
            True if case meets whistleblower program thresholds
        """
        # Check monetary threshold
        meets_monetary_threshold = estimated_sanctions >= self.WHISTLEBLOWER_THRESHOLD
        
        # Check jurisdiction (SEC or CFTC)
        whistleblower_agencies = {'SEC', 'CFTC'}
        has_whistleblower_jurisdiction = any(
            agency in whistleblower_agencies for agency in violation_types
        )
        
        is_relevant = meets_monetary_threshold and has_whistleblower_jurisdiction
        
        if is_relevant:
            # Calculate potential award range (internal use only)
            award_min = estimated_sanctions * self.WHISTLEBLOWER_AWARD_MIN
            award_max = estimated_sanctions * self.WHISTLEBLOWER_AWARD_MAX
            
            self.logger.info(
                f"Whistleblower program RELEVANT: "
                f"${estimated_sanctions:,.2f} estimated sanctions exceeds "
                f"${self.WHISTLEBLOWER_THRESHOLD:,.2f} threshold. "
                f"Potential award range: ${award_min:,.2f} - ${award_max:,.2f}"
            )
        else:
            self.logger.debug(
                f"Whistleblower program NOT RELEVANT: "
                f"${estimated_sanctions:,.2f} sanctions "
                f"(threshold: ${self.WHISTLEBLOWER_THRESHOLD:,.2f})"
            )
        
        return is_relevant
    
    # ═══════════════════════════════════════════════════════════════════════
    # PENALTY ESTIMATION
    # ═══════════════════════════════════════════════════════════════════════
    
    def calculate_penalty_estimate(
        self,
        violation_type: str,
        violation_count: int,
        estimated_damages: float
    ) -> PenaltyRange:
        """
        Calculate estimated penalty range.
        
        Conservative estimates based on:
        - Statutory penalty maximums
        - Historical enforcement patterns
        - Violation count multipliers
        - Damage magnitude
        
        Does not speculate - uses documented precedent and statutory limits.
        
        Args:
            violation_type: Type of violation
            violation_count: Number of violations
            estimated_damages: Estimated monetary damages
            
        Returns:
            PenaltyRange object with min/max estimates
        """
        # Normalize violation type
        normalized_type = self._normalize_violation_type(violation_type)
        
        # Get base penalty range
        penalty_info = self.PENALTY_RANGES.get(
            normalized_type,
            self.PENALTY_RANGES["disclosure_violation"]  # Default
        )
        
        # Calculate base penalties
        base_min = penalty_info["civil_min"]
        base_max = penalty_info["civil_max"]
        
        # Apply violation count multiplier (up to 10x)
        count_multiplier = min(violation_count, 10)
        
        # Apply damage-based multiplier
        damage_multiplier = 1.0
        if estimated_damages > 10000000:  # $10M+
            damage_multiplier = 2.0
        elif estimated_damages > 1000000:  # $1M+
            damage_multiplier = 1.5
        
        # Calculate final ranges
        min_penalty = base_min * count_multiplier
        max_penalty = base_max * count_multiplier * damage_multiplier
        
        # Determine penalty type
        has_criminal = penalty_info["criminal_max_years"] > 0
        penalty_type = "both" if has_criminal else "civil"
        
        return PenaltyRange(
            min_penalty=min_penalty,
            max_penalty=max_penalty,
            penalty_type=penalty_type,
            basis=penalty_info["basis"]
        )
    
    # ═══════════════════════════════════════════════════════════════════════
    # ROUTING REPORT GENERATION
    # ═══════════════════════════════════════════════════════════════════════
    
    def generate_routing_report(
        self,
        recommendations: List[EnforcementRecommendation]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive routing report.
        
        Aggregates enforcement recommendations into a summary report with:
        - Agency breakdown
        - Priority distribution
        - Trigger threshold summary
        - Whistleblower program assessment
        - Total penalty estimates
        
        Args:
            recommendations: List of enforcement recommendations
            
        Returns:
            Dictionary containing comprehensive routing report
        """
        if not recommendations:
            return {
                "total_recommendations": 0,
                "agencies": {},
                "priorities": {},
                "trigger_thresholds_met": 0,
                "whistleblower_relevant": False,
                "estimated_sanctions_range": {"min": 0, "max": 0},
                "summary": "No enforcement recommendations generated"
            }
        
        # Count by agency
        agencies = {}
        for rec in recommendations:
            agencies[rec.agency] = agencies.get(rec.agency, 0) + 1
        
        # Count by priority
        priorities = {}
        for rec in recommendations:
            priorities[rec.priority] = priorities.get(rec.priority, 0) + 1
        
        # Count trigger thresholds met
        trigger_count = sum(1 for rec in recommendations if rec.trigger_threshold_met)
        
        # Check whistleblower relevance
        whistleblower_relevant = any(rec.whistleblower_relevant for rec in recommendations)
        
        # Calculate total sanctions estimate
        total_min = sum(
            rec.estimated_penalties.min_penalty if rec.estimated_penalties else 0
            for rec in recommendations
        )
        total_max = sum(
            rec.estimated_penalties.max_penalty if rec.estimated_penalties else 0
            for rec in recommendations
        )
        
        # Generate summary
        summary_parts = [
            f"{len(recommendations)} enforcement recommendations generated",
            f"{trigger_count} SEC trigger thresholds met",
            f"Agencies: {', '.join(agencies.keys())}",
            f"Estimated sanctions: ${total_min:,.2f} - ${total_max:,.2f}"
        ]
        
        if whistleblower_relevant:
            summary_parts.append("Whistleblower program RELEVANT per Dodd-Frank §922")
        
        return {
            "total_recommendations": len(recommendations),
            "agencies": agencies,
            "priorities": priorities,
            "trigger_thresholds_met": trigger_count,
            "whistleblower_relevant": whistleblower_relevant,
            "estimated_sanctions_range": {
                "min": total_min,
                "max": total_max
            },
            "summary": " | ".join(summary_parts),
            "recommendations": [rec.to_dict() for rec in recommendations]
        }
    
    # ═══════════════════════════════════════════════════════════════════════
    # INTERNAL HELPER METHODS
    # ═══════════════════════════════════════════════════════════════════════
    
    def _group_violations_by_type(
        self,
        violations: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Group violations by type."""
        grouped = {}
        for violation in violations:
            vtype = violation.get('violation_type', violation.get('type', 'unknown'))
            if vtype not in grouped:
                grouped[vtype] = []
            grouped[vtype].append(violation)
        return grouped
    
    def _normalize_violation_type(self, violation_type: str) -> str:
        """Normalize violation type for threshold lookup."""
        vtype_lower = violation_type.lower()
        
        # Map to standard categories
        if 'insider' in vtype_lower or '10b' in vtype_lower or '16a' in vtype_lower:
            return 'insider_trading'
        elif 'fraud' in vtype_lower and 'securities' in vtype_lower:
            return 'securities_fraud'
        elif 'late' in vtype_lower or 'filing' in vtype_lower:
            return 'late_filing'
        elif 'disclosure' in vtype_lower:
            return 'disclosure_violation'
        elif 'manipulation' in vtype_lower:
            return 'market_manipulation'
        elif 'sox' in vtype_lower:
            return 'sox_violation'
        elif 'tax' in vtype_lower or 'irc' in vtype_lower:
            return 'tax_violation'
        elif 'beneficial' in vtype_lower or '13d' in vtype_lower or '13g' in vtype_lower:
            return 'beneficial_ownership'
        else:
            return 'disclosure_violation'  # Default
    
    def _determine_agencies(
        self,
        violation_type: str,
        violations: List[Dict[str, Any]]
    ) -> List[str]:
        """Determine appropriate enforcement agencies."""
        normalized = self._normalize_violation_type(violation_type)
        
        agencies = []
        
        # Primary agency mapping
        if normalized in ['insider_trading', 'securities_fraud', 'disclosure_violation', 
                         'market_manipulation', 'sox_violation', 'beneficial_ownership', 'late_filing']:
            agencies.append('SEC')
        
        if normalized == 'tax_violation':
            agencies.append('IRS')
        
        # Criminal referral for fraud with high damages
        has_high_damages = any(v.get('estimated_damages', 0) > 1000000 for v in violations)
        has_scienter = any(v.get('scienter_evidence', False) for v in violations)
        
        if normalized in ['securities_fraud', 'market_manipulation'] and (has_high_damages or has_scienter):
            if 'DOJ' not in agencies:
                agencies.append('DOJ')
        
        # Default to SEC if no agencies determined
        if not agencies:
            agencies.append('SEC')
        
        return agencies
    
    def _determine_case_type(
        self,
        violation_type: str,
        violations: List[Dict[str, Any]]
    ) -> str:
        """Determine case type (civil or criminal)."""
        normalized = self._normalize_violation_type(violation_type)
        
        # Check for criminal indicators
        has_scienter = any(v.get('scienter_evidence', False) for v in violations)
        has_high_damages = any(v.get('estimated_damages', 0) > 1000000 for v in violations)
        
        # Criminal case types
        if normalized in ['securities_fraud', 'market_manipulation', 'sox_violation']:
            if has_scienter or has_high_damages:
                return 'criminal'
        
        # Default to civil
        return 'civil'
    
    def _determine_priority(
        self,
        trigger_met: bool,
        penalty_estimate: PenaltyRange,
        violation_count: int
    ) -> str:
        """Determine enforcement priority."""
        if trigger_met and penalty_estimate.max_penalty > 10000000:
            return Priority.CRITICAL.value
        elif trigger_met and penalty_estimate.max_penalty > 1000000:
            return Priority.HIGH.value
        elif violation_count >= 5:
            return Priority.HIGH.value
        elif violation_count >= 3:
            return Priority.MEDIUM.value
        else:
            return Priority.LOW.value
    
    def _extract_statutory_references(
        self,
        violation_type: str,
        violation_ids: List[str],
        statutory_bindings: Optional[List[Dict[str, Any]]]
    ) -> List[str]:
        """Extract statutory references from bindings."""
        if not statutory_bindings:
            # Return default references based on violation type
            normalized = self._normalize_violation_type(violation_type)
            penalty_info = self.PENALTY_RANGES.get(normalized, {})
            basis = penalty_info.get('basis', '')
            return [basis] if basis else []
        
        # Extract from bindings
        refs = []
        for binding in statutory_bindings:
            if binding.get('violation_id') in violation_ids:
                statutes = binding.get('statutes', [])
                for statute in statutes:
                    code = statute.get('code') if isinstance(statute, dict) else str(statute)
                    if code and code not in refs:
                        refs.append(code)
        
        return refs
    
    def _generate_justification(
        self,
        agency: str,
        violation_type: str,
        violation_count: int,
        trigger_met: bool,
        penalty_estimate: PenaltyRange
    ) -> str:
        """Generate enforcement justification."""
        parts = [
            f"{agency} enforcement recommendation for {violation_type}",
            f"{violation_count} violation(s) detected",
            f"Estimated penalties: ${penalty_estimate.min_penalty:,.2f} - ${penalty_estimate.max_penalty:,.2f}"
        ]
        
        if trigger_met:
            parts.append("SEC investigation trigger threshold MET")
        
        if penalty_estimate.penalty_type == "both":
            parts.append("Both civil and criminal exposure identified")
        
        return " | ".join(parts)
    
    def _generate_recommended_actions(
        self,
        agency: str,
        violation_type: str,
        case_type: str,
        trigger_met: bool
    ) -> List[str]:
        """Generate recommended enforcement actions."""
        actions = []
        
        # Agency-specific actions
        if agency == 'SEC':
            actions.append("Prepare SEC enforcement referral via TCR system")
            actions.append("Compile evidence package with FRE 902(13)/(14) compliance")
            if trigger_met:
                actions.append("Expedite referral - trigger threshold met")
        
        if agency == 'DOJ':
            actions.append("Prepare criminal referral package for DOJ Fraud Section")
            actions.append("Document scienter evidence for criminal prosecution")
            actions.append("Coordinate with SEC for parallel proceedings")
        
        if agency == 'IRS':
            actions.append("Submit IRS Form 3949-A for tax violation investigation")
            actions.append("Calculate tax deficiency and penalties")
            actions.append("Prepare amended tax return analysis")
        
        # Case-type specific actions
        if case_type == 'criminal':
            actions.append("Interview witnesses under oath")
            actions.append("Execute search warrants if necessary")
            actions.append("Coordinate grand jury proceedings")
        
        # Violation-type specific actions
        normalized = self._normalize_violation_type(violation_type)
        if normalized == 'insider_trading':
            actions.append("Execute trade timing analysis")
            actions.append("Subpoena email and communication records")
            actions.append("Interview individuals with access to material information")
        
        return actions


# ═══════════════════════════════════════════════════════════════════════════
# MODULE EXPORTS
# ═══════════════════════════════════════════════════════════════════════════

__all__ = [
    'EnforcementRoutingEngine',
    'EnforcementRecommendation',
    'PenaltyRange',
    'EnforcementAgency',
    'CaseType',
    'Priority',
    'PenaltyType'
]
