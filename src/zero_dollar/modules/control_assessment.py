"""
Control Assessment Module
==========================

Evaluate indicators of retained beneficial ownership control.

Per Section 7.4 of JLAW Zero-Dollar Transaction Forensic Specification v1.0.

Reference:
    - Section 7.4: Beneficial Ownership Chain Construction
    - Control assessment and indicator evaluation
"""

import uuid
from dataclasses import dataclass, field
from decimal import Decimal
from typing import List, Optional
from datetime import datetime

from src.zero_dollar.models import EntityType, EntityReference


@dataclass
class ControlIndicator:
    """
    Single indicator of beneficial control retention.
    
    Attributes:
        indicator_type: Type of control indicator
        description: Human-readable description
        severity: Severity level (CRITICAL, HIGH, MODERATE, LOW)
        regulatory_citation: Applicable SEC/IRS regulation
    """
    indicator_type: str
    description: str
    severity: str  # CRITICAL, HIGH, MODERATE, LOW
    regulatory_citation: Optional[str] = None


@dataclass
class ControlAssessment:
    """
    Comprehensive control retention assessment.
    
    Attributes:
        assessment_id: Unique identifier
        entity: Entity being assessed
        indicators: List of control indicators found
        overall_control_probability: Probability of retained control (0-1)
        recommendation: Action recommendation
        assessment_timestamp: When assessment was performed
    """
    entity: EntityReference
    indicators: List[ControlIndicator]
    overall_control_probability: Decimal
    recommendation: str
    assessment_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    assessment_timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self):
        """Convert to dictionary for serialization."""
        return {
            'assessment_id': self.assessment_id,
            'entity': self.entity.to_dict(),
            'indicators': [
                {
                    'type': ind.indicator_type,
                    'description': ind.description,
                    'severity': ind.severity,
                    'citation': ind.regulatory_citation
                }
                for ind in self.indicators
            ],
            'overall_control_probability': str(self.overall_control_probability),
            'recommendation': self.recommendation,
            'assessment_timestamp': self.assessment_timestamp.isoformat(),
        }


