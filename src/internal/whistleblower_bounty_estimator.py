"""
JLAW Internal Module: Whistleblower Bounty Estimator
=====================================================

INTERNAL USE ONLY - DO NOT EXPORT OR SERIALIZE

This module estimates potential SEC whistleblower bounty amounts based on
detected violations and enforcement actions. This is for internal forensic
analysis and should not be exposed through public APIs or serialized to
prevent gaming the system.

Legal Basis:
- Dodd-Frank Act Section 922 (15 USC §78u-6)
- SEC Rule 21F (Whistleblower Program)
- SEC Order Determining Whistleblower Award Claims

Award Range: 10-30% of monetary sanctions exceeding $1,000,000
"""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from decimal import Decimal
from enum import Enum
import warnings


class ViolationSeverity(Enum):
    """Severity classification for violations."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EnforcementAgency(Enum):
    """Enforcement agencies that may bring actions."""
    SEC = "sec"
    DOJ = "doj"
    IRS = "irs"
    CFTC = "cftc"


@dataclass
class BountyEstimate:
    """
    Estimated whistleblower bounty calculation.
    
    WARNING: This class cannot be serialized or exported to prevent
    gaming the whistleblower program.
    """
    estimated_sanctions_min: Decimal
    estimated_sanctions_max: Decimal
    bounty_percentage_min: float  # 0.10 = 10%
    bounty_percentage_max: float  # 0.30 = 30%
    bounty_amount_min: Decimal
    bounty_amount_max: Decimal
    violation_count: int
    critical_violations: int
    enforcement_agencies: List[EnforcementAgency]
    confidence_level: str  # low, medium, high
    basis: str
    
    def __repr__(self) -> str:
        """Prevent accidental serialization."""
        return f"<BountyEstimate [INTERNAL USE ONLY - DO NOT SERIALIZE]>"
    
    def __str__(self) -> str:
        """Prevent accidental serialization."""
        return "[INTERNAL BOUNTY ESTIMATE - CONFIDENTIAL]"
    
    def to_dict(self) -> Dict[str, Any]:
        """Raise error to prevent serialization."""
        raise PermissionError(
            "BountyEstimate cannot be serialized or exported. "
            "This is internal-only information to prevent gaming the whistleblower program."
        )
    
    def __getstate__(self):
        """Prevent pickling."""
        raise PermissionError(
            "BountyEstimate cannot be pickled or serialized."
        )


class WhistleblowerBountyEstimator:
    """
    Estimates potential SEC whistleblower bounty amounts.
    
    INTERNAL USE ONLY - This estimator is designed for forensic analysis
    and should not be exposed through public APIs or user interfaces.
    """
    
    # SEC whistleblower award range (Dodd-Frank §922)
    MIN_BOUNTY_PERCENTAGE = 0.10  # 10%
    MAX_BOUNTY_PERCENTAGE = 0.30  # 30%
    MIN_SANCTIONS_THRESHOLD = Decimal("1000000")  # $1M minimum
    
    # Estimated penalty ranges by violation type (conservative estimates)
    VIOLATION_PENALTIES = {
        "insider_trading": (Decimal("100000"), Decimal("10000000")),
        "securities_fraud": (Decimal("500000"), Decimal("50000000")),
        "accounting_fraud": (Decimal("1000000"), Decimal("100000000")),
        "disclosure_violation": (Decimal("50000"), Decimal("5000000")),
        "market_manipulation": (Decimal("500000"), Decimal("25000000")),
        "bribery_fcpa": (Decimal("1000000"), Decimal("200000000")),
        "compensation_violation": (Decimal("100000"), Decimal("10000000")),
        "sox_violation": (Decimal("500000"), Decimal("25000000")),
        "tax_fraud": (Decimal("1000000"), Decimal("50000000")),
    }
    
    def __init__(self):
        """Initialize the bounty estimator."""
        warnings.warn(
            "WhistleblowerBountyEstimator is for internal use only. "
            "Do not expose estimates through public APIs.",
            category=UserWarning,
            stacklevel=2
        )
    
    def estimate_bounty(
        self,
        violations: List[Dict[str, Any]],
        company_market_cap: Optional[Decimal] = None,
        prior_enforcement_history: bool = False
    ) -> BountyEstimate:
        """
        Estimate potential whistleblower bounty based on detected violations.
        
        Args:
            violations: List of detected violations with types and severity
            company_market_cap: Market capitalization for scaling estimates
            prior_enforcement_history: Whether company has prior enforcement actions
            
        Returns:
            BountyEstimate object (cannot be serialized)
        """
        if not violations:
            return self._create_zero_estimate()
        
        # Classify violations by type and severity
        violation_count = len(violations)
        critical_violations = sum(
            1 for v in violations 
            if v.get('severity') == 'critical' or v.get('severity', 0) >= 8
        )
        
        # Estimate sanctions based on violation types
        min_sanctions = Decimal("0")
        max_sanctions = Decimal("0")
        
        for violation in violations:
            vtype = violation.get('type', 'disclosure_violation')
            # Map violation types to penalty estimates
            penalty_range = self.VIOLATION_PENALTIES.get(
                vtype,
                self.VIOLATION_PENALTIES['disclosure_violation']
            )
            min_sanctions += penalty_range[0]
            max_sanctions += penalty_range[1]
        
        # Apply multipliers for critical violations
        if critical_violations > 0:
            critical_multiplier = Decimal("1.5") * Decimal(str(critical_violations))
            max_sanctions *= critical_multiplier
        
        # Scale based on company size if available
        if company_market_cap and company_market_cap > Decimal("1000000000"):
            # Larger companies face higher penalties
            size_factor = min(
                Decimal("3.0"),
                (company_market_cap / Decimal("10000000000"))
            )
            max_sanctions *= size_factor
        
        # Apply multiplier for repeat offenders
        if prior_enforcement_history:
            min_sanctions *= Decimal("1.25")
            max_sanctions *= Decimal("1.5")
        
        # Ensure minimum threshold
        if max_sanctions < self.MIN_SANCTIONS_THRESHOLD:
            max_sanctions = self.MIN_SANCTIONS_THRESHOLD
        
        # Calculate bounty range
        bounty_min = max(
            Decimal("0"),
            min_sanctions * Decimal(str(self.MIN_BOUNTY_PERCENTAGE))
        )
        bounty_max = max_sanctions * Decimal(str(self.MAX_BOUNTY_PERCENTAGE))
        
        # Determine confidence level
        confidence = self._determine_confidence(
            violation_count,
            critical_violations,
            bool(company_market_cap)
        )
        
        # Identify potential enforcement agencies
        agencies = self._identify_agencies(violations)
        
        # Create basis description
        basis = (
            f"Estimated based on {violation_count} violations "
            f"({critical_violations} critical) with potential enforcement by "
            f"{', '.join(a.value.upper() for a in agencies)}"
        )
        
        return BountyEstimate(
            estimated_sanctions_min=min_sanctions,
            estimated_sanctions_max=max_sanctions,
            bounty_percentage_min=self.MIN_BOUNTY_PERCENTAGE,
            bounty_percentage_max=self.MAX_BOUNTY_PERCENTAGE,
            bounty_amount_min=bounty_min,
            bounty_amount_max=bounty_max,
            violation_count=violation_count,
            critical_violations=critical_violations,
            enforcement_agencies=agencies,
            confidence_level=confidence,
            basis=basis
        )
    
    def _create_zero_estimate(self) -> BountyEstimate:
        """Create a zero-value estimate."""
        return BountyEstimate(
            estimated_sanctions_min=Decimal("0"),
            estimated_sanctions_max=Decimal("0"),
            bounty_percentage_min=0.0,
            bounty_percentage_max=0.0,
            bounty_amount_min=Decimal("0"),
            bounty_amount_max=Decimal("0"),
            violation_count=0,
            critical_violations=0,
            enforcement_agencies=[],
            confidence_level="n/a",
            basis="No violations detected"
        )
    
    def _determine_confidence(
        self,
        violation_count: int,
        critical_violations: int,
        has_market_cap: bool
    ) -> str:
        """Determine confidence level for estimate."""
        if violation_count == 0:
            return "n/a"
        
        score = 0
        if violation_count >= 5:
            score += 1
        if critical_violations >= 2:
            score += 1
        if has_market_cap:
            score += 1
        
        if score >= 2:
            return "high"
        elif score == 1:
            return "medium"
        else:
            return "low"
    
    def _identify_agencies(
        self,
        violations: List[Dict[str, Any]]
    ) -> List[EnforcementAgency]:
        """Identify which enforcement agencies may be involved."""
        agencies = set()
        
        for violation in violations:
            vtype = violation.get('type', '')
            
            # SEC violations
            if any(term in vtype for term in [
                'insider', 'securities', 'disclosure', 'market', 'sox', '10-k', '10-q'
            ]):
                agencies.add(EnforcementAgency.SEC)
            
            # DOJ violations (criminal)
            if any(term in vtype for term in [
                'fraud', 'bribery', 'fcpa', 'obstruction'
            ]):
                agencies.add(EnforcementAgency.DOJ)
            
            # IRS violations
            if any(term in vtype for term in [
                'tax', 'irc', '83', '409a'
            ]):
                agencies.add(EnforcementAgency.IRS)
        
        # Default to SEC if none identified
        if not agencies:
            agencies.add(EnforcementAgency.SEC)
        
        return list(agencies)


__all__ = [
    'WhistleblowerBountyEstimator',
    'BountyEstimate',
    'ViolationSeverity',
    'EnforcementAgency'
]
