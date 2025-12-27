"""
Event Proximity Analysis Module
================================

Cross-reference zero-dollar transactions against material corporate events to
identify potential Material Nonpublic Information (MNPI) exploitation or
strategic timing indicative of informed disposition.

Per Section 6 of JLAW Zero-Dollar Transaction Forensic Specification v1.0.

Reference:
    - Section 6: Event Proximity Analysis Module
    - Section 6.1: Module Objective
    - Section 6.3: Proximity Detection Algorithm
    - Section 6.4: Output Specification
"""

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Tuple, Optional, Dict, Any

from src.zero_dollar.models import Transaction, MaterialEvent, EventProximityFlag
from src.zero_dollar.acquisition.event_calendar import EventCalendarAcquisition
from .material_event_taxonomy import (
    EventCategory,
    FORM_8K_EVENTS,
    EARNINGS_EVENTS,
    get_event_category,
)
from .mnpi_scoring import (
    calculate_mnpi_score,
    get_event_citations,
    determine_mnpi_severity,
)

logger = logging.getLogger(__name__)


@dataclass
class EventProximityOutput:
    """
    Output from Event Proximity Analysis Module.
    
    Contains all detected event proximity flags, aggregate statistics, and
    regulatory citations per Section 6.4 of the specification.
    
    Attributes:
        issuer_cik: CIK of issuer company
        analysis_period: Tuple of (start_date, end_date) for analysis window
        events_analyzed: Number of material events analyzed
        transactions_analyzed: Number of zero-dollar transactions analyzed
        flags_generated: List of EventProximityFlag objects
        high_risk_flags: Count of flags with mnpi_score > 0.5
        regulatory_citations: List of applicable statutory references
        detection_timestamp: When analysis was performed
        evidence_hash: SHA-256 hash for chain of custody
    """
    issuer_cik: str
    analysis_period: Tuple[date, date]
    events_analyzed: int
    transactions_analyzed: int
    flags_generated: List[EventProximityFlag]
    high_risk_flags: int
    regulatory_citations: List[str] = field(default_factory=list)
    detection_timestamp: datetime = field(default_factory=datetime.utcnow)
    evidence_hash: Optional[str] = None
    
    @property
    def flag_count(self) -> int:
        """Total number of proximity flags generated."""
        return len(self.flags_generated)
    
    @property
    def critical_flags(self) -> int:
        """Count of flags with CRITICAL severity."""
        return sum(1 for flag in self.flags_generated 
                  if determine_mnpi_severity(flag.mnpi_inference_score) == 'CRITICAL')
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'issuer_cik': self.issuer_cik,
            'analysis_period': {
                'start_date': self.analysis_period[0].isoformat(),
                'end_date': self.analysis_period[1].isoformat(),
            },
            'events_analyzed': self.events_analyzed,
            'transactions_analyzed': self.transactions_analyzed,
            'flag_count': self.flag_count,
            'high_risk_flags': self.high_risk_flags,
            'critical_flags': self.critical_flags,
            'flags_generated': [
                {
                    'flag_id': flag.flag_id,
                    'transaction_id': flag.transaction_id,
                    'event_id': flag.event.event_id if flag.event else None,
                    'proximity_type': flag.proximity_type,
                    'days_delta': flag.days_delta,
                    'mnpi_inference_score': str(flag.mnpi_inference_score),
                    'severity': determine_mnpi_severity(flag.mnpi_inference_score),
                    'regulatory_citations': flag.regulatory_citations,
                    'narrative': flag.narrative,
                }
                for flag in self.flags_generated
            ],
            'regulatory_citations': self.regulatory_citations,
            'detection_timestamp': self.detection_timestamp.isoformat(),
            'evidence_hash': self.evidence_hash,
        }