def assess_control_indicators(
    entity: EntityReference,
    schedule_13: Optional[object] = None
) -> ControlAssessment:
    """
    Evaluate indicators of retained beneficial ownership control.
    
    Control Indicators:
        1. Reporting person named as trustee, general partner, or manager
        2. Reporting person family members control entity
        3. Entity address matches reporting person address
        4. Voting power retained per Schedule 13D Item 5
        5. Investment discretion retained per Schedule 13D Item 5
    
    Args:
        entity: EntityReference object to assess
        schedule_13: Optional Schedule 13D/G filing for cross-reference
        
    Returns:
        ControlAssessment with indicators and recommendation
    """
    indicators = []
    
    # Check Schedule 13D/G for voting and dispositive power
    if schedule_13:
        if hasattr(schedule_13, 'sole_voting_power') and schedule_13.sole_voting_power > 0:
            indicators.append(ControlIndicator(
                indicator_type='VOTING_POWER_RETAINED',
                description=f"Voting power: {schedule_13.sole_voting_power} sole shares",
                severity='HIGH',
                regulatory_citation='17 CFR § 240.13d-3'
            ))
        
        if hasattr(schedule_13, 'shared_voting_power') and schedule_13.shared_voting_power > 0:
            indicators.append(ControlIndicator(
                indicator_type='SHARED_VOTING_POWER',
                description=f"Shared voting power: {schedule_13.shared_voting_power} shares",
                severity='HIGH',
                regulatory_citation='17 CFR § 240.13d-3'
            ))
        
        if hasattr(schedule_13, 'sole_dispositive_power') and schedule_13.sole_dispositive_power > 0:
            indicators.append(ControlIndicator(
                indicator_type='DISPOSITIVE_POWER_RETAINED',
                description=f"Dispositive power: {schedule_13.sole_dispositive_power} sole shares",
                severity='HIGH',
                regulatory_citation='17 CFR § 240.13d-3'
            ))
        
        if hasattr(schedule_13, 'shared_dispositive_power') and schedule_13.shared_dispositive_power > 0:
            indicators.append(ControlIndicator(
                indicator_type='SHARED_DISPOSITIVE_POWER',
                description=f"Shared dispositive power: {schedule_13.shared_dispositive_power} shares",
                severity='MODERATE',
                regulatory_citation='17 CFR § 240.13d-3'
            ))
    
    # Entity type-specific indicators
    if entity.entity_type == EntityType.RLT:
        indicators.append(ControlIndicator(
            indicator_type='REVOCABLE_TRUST_CONTROL',
            description="Revocable trusts provide no separation of beneficial ownership",
            severity='CRITICAL',
            regulatory_citation='26 U.S.C. § 676'
        ))
    
    if entity.entity_type in [EntityType.FLP, EntityType.LLC]:
        indicators.append(ControlIndicator(
            indicator_type='GENERAL_PARTNER_PRESUMPTION',
            description="Transferor presumed to retain GP/Manager control absent contrary evidence",
            severity='MODERATE',
            regulatory_citation='17 CFR § 240.13d-3'
        ))
    
    if entity.entity_type in [EntityType.SPOUSE, EntityType.CHILD]:
        indicators.append(ControlIndicator(
            indicator_type='FAMILY_AGGREGATION_REQUIRED',
            description="Family member transfers require aggregation under Section 16",
            severity='HIGH',
            regulatory_citation='15 U.S.C. § 78p(a); 17 CFR § 240.16a-1(a)(2)'
        ))
    
    if entity.entity_type == EntityType.GRAT:
        indicators.append(ControlIndicator(
            indicator_type='ANNUITY_INTEREST_RETAINED',
            description="Grantor retains annuity interest during trust term",
            severity='MODERATE',
            regulatory_citation='26 U.S.C. § 2702'
        ))
    
    if entity.entity_type == EntityType.IRT:
        indicators.append(ControlIndicator(
            indicator_type='IRREVOCABLE_TRUST_INDIRECT_CONTROL',
            description="Grantor may retain indirect control via trustee selection or removal powers",
            severity='MODERATE',
            regulatory_citation='26 U.S.C. § 674'
        ))
    
    if entity.entity_type == EntityType.PF:
        indicators.append(ControlIndicator(
            indicator_type='FOUNDATION_BOARD_CONTROL',
            description="Founders often serve as directors/officers of private foundations",
            severity='MODERATE',
            regulatory_citation='26 U.S.C. § 4946'
        ))
    
    if entity.entity_type == EntityType.DAF:
        indicators.append(ControlIndicator(
            indicator_type='DONOR_ADVISORY_PRIVILEGES',
            description="Donor retains advisory privileges but no legal control",
            severity='LOW',
            regulatory_citation='26 U.S.C. § 4966'
        ))
    
    # Calculate overall control probability
    control_prob = calculate_control_probability(indicators)
    
    # Generate recommendation
    recommendation = generate_control_recommendation(indicators)
    
    return ControlAssessment(
        entity=entity,
        indicators=indicators,
        overall_control_probability=control_prob,
        recommendation=recommendation
    )


def calculate_control_probability(indicators: List[ControlIndicator]) -> Decimal:
    """
    Calculate overall control retention probability from indicators.
    
    Weighted by severity level:
        - CRITICAL: 0.40
        - HIGH: 0.25
        - MODERATE: 0.15
        - LOW: 0.05
    
    Args:
        indicators: List of ControlIndicator objects
        
    Returns:
        Decimal probability from 0.0 to 1.0
    """
    if not indicators:
        return Decimal('0.25')  # Base probability for unknown entities
    
    severity_weights = {
        'CRITICAL': Decimal('0.40'),
        'HIGH': Decimal('0.25'),
        'MODERATE': Decimal('0.15'),
        'LOW': Decimal('0.05')
    }
    
    total = sum(
        severity_weights.get(indicator.severity, Decimal('0.10'))
        for indicator in indicators
    )
    
    # Cap at 1.0
    return min(total, Decimal('1.0'))


