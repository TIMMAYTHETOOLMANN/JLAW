"""
SEC EDGAR Acquisition Exceptions
=================================

Custom exceptions for SEC EDGAR data acquisition errors.

Reference:
- JLAW Zero-Dollar Transaction Forensic Specification v1.0
- Section 12.2: SEC EDGAR Acquisition Module
"""


class EdgarAcquisitionError(Exception):
    """Base exception for EDGAR acquisition errors."""
    pass


class EdgarRateLimitError(EdgarAcquisitionError):
    """Raised when SEC API rate limit is exceeded."""
    
    def __init__(self, message: str = "SEC API rate limit exceeded"):
        self.message = message
        super().__init__(self.message)


class EdgarParsingError(EdgarAcquisitionError):
    """Raised when Form 4 XML parsing fails."""
    
    def __init__(self, message: str, accession_number: str = None):
        self.message = message
        self.accession_number = accession_number
        if accession_number:
            super().__init__(f"{message} (Accession: {accession_number})")
        else:
            super().__init__(message)


class EdgarNetworkError(EdgarAcquisitionError):
    """Raised on network or HTTP errors."""
    
    def __init__(self, message: str, status_code: int = None):
        self.message = message
        self.status_code = status_code
        if status_code:
            super().__init__(f"{message} (HTTP {status_code})")
        else:
            super().__init__(message)
