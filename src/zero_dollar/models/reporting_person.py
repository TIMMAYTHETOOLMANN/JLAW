"""
Reporting Person Data Models
=============================

Data structures for SEC Section 16 reporting person classification.

Reference:
- Section 2.2: Reporting Person Classification
- Section 11.2: Reporting Person Schema
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Optional, List, Dict, Any


class ReportingPersonClassification(str, Enum):
    """
    SEC Section 16 reporting person classification.
    
    Defines the four primary classifications of insiders required to
    file Form 4 under Section 16 of the Securities Exchange Act of 1934.
    
    Values:
        SECTION_16_OFFICER: Corporate officer per Rule 16a-1(f)
        SECTION_16_DIRECTOR: Board of directors member
        TEN_PERCENT_OWNER: Beneficial owner of >10% of any class of equity
        AFFILIATED_PERSON: Other affiliated person (family, trust, etc.)
    """
    SECTION_16_OFFICER = "officer"
    SECTION_16_DIRECTOR = "director"
    TEN_PERCENT_OWNER = "ten_percent_owner"
    AFFILIATED_PERSON = "affiliated_person"


@dataclass
class ReportingPerson:
    """
    SEC reporting person with classification and relationship metadata.
    
    Represents an insider required to file Form 4 transactions under
    Section 16. Includes classification, relationship to issuer, and
    historical filing patterns.
    
    Attributes:
        cik: Central Index Key of reporting person
        name: Full legal name
        classification: Primary Section 16 classification
        is_officer: Whether person is a corporate officer
        is_director: Whether person is a board director
        is_ten_percent_owner: Whether person owns >10% equity
        officer_title: Official title if officer (e.g., "Chief Executive Officer")
        relationship_to_issuer: Description of relationship
        issuer_cik: CIK of the issuing company
        issuer_name: Name of issuing company
        first_filing_date: Date of first Form 4 filing
        most_recent_filing_date: Date of most recent filing
        total_filings: Historical count of Form 4 filings
        late_filing_count: Count of late filings (>2 business days)
        zero_dollar_transaction_count: Historical zero-dollar transaction count
        entity_references: List of related entities (trusts, LLCs, etc.)
    """
    # Identity
    cik: str
    name: str
    classification: ReportingPersonClassification
    
    # Section 16 Status Flags
    is_officer: bool = False
    is_director: bool = False
    is_ten_percent_owner: bool = False
    
    # Relationship Details
    officer_title: Optional[str] = None
    relationship_to_issuer: str = "N/A"
    
    # Issuer Information
    issuer_cik: str = ""
    issuer_name: str = ""
    
    # Filing History
    first_filing_date: Optional[date] = None
    most_recent_filing_date: Optional[date] = None
    total_filings: int = 0
    late_filing_count: int = 0
    zero_dollar_transaction_count: int = 0
    
    # Related Entities
    entity_references: List[str] = field(default_factory=list)
    
    # Metadata
    extracted_at: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def late_filing_rate(self) -> float:
        """
        Calculate rate of late filings.
        
        Returns:
            Ratio of late filings to total filings (0.0 to 1.0)
        """
        if self.total_filings == 0:
            return 0.0
        return self.late_filing_count / self.total_filings
    
    @property
    def zero_dollar_rate(self) -> float:
        """
        Calculate rate of zero-dollar transactions.
        
        Returns:
            Ratio of zero-dollar to total transactions (0.0 to 1.0)
        """
        if self.total_filings == 0:
            return 0.0
        return self.zero_dollar_transaction_count / self.total_filings
    
    @property
    def is_high_scrutiny(self) -> bool:
        """
        Determine if person warrants high forensic scrutiny.
        
        High scrutiny applies to officers, directors, and those with
        elevated late filing or zero-dollar transaction rates.
        
        Returns:
            True if person meets high scrutiny criteria
        """
        return (
            self.is_officer or 
            self.is_director or 
            self.late_filing_rate > 0.2 or
            self.zero_dollar_rate > 0.3
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'cik': self.cik,
            'name': self.name,
            'classification': self.classification.value,
            'is_officer': self.is_officer,
            'is_director': self.is_director,
            'is_ten_percent_owner': self.is_ten_percent_owner,
            'officer_title': self.officer_title,
            'relationship_to_issuer': self.relationship_to_issuer,
            'issuer_cik': self.issuer_cik,
            'issuer_name': self.issuer_name,
            'first_filing_date': self.first_filing_date.isoformat() if self.first_filing_date else None,
            'most_recent_filing_date': self.most_recent_filing_date.isoformat() if self.most_recent_filing_date else None,
            'total_filings': self.total_filings,
            'late_filing_count': self.late_filing_count,
            'zero_dollar_transaction_count': self.zero_dollar_transaction_count,
            'late_filing_rate': self.late_filing_rate,
            'zero_dollar_rate': self.zero_dollar_rate,
            'is_high_scrutiny': self.is_high_scrutiny,
            'entity_references': self.entity_references,
        }
