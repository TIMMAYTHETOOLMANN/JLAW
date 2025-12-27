"""
Magnitude Tier Constants
=========================

Share volume and notional value tier classification for anomaly detection.

Reference:
- Section 3.2: Magnitude Tier Classification
"""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Dict, Optional


class MagnitudeTier(str, Enum):
    """
    Transaction magnitude tier classification.
    
    Defines four tiers of transaction size for risk assessment.
    
    Values:
        TIER_1_ROUTINE: Routine, small transactions
        TIER_2_MODERATE: Moderate-sized transactions
        TIER_3_SUBSTANTIAL: Substantial, material transactions
        TIER_4_EXTRAORDINARY: Extraordinary, outsized transactions
    """
    TIER_1_ROUTINE = "tier_1_routine"
    TIER_2_MODERATE = "tier_2_moderate"
    TIER_3_SUBSTANTIAL = "tier_3_substantial"
    TIER_4_EXTRAORDINARY = "tier_4_extraordinary"


@dataclass
class MagnitudeThreshold:
    """
    Threshold definition for magnitude tier.
    
    Attributes:
        tier: Magnitude tier
        min_shares: Minimum shares for this tier
        max_shares: Maximum shares (None for top tier)
        min_notional: Minimum notional value (USD)
        max_notional: Maximum notional value (None for top tier)
        zero_dollar_risk_multiplier: Risk multiplier for zero-dollar transactions
        description: Human-readable description
        detection_priority: Priority level (1-4, 4=highest)
    """
    tier: MagnitudeTier
    min_shares: int
    max_shares: Optional[int]
    min_notional: Decimal
    max_notional: Optional[Decimal]
    zero_dollar_risk_multiplier: float
    description: str
    detection_priority: int


# Magnitude Tier Thresholds
MAGNITUDE_THRESHOLDS: Dict[MagnitudeTier, MagnitudeThreshold] = {
    MagnitudeTier.TIER_1_ROUTINE: MagnitudeThreshold(
        tier=MagnitudeTier.TIER_1_ROUTINE,
        min_shares=0,
        max_shares=10_000,
        min_notional=Decimal('0'),
        max_notional=Decimal('500_000'),
        zero_dollar_risk_multiplier=1.0,
        description="Routine transactions: <10K shares or <$500K",
        detection_priority=1,
    ),
    MagnitudeTier.TIER_2_MODERATE: MagnitudeThreshold(
        tier=MagnitudeTier.TIER_2_MODERATE,
        min_shares=10_001,
        max_shares=50_000,
        min_notional=Decimal('500_001'),
        max_notional=Decimal('2_500_000'),
        zero_dollar_risk_multiplier=1.5,
        description="Moderate transactions: 10K-50K shares or $500K-$2.5M",
        detection_priority=2,
    ),
    MagnitudeTier.TIER_3_SUBSTANTIAL: MagnitudeThreshold(
        tier=MagnitudeTier.TIER_3_SUBSTANTIAL,
        min_shares=50_001,
        max_shares=250_000,
        min_notional=Decimal('2_500_001'),
        max_notional=Decimal('10_000_000'),
        zero_dollar_risk_multiplier=2.0,
        description="Substantial transactions: 50K-250K shares or $2.5M-$10M",
        detection_priority=3,
    ),
    MagnitudeTier.TIER_4_EXTRAORDINARY: MagnitudeThreshold(
        tier=MagnitudeTier.TIER_4_EXTRAORDINARY,
        min_shares=250_001,
        max_shares=None,
        min_notional=Decimal('10_000_001'),
        max_notional=None,
        zero_dollar_risk_multiplier=3.0,
        description="Extraordinary transactions: >250K shares or >$10M",
        detection_priority=4,
    ),
}


