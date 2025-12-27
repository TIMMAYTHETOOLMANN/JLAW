"""
HSR Threshold Analysis Module
==============================

Hart-Scott-Rodino threshold analysis for ownership fragmentation detection.

Per Section 7.5 of JLAW Zero-Dollar Transaction Forensic Specification v1.0.

Reference:
    - Section 7.5: HSR Threshold Analysis
    - 15 U.S.C. § 18a - Hart-Scott-Rodino Antitrust Improvements Act
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import List, Tuple, Optional

from src.zero_dollar.models import EntityReference


# HSR Thresholds (2024, adjusted annually per 16 CFR § 801.1)
HSR_THRESHOLD_2024 = Decimal('119500000')  # $119.5 million
HSR_SIZE_OF_PERSON_2024 = Decimal('478000000')  # $478.0 million


@dataclass
class HSRAnalysis:
    """
    Hart-Scott-Rodino threshold analysis results.
    
    Attributes:
        aggregate_beneficial_ownership_shares: Total shares across controlled entities
        aggregate_beneficial_ownership_value: Total notional value
        hsr_threshold: Applicable HSR threshold
        threshold_exceeded: Whether aggregate exceeds threshold
        fragmentation_pattern_detected: Whether evasion pattern detected
        individual_entity_holdings: Holdings by entity
        regulatory_citations: Applicable regulations
        recommendation: Action recommendation
    """
    aggregate_beneficial_ownership_shares: Decimal
    aggregate_beneficial_ownership_value: Decimal
    hsr_threshold: Decimal
    threshold_exceeded: bool
    fragmentation_pattern_detected: bool
    individual_entity_holdings: List[Tuple[EntityReference, Decimal]]
    regulatory_citations: List[str]
    recommendation: str
    
    def to_dict(self):
        """Convert to dictionary for serialization."""
        return {
            'aggregate_shares': str(self.aggregate_beneficial_ownership_shares),
            'aggregate_value': str(self.aggregate_beneficial_ownership_value),
            'hsr_threshold': str(self.hsr_threshold),
            'threshold_exceeded': self.threshold_exceeded,
            'fragmentation_detected': self.fragmentation_pattern_detected,
            'entity_count': len(self.individual_entity_holdings),
            'individual_holdings': [
                {
                    'entity_name': entity.entity_name,
                    'entity_type': entity.entity_type.value,
                    'value': str(value)
                }
                for entity, value in self.individual_entity_holdings
            ],
            'regulatory_citations': self.regulatory_citations,
            'recommendation': self.recommendation,
        }


def check_hsr_circumvention(
    ownership_chain: object,
    issuer_cik: str,
    share_price: Decimal
) -> HSRAnalysis:
    """
    Analyze ownership fragmentation for Hart-Scott-Rodino threshold evasion.
    
    HSR Thresholds (2024, adjusted annually):
        - $119.5 million transaction size threshold
        - $478.0 million size-of-person threshold (alternative)
        - 15 U.S.C. § 18a notification requirements
    
    Circumvention Indicators:
        1. Aggregate holdings across controlled entities exceed threshold
        2. Individual entity holdings structured below threshold
        3. Timing of transfers clusters around threshold-crossing acquisitions
    
    Args:
        ownership_chain: OwnershipChain object with nodes
        issuer_cik: CIK of issuing company
        share_price: Current market price per share
        
    Returns:
        HSRAnalysis with fragmentation detection results
    """
    # Calculate aggregate beneficial ownership across chain
    # Only count entities where control probability > 50%
    aggregate_shares = Decimal('0')
    individual_holdings = []
    
    if hasattr(ownership_chain, 'nodes'):
        for node in ownership_chain.nodes:
            # Check if node has required attributes
            if not hasattr(node, 'shares_transferred'):
                continue
                
            shares = node.shares_transferred
            
            # Check control indicators
            control_prob = Decimal('0.5')  # Default
            if hasattr(node, 'control_indicators') and hasattr(node.control_indicators, 'overall_control_probability'):
                control_prob = node.control_indicators.overall_control_probability
            
            # Only count if control is retained (>50% probability)
            if control_prob > Decimal('0.5'):
                aggregate_shares += shares
                
                # Calculate notional value for this entity
                entity_value = shares * share_price
                entity_ref = node.entity if hasattr(node, 'entity') else None
                
                if entity_ref:
                    individual_holdings.append((entity_ref, entity_value))
    
    # Calculate aggregate notional value
    aggregate_notional = aggregate_shares * share_price
    
    # Check fragmentation pattern
    # Fragmentation detected if:
    # - Aggregate exceeds threshold
    # - BUT each individual entity is below threshold
    # - AND multiple entities involved (at least 2)
    fragmentation_detected = (
        aggregate_notional >= HSR_THRESHOLD_2024 and
        len(individual_holdings) >= 2 and
        all(holding[1] < HSR_THRESHOLD_2024 for holding in individual_holdings)
    )
    
    # Determine recommendation
    if fragmentation_detected:
        recommendation = 'FTC/DOJ ANTITRUST REFERRAL - Potential HSR circumvention detected'
    elif aggregate_notional >= HSR_THRESHOLD_2024:
        recommendation = 'HSR THRESHOLD EXCEEDED - Verify HSR compliance'
    elif aggregate_notional >= HSR_THRESHOLD_2024 * Decimal('0.8'):
        recommendation = 'APPROACHING HSR THRESHOLD - Monitor for additional acquisitions'
    else:
        recommendation = 'NO ACTION - Below HSR thresholds'
    
    return HSRAnalysis(
        aggregate_beneficial_ownership_shares=aggregate_shares,
        aggregate_beneficial_ownership_value=aggregate_notional,
        hsr_threshold=HSR_THRESHOLD_2024,
        threshold_exceeded=aggregate_notional >= HSR_THRESHOLD_2024,
        fragmentation_pattern_detected=fragmentation_detected,
        individual_entity_holdings=individual_holdings,
        regulatory_citations=[
            '15 U.S.C. § 18a',
            '16 CFR § 801 et seq.',
            'Hart-Scott-Rodino Antitrust Improvements Act of 1976',
            '16 CFR § 801.1 (Threshold adjustments)'
        ],
        recommendation=recommendation
    )


def calculate_hsr_threshold_distance(
    aggregate_value: Decimal,
    threshold: Decimal = HSR_THRESHOLD_2024
) -> Tuple[Decimal, float]:
    """
    Calculate distance from HSR threshold.
    
    Args:
        aggregate_value: Total beneficial ownership value
        threshold: HSR threshold to compare against
        
    Returns:
        Tuple of (dollar distance, percentage distance)
    """
    distance = threshold - aggregate_value
    percentage = float((aggregate_value / threshold) * 100) if threshold > 0 else 0.0
    
    return distance, percentage


def detect_threshold_fragmentation(
    holdings: List[Tuple[EntityReference, Decimal]],
    threshold: Decimal = HSR_THRESHOLD_2024
) -> dict:
    """
    Detect if holdings are deliberately fragmented below threshold.
    
    Statistical analysis of holding sizes to detect artificial fragmentation.
    
    Args:
        holdings: List of (entity, value) tuples
        threshold: Threshold to check against
        
    Returns:
        Dictionary with fragmentation analysis
    """
    if not holdings:
        return {
            'is_fragmented': False,
            'confidence': 0.0,
            'indicators': []
        }
    
    indicators = []
    
    # Check if all holdings are suspiciously close to threshold
    values = [value for _, value in holdings]
    avg_value = sum(values) / len(values)
    
    if len(holdings) >= 2:
        # Check if holdings are near threshold
        threshold_proximity = sum(
            1 for value in values
            if value >= threshold * Decimal('0.80') and value < threshold
        )
        
        if threshold_proximity >= 2:
            indicators.append('Multiple holdings within 80-100% of threshold')
        
        # Check if aggregate exceeds but individuals don't
        aggregate = sum(values)
        if aggregate >= threshold and all(v < threshold for v in values):
            indicators.append('Aggregate exceeds threshold while individuals remain below')
        
        # Check for uniform sizing (suggests deliberate structuring)
        if len(holdings) >= 3:
            max_value = max(values)
            min_value = min(values)
            if max_value > 0 and (min_value / max_value) > Decimal('0.7'):
                indicators.append('Holdings uniformly sized (may indicate structuring)')
    
    is_fragmented = len(indicators) >= 2
    confidence = min(len(indicators) / 3.0, 1.0)
    
    return {
        'is_fragmented': is_fragmented,
        'confidence': confidence,
        'indicators': indicators,
        'holding_count': len(holdings),
        'aggregate_value': sum(values),
        'average_value': avg_value,
    }


def get_hsr_filing_requirements(
    aggregate_value: Decimal,
    acquirer_size: Optional[Decimal] = None
) -> dict:
    """
    Determine HSR filing requirements based on transaction size.
    
    Args:
        aggregate_value: Transaction value
        acquirer_size: Size of acquiring person (optional)
        
    Returns:
        Dictionary with filing requirements
    """
    filing_required = aggregate_value >= HSR_THRESHOLD_2024
    
    # Alternative threshold based on size of person
    if acquirer_size and acquirer_size >= HSR_SIZE_OF_PERSON_2024:
        filing_required = aggregate_value >= HSR_THRESHOLD_2024
    
    if not filing_required:
        return {
            'filing_required': False,
            'threshold_type': None,
            'filing_fee': None,
            'waiting_period': None,
        }
    
    # Determine filing fee tier (2024 rates)
    if aggregate_value >= Decimal('5000000000'):  # $5B+
        filing_fee = Decimal('2390000')
        tier = 'Tier 4'
    elif aggregate_value >= Decimal('1000000000'):  # $1B - $5B
        filing_fee = Decimal('1190000')
        tier = 'Tier 3'
    elif aggregate_value >= Decimal('500000000'):  # $500M - $1B
        filing_fee = Decimal('280000')
        tier = 'Tier 2'
    else:  # $119.5M - $500M
        filing_fee = Decimal('45000')
        tier = 'Tier 1'
    
    return {
        'filing_required': True,
        'threshold_type': 'Size of Transaction',
        'filing_fee': str(filing_fee),
        'filing_fee_tier': tier,
        'waiting_period': '30 days (or early termination)',
        'form': 'Notification and Report Form for Certain Mergers and Acquisitions',
    }
