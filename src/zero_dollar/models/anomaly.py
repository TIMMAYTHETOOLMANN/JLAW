"""
Anomaly Detection Data Models
==============================

Data structures for anomaly types, severity classifications, and detection results.

Reference:
- Section 3: Detection Methodology
- Section 11.3: Anomaly Schema
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Dict, Any


class AnomalyType(str, Enum):
    """
    Types of zero-dollar transaction anomalies.
    
    Defines the detection patterns per Section 3 of the specification.
    
    Values:
        ZERO_DOLLAR_MAGNITUDE_DISPROPORTION: Large share volume with zero price
        TEMPORAL_CLUSTERING_ANOMALY: Multiple zero-dollar transactions in short window
        LATE_FILING_PATTERN: Systematic late filing beyond Section 16(a) deadline
        RELATED_ENTITY_TRANSFER: Transfer to trust, LLC, family member
        PRE_EVENT_TIMING: Zero-dollar transaction before material corporate event
        POST_EVENT_TIMING: Zero-dollar transaction after material event
        CONTROL_TRANSFER_PATTERN: Ownership changes maintaining control
        DERIVATIVE_CONVERSION_ANOMALY: Suspicious derivative exercise patterns
        CROSS_PERSON_COORDINATION: Coordinated transactions across multiple insiders
        FOOTNOTE_OBFUSCATION: Excessive or vague footnotes obscuring transaction
    """
    ZERO_DOLLAR_MAGNITUDE_DISPROPORTION = "zero_dollar_magnitude_disproportion"
    TEMPORAL_CLUSTERING_ANOMALY = "temporal_clustering_anomaly"
    LATE_FILING_PATTERN = "late_filing_pattern"
    RELATED_ENTITY_TRANSFER = "related_entity_transfer"
    PRE_EVENT_TIMING = "pre_event_timing"
    POST_EVENT_TIMING = "post_event_timing"
    CONTROL_TRANSFER_PATTERN = "control_transfer_pattern"
    DERIVATIVE_CONVERSION_ANOMALY = "derivative_conversion_anomaly"
    CROSS_PERSON_COORDINATION = "cross_person_coordination"
    FOOTNOTE_OBFUSCATION = "footnote_obfuscation"


class AnomalySeverity(str, Enum):
    """
    Severity classification for anomalies.
    
    Based on prosecutorial merit and forensic significance.
    
    Values:
        CRITICAL: Immediate DOJ/SEC referral warranted
        HIGH: Strong prosecutorial merit
        MODERATE: Warrants investigation
        LOW: Informational, pattern monitoring
    """
    CRITICAL = "critical"
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"


class EntityType(str, Enum):
    """
    Types of related entities in ownership structures.
    
    Per Section 2.3: Related Entity Classification
    
    Values:
        RLT: Revocable Living Trust
        IRT: Irrevocable Trust
        GRAT: Grantor Retained Annuity Trust
        FLP: Family Limited Partnership
        LLC: Limited Liability Company
        DAF: Donor-Advised Fund
        PF: Private Foundation
        CRT: Charitable Remainder Trust
        SPOUSE: Spousal ownership
        CHILD: Child ownership
    """
    RLT = "revocable_living_trust"
    IRT = "irrevocable_trust"
    GRAT = "grantor_retained_annuity_trust"
    FLP = "family_limited_partnership"
    LLC = "limited_liability_company"
    DAF = "donor_advised_fund"
    PF = "private_foundation"
    CRT = "charitable_remainder_trust"
    SPOUSE = "spouse"
    CHILD = "child"


@dataclass
class AnomalyFlag:
    """
    Detected anomaly with supporting evidence.
    
    Represents a single anomaly detection with full forensic context.
    
    Attributes:
        flag_id: Unique identifier for this anomaly
        anomaly_type: Type of anomaly detected
        severity: Severity classification
        transaction_accession: Accession number of flagged transaction
        reporting_person_cik: CIK of reporting person
        reporting_person_name: Name of reporting person
        issuer_cik: CIK of issuing company
        issuer_name: Name of issuing company
        detection_date: When anomaly was detected
        transaction_date: Date of the flagged transaction
        shares_involved: Number of shares in transaction
        notional_value: Estimated market value
        description: Human-readable anomaly description
        supporting_evidence: List of evidence identifiers
        forensic_score: Quantitative risk score (0-100)
        requires_investigation: Whether manual review is required
    """
    flag_id: str
    anomaly_type: AnomalyType
    severity: AnomalySeverity
    transaction_accession: str
    reporting_person_cik: str
    reporting_person_name: str
    issuer_cik: str
    issuer_name: str
    detection_date: datetime
    transaction_date: date
    shares_involved: Decimal
    notional_value: Decimal
    description: str
    supporting_evidence: List[str] = field(default_factory=list)
    forensic_score: float = 0.0
    requires_investigation: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'flag_id': self.flag_id,
            'anomaly_type': self.anomaly_type.value,
            'severity': self.severity.value,
            'transaction_accession': self.transaction_accession,
            'reporting_person_cik': self.reporting_person_cik,
            'reporting_person_name': self.reporting_person_name,
            'issuer_cik': self.issuer_cik,
            'issuer_name': self.issuer_name,
            'detection_date': self.detection_date.isoformat(),
            'transaction_date': self.transaction_date.isoformat(),
            'shares_involved': str(self.shares_involved),
            'notional_value': str(self.notional_value),
            'description': self.description,
            'supporting_evidence': self.supporting_evidence,
            'forensic_score': self.forensic_score,
            'requires_investigation': self.requires_investigation,
        }


@dataclass
class MaterialEvent:
    """
    Material corporate event for timing analysis.
    
    Represents significant corporate events (earnings, M&A, etc.) for
    proximity analysis per Section 5.2.
    
    Attributes:
        event_id: Unique event identifier
        issuer_cik: CIK of company
        issuer_name: Company name
        event_type: Type of event (earnings, merger, lawsuit, etc.)
        event_date: Date event occurred or was announced
        event_description: Description of event
        stock_price_impact: Percentage stock price change
        is_price_sensitive: Whether event is material to stock price
        sec_filing_url: URL to related SEC filing (8-K, etc.)
    """
    event_id: str
    issuer_cik: str
    issuer_name: str
    event_type: str
    event_date: date
    event_description: str
    stock_price_impact: Optional[float] = None
    is_price_sensitive: bool = False
    sec_filing_url: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'event_id': self.event_id,
            'issuer_cik': self.issuer_cik,
            'issuer_name': self.issuer_name,
            'event_type': self.event_type,
            'event_date': self.event_date.isoformat(),
            'event_description': self.event_description,
            'stock_price_impact': self.stock_price_impact,
            'is_price_sensitive': self.is_price_sensitive,
            'sec_filing_url': self.sec_filing_url,
        }


@dataclass
class EventProximityFlag:
    """
    Zero-dollar transaction occurring near material event.
    
    Links transactions to nearby corporate events for timing analysis.
    
    Attributes:
        proximity_id: Unique identifier
        transaction_accession: Transaction accession number
        event_id: Material event identifier
        days_before_event: Days transaction preceded event (negative if after)
        proximity_score: Risk score based on timing (0-100)
        is_suspicious_timing: Whether timing warrants investigation
    """
    proximity_id: str
    transaction_accession: str
    event_id: str
    days_before_event: int
    proximity_score: float
    is_suspicious_timing: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'proximity_id': self.proximity_id,
            'transaction_accession': self.transaction_accession,
            'event_id': self.event_id,
            'days_before_event': self.days_before_event,
            'proximity_score': self.proximity_score,
            'is_suspicious_timing': self.is_suspicious_timing,
        }


@dataclass
class EntityReference:
    """
    Parsed entity reference from Form 4 transaction.
    
    Extracted from "nature of ownership" or footnotes to identify
    trusts, LLCs, and other related entities.
    
    Attributes:
        entity_id: Unique entity identifier
        entity_name: Name as appears in Form 4
        entity_type: Classified entity type
        transaction_accession: Source transaction
        reporting_person_cik: Beneficial owner CIK
        confidence_score: NLP extraction confidence (0-1)
        raw_text: Original text from Form 4
    """
    entity_id: str
    entity_name: str
    entity_type: EntityType
    transaction_accession: str
    reporting_person_cik: str
    confidence_score: float
    raw_text: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'entity_id': self.entity_id,
            'entity_name': self.entity_name,
            'entity_type': self.entity_type.value,
            'transaction_accession': self.transaction_accession,
            'reporting_person_cik': self.reporting_person_cik,
            'confidence_score': self.confidence_score,
            'raw_text': self.raw_text,
        }


@dataclass
class ControlIndicator:
    """
    Indicator of beneficial control retention.
    
    Flags transactions that transfer ownership while maintaining control
    through related entities or family members.
    
    Attributes:
        indicator_id: Unique identifier
        transaction_accession: Flagged transaction
        control_mechanism: How control is retained (e.g., "trustee powers")
        related_entities: List of entity IDs involved
        control_percentage: Estimated retained control (0-100%)
        is_control_transfer: Whether this is a control transfer pattern
    """
    indicator_id: str
    transaction_accession: str
    control_mechanism: str
    related_entities: List[str]
    control_percentage: float
    is_control_transfer: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'indicator_id': self.indicator_id,
            'transaction_accession': self.transaction_accession,
            'control_mechanism': self.control_mechanism,
            'related_entities': self.related_entities,
            'control_percentage': self.control_percentage,
            'is_control_transfer': self.is_control_transfer,
        }


@dataclass
class ControlAssessment:
    """
    Assessment of beneficial control across ownership structure.
    
    Aggregates control indicators for a reporting person to determine
    if zero-dollar transfers maintain effective control.
    
    Attributes:
        assessment_id: Unique identifier
        reporting_person_cik: Subject of assessment
        total_control_percentage: Aggregated control estimate
        direct_ownership: Direct ownership percentage
        indirect_ownership: Indirect ownership percentage
        control_indicators: List of control indicator IDs
        assessment_date: When assessment was performed
        is_control_maintained: Whether control appears maintained
    """
    assessment_id: str
    reporting_person_cik: str
    total_control_percentage: float
    direct_ownership: float
    indirect_ownership: float
    control_indicators: List[str]
    assessment_date: datetime
    is_control_maintained: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'assessment_id': self.assessment_id,
            'reporting_person_cik': self.reporting_person_cik,
            'total_control_percentage': self.total_control_percentage,
            'direct_ownership': self.direct_ownership,
            'indirect_ownership': self.indirect_ownership,
            'control_indicators': self.control_indicators,
            'assessment_date': self.assessment_date.isoformat(),
            'is_control_maintained': self.is_control_maintained,
        }


@dataclass
class OwnershipNode:
    """
    Node in beneficial ownership chain graph.
    
    Represents a single entity or person in ownership structure.
    
    Attributes:
        node_id: Unique node identifier
        entity_name: Name of entity or person
        entity_type: Type classification
        ownership_percentage: Percentage of parent entity owned
        is_ultimate_beneficiary: Whether this is the ultimate beneficial owner
    """
    node_id: str
    entity_name: str
    entity_type: str
    ownership_percentage: float
    is_ultimate_beneficiary: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'node_id': self.node_id,
            'entity_name': self.entity_name,
            'entity_type': self.entity_type,
            'ownership_percentage': self.ownership_percentage,
            'is_ultimate_beneficiary': self.is_ultimate_beneficiary,
        }


@dataclass
class OwnershipChain:
    """
    Complete beneficial ownership chain.
    
    Represents the full ownership path from ultimate beneficial owner
    through intermediate entities to the issuer's securities.
    
    Attributes:
        chain_id: Unique chain identifier
        reporting_person_cik: Ultimate beneficial owner
        issuer_cik: Issuer of securities
        nodes: List of ownership nodes in chain
        total_depth: Number of layers in ownership
        effective_ownership: Final ownership percentage
        contains_foreign_entities: Whether chain includes offshore entities
        is_complex_structure: Whether structure warrants enhanced scrutiny
    """
    chain_id: str
    reporting_person_cik: str
    issuer_cik: str
    nodes: List[OwnershipNode]
    total_depth: int
    effective_ownership: float
    contains_foreign_entities: bool = False
    is_complex_structure: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'chain_id': self.chain_id,
            'reporting_person_cik': self.reporting_person_cik,
            'issuer_cik': self.issuer_cik,
            'nodes': [node.to_dict() for node in self.nodes],
            'total_depth': self.total_depth,
            'effective_ownership': self.effective_ownership,
            'contains_foreign_entities': self.contains_foreign_entities,
            'is_complex_structure': self.is_complex_structure,
        }
