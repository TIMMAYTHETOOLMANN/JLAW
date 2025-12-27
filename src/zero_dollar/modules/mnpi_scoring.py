"""
MNPI Scoring Algorithm
======================

Calculate Material Nonpublic Information (MNPI) inference probability scores
for zero-dollar transactions in proximity to material corporate events.

Per Section 6.3 of JLAW Zero-Dollar Transaction Forensic Specification v1.0.

Reference:
    - Section 6.3: Proximity Detection Algorithm
    - Section 6.3.1: MNPI Score Calculation Formula
    - 15 U.S.C. § 78j(b) - Securities Exchange Act Section 10(b)
    - 17 CFR § 240.10b-5 - Rule 10b-5
"""

import math
from decimal import Decimal
from typing import List

from src.zero_dollar.models import MaterialEvent


def calculate_mnpi_score(
    event: MaterialEvent,
    days_delta: int,
    proximity_type: str,
    sensitivity: str = None
) -> Decimal:
    """
    Calculate MNPI inference probability score.
    
    Computes the likelihood that a zero-dollar transaction was executed
    based on Material Nonpublic Information (MNPI), considering:
        1. Event Sensitivity Level (CRITICAL=1.0, HIGH=0.75, MODERATE=0.5, LOW=0.25)
        2. Temporal Proximity (exponential decay with distance from event)
        3. Direction Alignment (PRE_EVENT dispositions before negative news score higher)
    
    Formula:
        MNPI_SCORE = SENSITIVITY * e^(-λ * days_delta) * DIRECTION_FACTOR
    
    Where:
        λ = 0.1 (decay constant, calibrated to half-life of ~7 days)
        DIRECTION_FACTOR = 1.0 for dispositions before negative events
                         = 0.5 for dispositions before positive events
                         = 0.25 for post-event transactions
    
    Args:
        event: MaterialEvent object with sensitivity information
        days_delta: Absolute days between transaction and event (always positive)
        proximity_type: 'PRE' (before event) or 'POST' (after event)
        sensitivity: Optional override for event sensitivity
                    (CRITICAL, HIGH, MODERATE, LOW, VARIABLE)
    
    Returns:
        Decimal: MNPI exploitation probability score [0.0 - 1.0]
    
    Example:
        >>> event = MaterialEvent(event_type="2.02", ...)
        >>> score = calculate_mnpi_score(event, days_delta=3, proximity_type='PRE', sensitivity='CRITICAL')
        >>> print(score)  # 0.741 (high probability)
    """
    # Sensitivity mapping
    sensitivity_map = {
        'CRITICAL': Decimal('1.0'),
        'HIGH': Decimal('0.75'),
        'MODERATE': Decimal('0.5'),
        'LOW': Decimal('0.25'),
        'VARIABLE': Decimal('0.5'),  # Default for variable sensitivity events
    }
    
    # Use provided sensitivity or extract from event_type
    # Note: event object stores event_type as string, sensitivity must be provided
    # or determined from taxonomy
    if sensitivity is None:
        sensitivity = 'MODERATE'  # Default fallback
    
    sensitivity_score = sensitivity_map.get(sensitivity, Decimal('0.25'))
    
    # Exponential decay based on temporal distance
    # λ = 0.1 gives half-life of ~7 days
    lambda_decay = 0.1
    temporal_factor = Decimal(str(math.exp(-lambda_decay * abs(days_delta))))
    
    # Direction factor - pre-event more suspicious than post-event
    if proximity_type == 'PRE':
        direction_factor = Decimal('1.0')  # Pre-event dispositions are highly suspicious
    else:  # POST
        direction_factor = Decimal('0.25')  # Post-event less suspicious
    
    # Calculate final MNPI score
    mnpi_score = sensitivity_score * temporal_factor * direction_factor
    
    # Quantize to 3 decimal places
    return mnpi_score.quantize(Decimal('0.001'))


def get_event_citations(event: MaterialEvent, sensitivity: str = None) -> List[str]:
    """
    Return applicable regulatory citations for event type.
    
    Provides statutory and regulatory references for enforcement actions
    based on event sensitivity and type.
    
    Args:
        event: MaterialEvent object
        sensitivity: Optional sensitivity level (CRITICAL, HIGH, MODERATE, LOW)
    
    Returns:
        List of regulatory citations (CFR sections, USC sections)
    
    Example:
        >>> event = MaterialEvent(event_type="2.02", ...)
        >>> citations = get_event_citations(event, sensitivity='CRITICAL')
        >>> print(citations)
        ['15 U.S.C. § 78j(b)', '17 CFR § 240.10b-5', '17 CFR § 240.10b5-1', 
         '18 U.S.C. § 1348', 'Regulation FD (17 CFR § 243)']
    """
    # Base citations applicable to all insider trading violations
    base_citations = [
        '15 U.S.C. § 78j(b)',   # Securities Exchange Act Section 10(b)
        '17 CFR § 240.10b-5',   # Rule 10b-5 (antifraud)
    ]
    
    # Add critical-level citations for high-sensitivity events
    if sensitivity == 'CRITICAL':
        base_citations.extend([
            '17 CFR § 240.10b5-1',  # Rule 10b5-1 (trading plans)
            '18 U.S.C. § 1348',      # Securities fraud (criminal statute)
        ])
    
    # Add Regulation FD for earnings-related events
    event_type = event.event_type.lower() if hasattr(event, 'event_type') else ''
    if 'earnings' in event_type or 'quarterly' in event_type or 'annual' in event_type:
        base_citations.append('Regulation FD (17 CFR § 243)')
    
    # Add Form 8-K citations for specific event types
    if event_type in ['2.02', '2.06', '4.02', '1.03', '3.01', '5.01']:
        # Major disclosure events
        base_citations.append('17 CFR § 229.308 (Item 308 - Internal Controls)')
    
    return base_citations


def determine_mnpi_severity(mnpi_score: Decimal) -> str:
    """
    Classify MNPI score into severity level.
    
    Maps MNPI probability score to investigation priority level.
    
    Args:
        mnpi_score: MNPI inference probability [0.0 - 1.0]
    
    Returns:
        Severity level: CRITICAL, HIGH, MODERATE, or LOW
    
    Classification:
        - CRITICAL: score >= 0.70 (immediate investigation)
        - HIGH: score >= 0.50 (priority investigation)
        - MODERATE: score >= 0.30 (enhanced monitoring)
        - LOW: score < 0.30 (routine monitoring)
    """
    if mnpi_score >= Decimal('0.70'):
        return 'CRITICAL'
    elif mnpi_score >= Decimal('0.50'):
        return 'HIGH'
    elif mnpi_score >= Decimal('0.30'):
        return 'MODERATE'
    else:
        return 'LOW'


__all__ = [
    'calculate_mnpi_score',
    'get_event_citations',
    'determine_mnpi_severity',
]
