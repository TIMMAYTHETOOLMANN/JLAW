"""
Transaction Data Models
========================

Core data structures for SEC Form 4 transaction representation and analysis.

Reference:
- Section 2.1: Zero-Dollar Transaction Definition
- Section 11.1: Transaction Schema
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from enum import Enum


@dataclass
class Transaction:
    """
    SEC Form 4 transaction with forensic metadata.
    
    Represents a single transaction from Form 4 with all required fields
    for forensic analysis including zero-dollar detection, late filing
    tracking, and notional value calculation.
    
    Attributes:
        accession_number: SEC EDGAR accession number (NNNNNNNNNN-NN-NNNNNN)
        issuer_cik: Central Index Key of the issuing company
        issuer_name: Official company name
        reporting_person_cik: CIK of the reporting insider
        reporting_person_name: Full name of reporting person
        transaction_date: Date transaction was executed
        filing_date: Date Form 4 was filed with SEC
        transaction_code: SEC Form 4 transaction code (P, S, M, A, etc.)
        shares: Number of shares involved in transaction
        price_per_share: Transaction price per share (None for zero-dollar)
        transaction_acquired_disposed: 'A' (acquired) or 'D' (disposed)
        shares_owned_following: Total shares owned after transaction
        direct_indirect: 'D' (direct) or 'I' (indirect ownership)
        nature_of_ownership: Description if indirect (e.g., "By Trust")
        footnotes: List of footnote references
        security_title: Type of security (e.g., "Common Stock")
        form_type: Filing form type (typically "4")
        document_url: URL to filed Form 4 document
        derivative_security: Whether this is a derivative security
        conversion_exercise_price: Price for derivative conversion/exercise
        exercise_date: Date derivative can be exercised
        expiration_date: Date derivative expires
    """
    # SEC Filing Identifiers
    accession_number: str
    issuer_cik: str
    issuer_name: str
    
    # Reporting Person
    reporting_person_cik: str
    reporting_person_name: str
    
    # Transaction Details
    transaction_date: date
    filing_date: date
    transaction_code: str
    shares: Decimal
    price_per_share: Optional[Decimal]
    transaction_acquired_disposed: str  # 'A' or 'D'
    shares_owned_following: Decimal
    
    # Ownership Type
    direct_indirect: str  # 'D' or 'I'
    nature_of_ownership: Optional[str] = None
    
    # Additional Metadata
    footnotes: List[str] = field(default_factory=list)
    security_title: str = "Common Stock"
    form_type: str = "4"
    document_url: Optional[str] = None
    
    # Derivative Fields
    derivative_security: bool = False
    conversion_exercise_price: Optional[Decimal] = None
    exercise_date: Optional[date] = None
    expiration_date: Optional[date] = None
    
    # Forensic Metadata (computed)
    extracted_at: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def is_zero_dollar(self) -> bool:
        """
        Determine if this is a zero-dollar transaction.
        
        Per Section 2.1: A transaction where price_per_share is None,
        zero, or explicitly marked as $0.00 in Form 4 filings.
        
        Returns:
            True if transaction has zero or null price
        """
        return (
            self.price_per_share is None or 
            self.price_per_share == Decimal('0') or
            self.price_per_share == Decimal('0.00')
        )
    
    @property
    def notional_value(self) -> Decimal:
        """
        Calculate notional value of the transaction.
        
        For zero-dollar transactions, this requires market price lookup.
        For priced transactions, multiply shares by price_per_share.
        
        Returns:
            Notional value (shares * price), or 0 for zero-dollar
        """
        if self.is_zero_dollar:
            return Decimal('0')
        return abs(self.shares) * (self.price_per_share or Decimal('0'))
    
    @property
    def days_to_filing(self) -> int:
        """
        Calculate days between transaction and filing.
        
        Section 16(a) requires filing within 2 business days.
        This calculates calendar days for anomaly detection.
        
        Returns:
            Number of calendar days from transaction to filing
        """
        delta = self.filing_date - self.transaction_date
        return delta.days
    
    @property
    def is_late_filing(self) -> bool:
        """
        Determine if filing is late per Section 16(a).
        
        SEC requires Form 4 within 2 business days. We use 3 calendar
        days as conservative threshold for late filing detection.
        
        Returns:
            True if filed more than 3 calendar days after transaction
        """
        return self.days_to_filing > 3
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'accession_number': self.accession_number,
            'issuer_cik': self.issuer_cik,
            'issuer_name': self.issuer_name,
            'reporting_person_cik': self.reporting_person_cik,
            'reporting_person_name': self.reporting_person_name,
            'transaction_date': self.transaction_date.isoformat(),
            'filing_date': self.filing_date.isoformat(),
            'transaction_code': self.transaction_code,
            'shares': str(self.shares),
            'price_per_share': str(self.price_per_share) if self.price_per_share else None,
            'transaction_acquired_disposed': self.transaction_acquired_disposed,
            'shares_owned_following': str(self.shares_owned_following),
            'direct_indirect': self.direct_indirect,
            'nature_of_ownership': self.nature_of_ownership,
            'footnotes': self.footnotes,
            'security_title': self.security_title,
            'form_type': self.form_type,
            'document_url': self.document_url,
            'derivative_security': self.derivative_security,
            'is_zero_dollar': self.is_zero_dollar,
            'notional_value': str(self.notional_value),
            'days_to_filing': self.days_to_filing,
            'is_late_filing': self.is_late_filing,
        }


@dataclass
class TransactionCluster:
    """
    Temporal cluster of related transactions.
    
    Groups transactions by reporting person and temporal proximity
    for pattern detection. Implements temporal clustering algorithm
    per Section 4.2 of the specification.
    
    Attributes:
        cluster_id: Unique cluster identifier
        reporting_person_cik: CIK of reporting person
        reporting_person_name: Name of reporting person
        transactions: List of transactions in cluster
        start_date: Earliest transaction date in cluster
        end_date: Latest transaction date in cluster
        total_shares: Sum of all shares in cluster
        zero_dollar_count: Count of zero-dollar transactions
        cluster_score: Temporal clustering risk score (0-100)
        detection_timestamp: When cluster was identified
    """
    cluster_id: str
    reporting_person_cik: str
    reporting_person_name: str
    transactions: List[Transaction]
    start_date: date
    end_date: date
    total_shares: Decimal
    zero_dollar_count: int
    cluster_score: float
    detection_timestamp: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def cluster_span_days(self) -> int:
        """Calculate temporal span of cluster in days."""
        delta = self.end_date - self.start_date
        return delta.days
    
    @property
    def transaction_count(self) -> int:
        """Total number of transactions in cluster."""
        return len(self.transactions)
    
    @property
    def zero_dollar_ratio(self) -> float:
        """Ratio of zero-dollar to total transactions."""
        if self.transaction_count == 0:
            return 0.0
        return self.zero_dollar_count / self.transaction_count
    
    @property
    def average_notional_value(self) -> Decimal:
        """Average notional value across non-zero transactions."""
        non_zero = [t for t in self.transactions if not t.is_zero_dollar]
        if not non_zero:
            return Decimal('0')
        total = sum(t.notional_value for t in non_zero)
        return total / len(non_zero)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'cluster_id': self.cluster_id,
            'reporting_person_cik': self.reporting_person_cik,
            'reporting_person_name': self.reporting_person_name,
            'transaction_count': self.transaction_count,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'cluster_span_days': self.cluster_span_days,
            'total_shares': str(self.total_shares),
            'zero_dollar_count': self.zero_dollar_count,
            'zero_dollar_ratio': self.zero_dollar_ratio,
            'cluster_score': self.cluster_score,
            'average_notional_value': str(self.average_notional_value),
            'detection_timestamp': self.detection_timestamp.isoformat(),
        }
