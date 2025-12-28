"""
SEC EDGAR Models - Data Structures for Acquisitions
===================================================

Structured result types for SEC filing acquisitions with integrity tracking.

Note: DocumentType and ValidationResult are defined in document_validator.py
and re-exported here for convenience.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, Dict, Any, List
from enum import Enum

# Import and re-export validation types
from .document_validator import DocumentType, ValidationResult


class AcquisitionStatus(Enum):
    """Status of an acquisition attempt."""
    SUCCESS = "success"
    ERROR = "error"
    RETRIED = "retried"
    CACHED = "cached"
    MOCK = "mock"


@dataclass
class IntegrityHashes:
    """Triple-hash integrity verification for FRE 902(13)/(14) compliance."""
    sha256: str
    sha3_512: str
    blake2b: str
    
    def to_dict(self) -> Dict[str, str]:
        return {
            "sha256": self.sha256,
            "sha3_512": self.sha3_512,
            "blake2b": self.blake2b
        }
    
    def verify(self, other: 'IntegrityHashes') -> bool:
        """Verify all three hashes match."""
        return (
            self.sha256 == other.sha256 and
            self.sha3_512 == other.sha3_512 and
            self.blake2b == other.blake2b
        )


@dataclass
class SECFiling:
    """
    Parsed SEC filing metadata.
    
    This is a re-export of the existing SECFiling class for convenience.
    Actual implementation is in edgar_client.py.
    """
    accession_number: str
    form_type: str
    filing_date: date
    report_date: Optional[date]
    primary_document: str
    file_number: str
    cik: str
    company_name: str
    document_url: str
    index_url: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "accession_number": self.accession_number,
            "form_type": self.form_type,
            "filing_date": self.filing_date.isoformat(),
            "report_date": self.report_date.isoformat() if self.report_date else None,
            "primary_document": self.primary_document,
            "document_url": self.document_url,
            "cik": self.cik,
            "company_name": self.company_name
        }


@dataclass
class AcquisitionResult:
    """
    Result of a filing acquisition attempt with integrity tracking.
    
    Tracks success/failure, retry count, response codes, and integrity hashes
    for FRE 902(13)/(14) compliant evidence chains.
    """
    success: bool
    status: AcquisitionStatus
    filing: Optional[SECFiling] = None
    content: Optional[str] = None
    error: Optional[str] = None
    retry_count: int = 0
    response_code: Optional[int] = None
    integrity_hashes: Optional[IntegrityHashes] = None
    retrieved_at: datetime = field(default_factory=datetime.utcnow)
    source: str = "sec_edgar_api"  # 'sec_edgar_api', 'cache', 'mock'
    cache_hit: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "status": self.status.value,
            "filing": self.filing.to_dict() if self.filing else None,
            "error": self.error,
            "retry_count": self.retry_count,
            "response_code": self.response_code,
            "integrity_hashes": self.integrity_hashes.to_dict() if self.integrity_hashes else None,
            "retrieved_at": self.retrieved_at.isoformat(),
            "source": self.source,
            "cache_hit": self.cache_hit
        }
    
    @classmethod
    def success_result(
        cls,
        filing: SECFiling,
        content: str,
        integrity_hashes: IntegrityHashes,
        retry_count: int = 0,
        response_code: int = 200,
        source: str = "sec_edgar_api",
        cache_hit: bool = False
    ) -> 'AcquisitionResult':
        """Create a successful acquisition result."""
        status = AcquisitionStatus.CACHED if cache_hit else AcquisitionStatus.SUCCESS
        return cls(
            success=True,
            status=status,
            filing=filing,
            content=content,
            integrity_hashes=integrity_hashes,
            retry_count=retry_count,
            response_code=response_code,
            source=source,
            cache_hit=cache_hit
        )
    
    @classmethod
    def error_result(
        cls,
        error: str,
        filing: Optional[SECFiling] = None,
        retry_count: int = 0,
        response_code: Optional[int] = None
    ) -> 'AcquisitionResult':
        """Create an error acquisition result."""
        return cls(
            success=False,
            status=AcquisitionStatus.ERROR,
            filing=filing,
            error=error,
            retry_count=retry_count,
            response_code=response_code
        )


@dataclass
class XBRLContext:
    """XBRL context information for period and entity identification."""
    context_id: str
    entity_identifier: str
    entity_scheme: str  # Usually 'http://www.sec.gov/CIK'
    period_type: str  # 'instant' or 'duration'
    instant_date: Optional[date] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "context_id": self.context_id,
            "entity_identifier": self.entity_identifier,
            "entity_scheme": self.entity_scheme,
            "period_type": self.period_type,
            "instant_date": self.instant_date.isoformat() if self.instant_date else None,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None
        }


@dataclass
class Form4TransactionCode:
    """SEC Form 4 transaction code taxonomy."""
    code: str
    description: str
    category: str  # 'GENERAL', 'RULE_16B3', 'DERIVATIVE', 'GIFT', 'OTHER_EXEMPT'
    is_exempt: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "description": self.description,
            "category": self.category,
            "is_exempt": self.is_exempt
        }


# Complete taxonomy of SEC Form 4 transaction codes
FORM4_TRANSACTION_CODES: Dict[str, Form4TransactionCode] = {
    'P': Form4TransactionCode('P', 'Open market or private purchase', 'GENERAL'),
    'S': Form4TransactionCode('S', 'Open market or private sale', 'GENERAL'),
    'A': Form4TransactionCode('A', 'Grant, award, or other acquisition from issuer', 'RULE_16B3', True),
    'D': Form4TransactionCode('D', 'Disposition to issuer', 'RULE_16B3', True),
    'F': Form4TransactionCode('F', 'Payment of exercise price or tax liability', 'RULE_16B3', True),
    'I': Form4TransactionCode('I', 'Discretionary transaction', 'RULE_16B3', True),
    'M': Form4TransactionCode('M', 'Exercise or conversion of derivative', 'DERIVATIVE'),
    'C': Form4TransactionCode('C', 'Conversion of derivative security', 'DERIVATIVE'),
    'E': Form4TransactionCode('E', 'Expiration of short derivative position', 'DERIVATIVE'),
    'H': Form4TransactionCode('H', 'Expiration of long derivative position', 'DERIVATIVE'),
    'O': Form4TransactionCode('O', 'Exercise of out-of-the-money derivative', 'DERIVATIVE'),
    'X': Form4TransactionCode('X', 'Exercise of in-the-money derivative', 'DERIVATIVE'),
    'G': Form4TransactionCode('G', 'Gift', 'GIFT', True),
    'J': Form4TransactionCode('J', 'Other acquisition or disposition', 'OTHER_EXEMPT', True),
    'L': Form4TransactionCode('L', 'Small acquisition', 'OTHER_EXEMPT', True),
    'W': Form4TransactionCode('W', 'Acquisition or disposition by will', 'OTHER_EXEMPT', True),
}
