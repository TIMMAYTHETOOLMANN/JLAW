"""
Zero-Dollar Transaction SEC EDGAR Acquisition Module
=====================================================

Acquire and parse SEC Form 4 filings for zero-dollar transaction detection.

Key Components:
- SECEdgarAcquisition: Main acquisition client
- Form4Filing: Parsed Form 4 filing structure
- FilingMetadata: Filing metadata from EDGAR index
- EdgarRateLimiter: SEC-compliant rate limiting
- Custom exceptions for error handling

Reference:
- JLAW Zero-Dollar Transaction Forensic Specification v1.0
- Section 12.2: SEC EDGAR Acquisition Module
- Section 4.2: Data Flow Specification
"""

from .edgar_client import (
    SECEdgarAcquisition,
    enrich_with_issuer_metadata,
    calculate_derived_fields,
)
from .form4_parser import (
    FilingMetadata,
    Form4Filing,
    parse_issuer_element,
    parse_reporting_owner,
    parse_transaction_amounts,
    parse_ownership_nature,
    extract_footnotes,
    link_footnotes_to_transactions,
)
from .rate_limiter import (
    EdgarRateLimiter,
    get_edgar_rate_limiter,
)
from .exceptions import (
    EdgarAcquisitionError,
    EdgarRateLimitError,
    EdgarParsingError,
    EdgarNetworkError,
)

__all__ = [
    # Main client
    'SECEdgarAcquisition',
    'enrich_with_issuer_metadata',
    'calculate_derived_fields',
    
    # Data structures
    'FilingMetadata',
    'Form4Filing',
    
    # Parsing utilities
    'parse_issuer_element',
    'parse_reporting_owner',
    'parse_transaction_amounts',
    'parse_ownership_nature',
    'extract_footnotes',
    'link_footnotes_to_transactions',
    
    # Rate limiting
    'EdgarRateLimiter',
    'get_edgar_rate_limiter',
    
    # Exceptions
    'EdgarAcquisitionError',
    'EdgarRateLimitError',
    'EdgarParsingError',
    'EdgarNetworkError',
]