class EventProximityModule:
    """
    Event Proximity Analysis Module.
    
    Cross-references zero-dollar transactions against material corporate events
    to detect MNPI exploitation patterns.
    
    Per Section 6 of JLAW Zero-Dollar Transaction Forensic Specification.
    
    The module performs the following analysis steps:
        1. Fetch material events for issuer within expanded window
        2. For each zero-dollar transaction, check proximity to events
        3. Calculate MNPI inference score for matches
        4. Generate EventProximityFlag for suspicious proximity
        5. Compute evidence hash for chain of custody
    
    Attributes:
        config: Configuration dictionary with optional parameters
        event_buffer_days: Additional days to extend event search window
    """
    
    def __init__(self, config: dict = None):
        """
        Initialize Event Proximity Module.
        
        Args:
            config: Optional configuration dictionary with keys:
                   - event_buffer_days: Days to extend event search (default: 60)
                   - user_agent: SEC EDGAR User-Agent string
                   - mnpi_threshold: Minimum score for flagging (default: 0.3)
        """
        self.config = config or {}
        self.event_buffer_days = self.config.get('event_buffer_days', 60)
        self.mnpi_threshold = self.config.get('mnpi_threshold', Decimal('0.3'))
        self.user_agent = self.config.get('user_agent', 
            'JLAW-Forensics/2.0 Zero-Dollar-Detection forensics@jlaw-system.org')
    
    async def analyze(
        self,
        transactions: List[Transaction],
        issuer_cik: str,
        analysis_window: Tuple[date, date]
    ) -> EventProximityOutput:
        """
        Execute event proximity analysis on zero-dollar transactions.
        
        Performs complete analysis workflow per Section 6:
            1. Fetch material events for issuer within expanded window
            2. For each zero-dollar transaction, check proximity to events
            3. Calculate MNPI inference score for matches
            4. Generate EventProximityFlag for suspicious proximity
            5. Compute evidence hash for chain of custody
        
        Args:
            transactions: List of Transaction objects to analyze
            issuer_cik: CIK of issuing company
            analysis_window: Tuple of (start_date, end_date) for analysis
        
        Returns:
            EventProximityOutput with all detected proximity flags
        """
        logger.info(f"Starting event proximity analysis for CIK {issuer_cik}")
        
        # Filter to zero-dollar transactions
        zero_dollar_txns = [txn for txn in transactions if txn.is_zero_dollar]
        logger.info(f"Analyzing {len(zero_dollar_txns)} zero-dollar transactions")
        
        # Expand event search window
        start_date, end_date = analysis_window
        expanded_start = start_date - timedelta(days=self.event_buffer_days)
        expanded_end = end_date + timedelta(days=self.event_buffer_days)
        
        # Fetch material events
        events = await self.fetch_material_events(
            issuer_cik,
            expanded_start,
            expanded_end
        )
        logger.info(f"Retrieved {len(events)} material events")
        
        # Detect proximity for each transaction
        flags = []
        for txn in zero_dollar_txns:
            txn_flags = self.detect_event_proximity(txn, events)
            flags.extend(txn_flags)
        
        # Compute aggregate statistics
        high_risk_flags = sum(1 for flag in flags 
                             if flag.mnpi_inference_score >= Decimal('0.5'))
        
        # Collect unique regulatory citations
        all_citations = set()
        for flag in flags:
            all_citations.update(flag.regulatory_citations)
        
        # Compute evidence hash
        evidence_hash = self._compute_evidence_hash(flags)
        
        output = EventProximityOutput(
            issuer_cik=issuer_cik,
            analysis_period=analysis_window,
            events_analyzed=len(events),
            transactions_analyzed=len(zero_dollar_txns),
            flags_generated=flags,
            high_risk_flags=high_risk_flags,
            regulatory_citations=sorted(list(all_citations)),
            evidence_hash=evidence_hash,
        )
        
        logger.info(f"Generated {len(flags)} proximity flags ({high_risk_flags} high-risk)")
        return output
    
    async def fetch_material_events(
        self,
        issuer_cik: str,
        start_date: date,
        end_date: date
    ) -> List[MaterialEvent]:
        """
        Retrieve material events for issuer within date range.
        
        Fetches Form 8-K filings and earnings announcements from SEC EDGAR
        and external data sources.
        
        Args:
            issuer_cik: SEC Central Index Key for issuer
            start_date: Start of event search window
            end_date: End of event search window
        
        Returns:
            List of MaterialEvent objects
        """
        config = {'user_agent': self.user_agent}
        
        async with EventCalendarAcquisition(config) as client:
            # Fetch 8-K events
            events_8k = await client.fetch_8k_events(issuer_cik, start_date, end_date)
            
            # Fetch earnings events (placeholder - requires ticker lookup)
            # TODO: Implement ticker resolution from CIK
            # events_earnings = await client.fetch_earnings_dates(ticker, start_date, end_date)
            events_earnings = []
            
            # Combine all events
            all_events = events_8k + events_earnings
            
            return all_events
    
    def detect_event_proximity(
        self,
        transaction: Transaction,
        events: List[MaterialEvent]
    ) -> List[EventProximityFlag]:
        """
        Cross-reference transaction with events to detect proximity.
        
        For each material event, calculates temporal distance and MNPI score.
        Generates EventProximityFlag for transactions within proximity windows.
        
        Args:
            transaction: Transaction to analyze
            events: List of MaterialEvent objects
        
        Returns:
            List of EventProximityFlag for suspicious proximity matches
        """
        flags = []
        txn_date = transaction.transaction_date
        
        for event in events:
            # Calculate days between transaction and event
            days_delta = (event.event_date - txn_date).days
            
            # Determine proximity type
            if days_delta > 0:
                proximity_type = 'PRE_EVENT'  # Transaction before event
            elif days_delta < 0:
                proximity_type = 'POST_EVENT'  # Transaction after event
            else:
                proximity_type = 'SAME_DAY'  # Same day - treat as PRE_EVENT
                days_delta = 0
            
            # Get event category from taxonomy
            sensitivity = self._get_event_sensitivity(event)
            
            # Check if within proximity window
            if not self._is_within_proximity_window(event, abs(days_delta), proximity_type):
                continue
            
            # Calculate MNPI score
            mnpi_score = calculate_mnpi_score(
                event=event,
                days_delta=abs(days_delta),
                proximity_type='PRE' if proximity_type in ['PRE_EVENT', 'SAME_DAY'] else 'POST',
                sensitivity=sensitivity
            )
            
            # Only flag if above threshold
            if mnpi_score < self.mnpi_threshold:
                continue
            
            # Get regulatory citations
            citations = get_event_citations(event, sensitivity)
            
            # Generate narrative
            narrative = self._generate_narrative(
                transaction, event, days_delta, proximity_type, mnpi_score
            )
            
            # Compute evidence hash for this flag
            evidence_hash = self._compute_flag_hash(transaction, event, mnpi_score)
            
            # Create flag
            flag = EventProximityFlag(
                flag_id=f"EPF-{transaction.accession_number}-{event.event_id}",
                transaction_id=transaction.accession_number,
                event=event,
                proximity_type=proximity_type,
                days_delta=days_delta,
                mnpi_inference_score=mnpi_score,
                regulatory_citations=citations,
                narrative=narrative,
                evidence_hash=evidence_hash,
            )
            
            flags.append(flag)
        
        return flags
    
    def _get_event_sensitivity(self, event: MaterialEvent) -> str:
        """Extract sensitivity level from event type via taxonomy."""
        event_type = event.event_type
        
        # Extract item number from 8K events (e.g., "8K-2.02" -> "2.02")
        if event_type.startswith('8K-'):
            item = event_type.replace('8K-', '')
            if item in FORM_8K_EVENTS:
                return FORM_8K_EVENTS[item].mnpi_sensitivity
        
        # Check earnings events
        for key, category in EARNINGS_EVENTS.items():
            if key in event_type or category.description.lower() in event.event_description.lower():
                return category.mnpi_sensitivity
        
        # Default to MODERATE if not found
        return 'MODERATE'
    
    def _is_within_proximity_window(
        self,
        event: MaterialEvent,
        days_delta: int,
        proximity_type: str
    ) -> bool:
        """Check if transaction is within event's proximity window."""
        event_type = event.event_type
        
        # Get event category
        if event_type.startswith('8K-'):
            item = event_type.replace('8K-', '')
            if item in FORM_8K_EVENTS:
                category = FORM_8K_EVENTS[item]
            else:
                return False
        else:
            # Default windows for earnings events
            category = EventCategory(
                item="DEFAULT",
                description="",
                mnpi_sensitivity="MODERATE",
                lookback_days=14,
                lookforward_days=2
            )
        
        # Check if within window
        if proximity_type in ['PRE_EVENT', 'SAME_DAY']:
            return days_delta <= category.lookback_days
        else:  # POST_EVENT
            return days_delta <= category.lookforward_days
    
    def _generate_narrative(
        self,
        transaction: Transaction,
        event: MaterialEvent,
        days_delta: int,
        proximity_type: str,
        mnpi_score: Decimal
    ) -> str:
        """Generate human-readable narrative for proximity flag."""
        severity = determine_mnpi_severity(mnpi_score)
        
        direction = "before" if proximity_type in ['PRE_EVENT', 'SAME_DAY'] else "after"
        abs_days = abs(days_delta)
        day_word = "day" if abs_days == 1 else "days"
        
        narrative = (
            f"{severity} MNPI risk: Zero-dollar transaction of {transaction.shares:,} shares "
            f"executed {abs_days} {day_word} {direction} material event "
            f"({event.event_description}). "
            f"MNPI inference probability: {mnpi_score:.1%}. "
            f"Reporting person: {transaction.reporting_person_name}. "
        )
        
        if transaction.nature_of_ownership:
            narrative += f"Ownership: {transaction.nature_of_ownership}. "
        
        return narrative
    
    def _compute_flag_hash(
        self,
        transaction: Transaction,
        event: MaterialEvent,
        mnpi_score: Decimal
    ) -> str:
        """Compute SHA-256 hash for evidence integrity."""
        evidence_data = (
            f"{transaction.accession_number}|"
            f"{transaction.transaction_date.isoformat()}|"
            f"{event.event_id}|"
            f"{event.event_date.isoformat()}|"
            f"{mnpi_score}"
        )
        return hashlib.sha256(evidence_data.encode('utf-8')).hexdigest()
    
    def _compute_evidence_hash(self, flags: List[EventProximityFlag]) -> str:
        """Compute aggregate evidence hash for all flags."""
        if not flags:
            return hashlib.sha256(b"NO_FLAGS").hexdigest()
        
        combined_hashes = "|".join(flag.evidence_hash for flag in flags)
        return hashlib.sha256(combined_hashes.encode('utf-8')).hexdigest()


def detect_event_proximity(
    transactions: List[Transaction],
    events: List[MaterialEvent],
    config: dict = None
) -> List[EventProximityFlag]:
    """
    Convenience function to detect event proximity without module instantiation.
    
    Args:
        transactions: List of Transaction objects
        events: List of MaterialEvent objects
        config: Optional configuration dictionary
    
    Returns:
        List of EventProximityFlag objects
    """
    module = EventProximityModule(config)
    
    flags = []
    for txn in transactions:
        if txn.is_zero_dollar:
            txn_flags = module.detect_event_proximity(txn, events)
            flags.extend(txn_flags)
    
    return flags


__all__ = [
    'EventProximityModule',
    'EventProximityOutput',
    'detect_event_proximity',
]