def generate_control_recommendation(indicators: List[ControlIndicator]) -> str:
    """
    Generate recommendation based on control indicators.
    
    Recommendations:
        - BENEFICIAL OWNERSHIP RETAINED: Critical indicators present
        - PROBABLE CONTROL RETENTION: Multiple high indicators
        - POSSIBLE CONTROL RETENTION: Single high indicator
        - LOW CONTROL INDICATORS: Only moderate/low indicators
    
    Args:
        indicators: List of ControlIndicator objects
        
    Returns:
        Recommendation string
    """
    if not indicators:
        return "INSUFFICIENT DATA - Unable to assess control retention"
    
    critical_count = sum(1 for ind in indicators if ind.severity == 'CRITICAL')
    high_count = sum(1 for ind in indicators if ind.severity == 'HIGH')
    
    if critical_count > 0:
        return "BENEFICIAL OWNERSHIP RETAINED - Recommend Schedule 13D cross-reference"
    elif high_count >= 2:
        return "PROBABLE CONTROL RETENTION - Enhanced monitoring recommended"
    elif high_count == 1:
        return "POSSIBLE CONTROL RETENTION - Standard review"
    else:
        return "LOW CONTROL INDICATORS - Archive"


def assess_voting_control(
    sole_voting: int,
    shared_voting: int,
    total_shares: int
) -> ControlIndicator:
    """
    Assess voting control from Schedule 13D/G data.
    
    Args:
        sole_voting: Shares with sole voting power
        shared_voting: Shares with shared voting power
        total_shares: Total shares owned
        
    Returns:
        ControlIndicator for voting control
    """
    voting_percentage = ((sole_voting + shared_voting) / total_shares * 100) if total_shares > 0 else 0
    
    if voting_percentage >= 90:
        severity = 'CRITICAL'
        description = f"Retains {voting_percentage:.1f}% voting control"
    elif voting_percentage >= 50:
        severity = 'HIGH'
        description = f"Retains {voting_percentage:.1f}% voting control (majority)"
    elif voting_percentage >= 20:
        severity = 'MODERATE'
        description = f"Retains {voting_percentage:.1f}% voting control"
    else:
        severity = 'LOW'
        description = f"Limited voting control ({voting_percentage:.1f}%)"
    
    return ControlIndicator(
        indicator_type='VOTING_CONTROL_PERCENTAGE',
        description=description,
        severity=severity,
        regulatory_citation='17 CFR § 240.13d-3'
    )


def assess_dispositive_control(
    sole_dispositive: int,
    shared_dispositive: int,
    total_shares: int
) -> ControlIndicator:
    """
    Assess dispositive (investment) control from Schedule 13D/G data.
    
    Args:
        sole_dispositive: Shares with sole dispositive power
        shared_dispositive: Shares with shared dispositive power
        total_shares: Total shares owned
        
    Returns:
        ControlIndicator for dispositive control
    """
    dispositive_percentage = ((sole_dispositive + shared_dispositive) / total_shares * 100) if total_shares > 0 else 0
    
    if dispositive_percentage >= 90:
        severity = 'CRITICAL'
        description = f"Retains {dispositive_percentage:.1f}% dispositive power"
    elif dispositive_percentage >= 50:
        severity = 'HIGH'
        description = f"Retains {dispositive_percentage:.1f}% dispositive power"
    elif dispositive_percentage >= 20:
        severity = 'MODERATE'
        description = f"Retains {dispositive_percentage:.1f}% dispositive power"
    else:
        severity = 'LOW'
        description = f"Limited dispositive power ({dispositive_percentage:.1f}%)"
    
    return ControlIndicator(
        indicator_type='DISPOSITIVE_CONTROL_PERCENTAGE',
        description=description,
        severity=severity,
        regulatory_citation='17 CFR § 240.13d-3'
    )
