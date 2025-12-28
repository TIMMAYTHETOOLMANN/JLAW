"""
SEC EDGAR Integration Module
============================

Production-grade SEC EDGAR API client with comprehensive features:
- Rate limiting (9 req/sec with 60s cooldown on 403)
- Triple-hash integrity verification (SHA-256 + SHA3-512 + BLAKE2b)
- Document completeness validation
- Connection pooling and retry strategy
- CIK/accession number normalization
- Structured acquisition results

Key Components:
- edgar_client.SECEdgarClient: Main API client
- document_validator.SECDocumentValidator: Document validation engine
- rate_limiter.RateLimiter: Shared rate limiter with cooldown
- models: Data structures (AcquisitionResult, IntegrityHashes, etc.)
- utils: CIK/accession normalization utilities
- session_manager: HTTP session management
"""

from .edgar_client import SECEdgarClient, FormType, SECFiling, XBRLFact
from .document_validator import SECDocumentValidator, DocumentType, ValidationResult
from .rate_limiter import RateLimiter, get_shared_rate_limiter
from .models import (
    AcquisitionResult,
    AcquisitionStatus,
    IntegrityHashes,
    XBRLContext,
    Form4TransactionCode,
    FORM4_TRANSACTION_CODES
)
from .utils import (
    normalize_cik,
    strip_cik_leading_zeros,
    format_accession_number,
    build_edgar_document_url,
    build_edgar_index_url,
    build_submissions_url,
    build_xbrl_companyfacts_url,
    extract_cik_from_url,
    validate_cik,
    validate_accession_number
)

__all__ = [
    # Main client
    'SECEdgarClient',
    'FormType',
    'SECFiling',
    'XBRLFact',
    
    # Document validation
    'SECDocumentValidator',
    'DocumentType',
    'ValidationResult',
    
    # Rate limiting
    'RateLimiter',
    'get_shared_rate_limiter',
    
    # Models
    'AcquisitionResult',
    'AcquisitionStatus',
    'IntegrityHashes',
    'XBRLContext',
    'Form4TransactionCode',
    'FORM4_TRANSACTION_CODES',
    
    # Utilities
    'normalize_cik',
    'strip_cik_leading_zeros',
    'format_accession_number',
    'build_edgar_document_url',
    'build_edgar_index_url',
    'build_submissions_url',
    'build_xbrl_companyfacts_url',
    'extract_cik_from_url',
    'validate_cik',
    'validate_accession_number',
]