def classify_magnitude(
    shares: int,
    notional_value: Optional[Decimal] = None,
) -> MagnitudeTier:
    """
    Classify transaction magnitude tier.
    
    Uses both share count and notional value to determine tier.
    If either metric qualifies for a higher tier, the higher tier is assigned.
    
    Args:
        shares: Number of shares in transaction
        notional_value: Notional value (shares * price), if known
        
    Returns:
        MagnitudeTier classification
        
    Examples:
        >>> classify_magnitude(5000)
        MagnitudeTier.TIER_1_ROUTINE
        
        >>> classify_magnitude(25000, Decimal('1_000_000'))
        MagnitudeTier.TIER_2_MODERATE
        
        >>> classify_magnitude(500000)
        MagnitudeTier.TIER_4_EXTRAORDINARY
    """
    abs_shares = abs(shares)
    
    # Classify by shares
    tier_by_shares = MagnitudeTier.TIER_1_ROUTINE
    for tier in [
        MagnitudeTier.TIER_4_EXTRAORDINARY,
        MagnitudeTier.TIER_3_SUBSTANTIAL,
        MagnitudeTier.TIER_2_MODERATE,
        MagnitudeTier.TIER_1_ROUTINE,
    ]:
        threshold = MAGNITUDE_THRESHOLDS[tier]
        if abs_shares >= threshold.min_shares:
            if threshold.max_shares is None or abs_shares <= threshold.max_shares:
                tier_by_shares = tier
                break
    
    # If notional value provided, classify by value
    if notional_value is not None:
        abs_notional = abs(notional_value)
        tier_by_value = MagnitudeTier.TIER_1_ROUTINE
        
        for tier in [
            MagnitudeTier.TIER_4_EXTRAORDINARY,
            MagnitudeTier.TIER_3_SUBSTANTIAL,
            MagnitudeTier.TIER_2_MODERATE,
            MagnitudeTier.TIER_1_ROUTINE,
        ]:
            threshold = MAGNITUDE_THRESHOLDS[tier]
            if abs_notional >= threshold.min_notional:
                if threshold.max_notional is None or abs_notional <= threshold.max_notional:
                    tier_by_value = tier
                    break
        
        # Return higher of the two tiers
        tier_values = {
            MagnitudeTier.TIER_1_ROUTINE: 1,
            MagnitudeTier.TIER_2_MODERATE: 2,
            MagnitudeTier.TIER_3_SUBSTANTIAL: 3,
            MagnitudeTier.TIER_4_EXTRAORDINARY: 4,
        }
        
        if tier_values[tier_by_value] > tier_values[tier_by_shares]:
            return tier_by_value
    
    return tier_by_shares


def get_magnitude_threshold(tier: MagnitudeTier) -> MagnitudeThreshold:
    """
    Get threshold definition for a magnitude tier.
    
    Args:
        tier: Magnitude tier
        
    Returns:
        MagnitudeThreshold definition
    """
    return MAGNITUDE_THRESHOLDS[tier]


def calculate_magnitude_risk_score(
    tier: MagnitudeTier,
    is_zero_dollar: bool,
) -> float:
    """
    Calculate risk score based on magnitude tier.
    
    Args:
        tier: Transaction magnitude tier
        is_zero_dollar: Whether transaction is zero-dollar
        
    Returns:
        Risk score (0-25) for magnitude component
    """
    threshold = MAGNITUDE_THRESHOLDS[tier]
    base_score = threshold.detection_priority * 5.0  # Max 20 for tier 4
    
    if is_zero_dollar:
        # Apply multiplier for zero-dollar transactions
        return min(25.0, base_score * threshold.zero_dollar_risk_multiplier)
    
    return base_score


def get_tier_display_name(tier: MagnitudeTier) -> str:
    """
    Get human-readable display name for tier.
    
    Args:
        tier: Magnitude tier
        
    Returns:
        Display name string
    """
    names = {
        MagnitudeTier.TIER_1_ROUTINE: "Tier 1 - Routine",
        MagnitudeTier.TIER_2_MODERATE: "Tier 2 - Moderate",
        MagnitudeTier.TIER_3_SUBSTANTIAL: "Tier 3 - Substantial",
        MagnitudeTier.TIER_4_EXTRAORDINARY: "Tier 4 - Extraordinary",
    }
    return names.get(tier, "Unknown Tier")
