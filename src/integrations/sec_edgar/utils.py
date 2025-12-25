"""
SEC EDGAR Utilities - CIK and Accession Number Normalization
=============================================================

Utility functions for normalizing CIK numbers and accession numbers
to ensure consistent URL construction and data retrieval.

SEC EDGAR URL patterns:
- CIK: Must be 10 digits with leading zeros stripped for some URLs
- Accession: Can be with or without dashes (0001234567-24-000001 or 000123456724000001)
"""

import re
from typing import Optional


def normalize_cik(cik: str) -> str:
    """
    Normalize CIK to 10-digit format with leading zeros.
    
    SEC accepts CIKs in various formats:
    - With leading zeros: '0000320193'
    - Without leading zeros: '320193'
    - As integer: 320193
    
    This function normalizes all formats to 10-digit zero-padded string.
    
    Args:
        cik: CIK in any format
        
    Returns:
        10-digit zero-padded CIK string
        
    Examples:
        >>> normalize_cik('320193')
        '0000320193'
        >>> normalize_cik('0000320193')
        '0000320193'
        >>> normalize_cik(320193)
        '0000320193'
    """
    # Remove all non-digit characters
    cik_clean = re.sub(r'\D', '', str(cik))
    
    # Pad with leading zeros to 10 digits
    return cik_clean.zfill(10)


def strip_cik_leading_zeros(cik: str) -> str:
    """
    Strip leading zeros from CIK.
    
    Some SEC EDGAR URLs require CIK without leading zeros.
    
    Args:
        cik: CIK with or without leading zeros
        
    Returns:
        CIK without leading zeros (or '0' if all zeros)
        
    Examples:
        >>> strip_cik_leading_zeros('0000320193')
        '320193'
        >>> strip_cik_leading_zeros('0000000000')
        '0'
    """
    cik_clean = normalize_cik(cik)
    return cik_clean.lstrip('0') or '0'


def format_accession_number(accession: str, with_dashes: bool = True) -> str:
    """
    Format accession number with or without dashes.
    
    SEC EDGAR uses two formats for accession numbers:
    - With dashes: 0001234567-24-000001 (18 chars + 2 dashes)
    - Without dashes: 000123456724000001 (18 chars)
    
    Args:
        accession: Accession number in any format
        with_dashes: If True, return format with dashes (default)
        
    Returns:
        Formatted accession number
        
    Examples:
        >>> format_accession_number('0001234567-24-000001', with_dashes=False)
        '000123456724000001'
        >>> format_accession_number('000123456724000001', with_dashes=True)
        '0001234567-24-000001'
    """
    # Remove all dashes
    clean = accession.replace('-', '')
    
    # Validate length (should be 18 digits)
    if len(clean) < 18:
        # Pad with leading zeros if needed
        clean = clean.zfill(18)
    
    if with_dashes and len(clean) >= 18:
        # Format: XXXXXXXXXX-XX-XXXXXX
        return f"{clean[:10]}-{clean[10:12]}-{clean[12:]}"
    
    return clean


def build_edgar_document_url(cik: str, accession: str, filename: str) -> str:
    """
    Build SEC EDGAR document URL.
    
    Format: https://www.sec.gov/Archives/edgar/data/{CIK}/{ACCESSION}/{FILENAME}
    
    Args:
        cik: CIK (any format)
        accession: Accession number (any format)
        filename: Document filename
        
    Returns:
        Complete document URL
        
    Examples:
        >>> build_edgar_document_url('320193', '0001234567-24-000001', 'form4.xml')
        'https://www.sec.gov/Archives/edgar/data/320193/000123456724000001/form4.xml'
    """
    cik_clean = strip_cik_leading_zeros(cik)
    accession_clean = format_accession_number(accession, with_dashes=False)
    return f"https://www.sec.gov/Archives/edgar/data/{cik_clean}/{accession_clean}/{filename}"


def build_edgar_index_url(cik: str, accession: str) -> str:
    """
    Build SEC EDGAR index.json URL.
    
    Format: https://www.sec.gov/Archives/edgar/data/{CIK}/{ACCESSION}/index.json
    
    Args:
        cik: CIK (any format)
        accession: Accession number (any format)
        
    Returns:
        Complete index.json URL
        
    Examples:
        >>> build_edgar_index_url('320193', '0001234567-24-000001')
        'https://www.sec.gov/Archives/edgar/data/320193/000123456724000001/index.json'
    """
    return build_edgar_document_url(cik, accession, 'index.json')


def build_submissions_url(cik: str) -> str:
    """
    Build SEC EDGAR submissions API URL.
    
    Format: https://data.sec.gov/submissions/CIK{CIK}.json
    
    Args:
        cik: CIK (any format)
        
    Returns:
        Complete submissions URL
        
    Examples:
        >>> build_submissions_url('320193')
        'https://data.sec.gov/submissions/CIK0000320193.json'
    """
    cik_padded = normalize_cik(cik)
    return f"https://data.sec.gov/submissions/CIK{cik_padded}.json"


def build_xbrl_companyfacts_url(cik: str) -> str:
    """
    Build SEC EDGAR XBRL company facts API URL.
    
    Format: https://data.sec.gov/api/xbrl/companyfacts/CIK{CIK}.json
    
    Args:
        cik: CIK (any format)
        
    Returns:
        Complete company facts URL
        
    Examples:
        >>> build_xbrl_companyfacts_url('320193')
        'https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json'
    """
    cik_padded = normalize_cik(cik)
    return f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik_padded}.json"


def extract_cik_from_url(url: str) -> Optional[str]:
    """
    Extract CIK from SEC EDGAR URL.
    
    Args:
        url: SEC EDGAR URL
        
    Returns:
        Extracted CIK (normalized) or None if not found
        
    Examples:
        >>> extract_cik_from_url('https://www.sec.gov/Archives/edgar/data/320193/...')
        '0000320193'
    """
    # Match CIK in various URL patterns
    patterns = [
        r'/data/(\d+)/',  # Archive URLs
        r'CIK(\d+)',  # API URLs
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return normalize_cik(match.group(1))
    
    return None


def validate_cik(cik: str) -> bool:
    """
    Validate CIK format.
    
    Args:
        cik: CIK to validate
        
    Returns:
        True if valid CIK format
    """
    try:
        cik_clean = re.sub(r'\D', '', str(cik))
        return len(cik_clean) > 0 and len(cik_clean) <= 10 and cik_clean.isdigit()
    except:
        return False


def validate_accession_number(accession: str) -> bool:
    """
    Validate accession number format.
    
    Args:
        accession: Accession number to validate
        
    Returns:
        True if valid accession format
    """
    try:
        clean = accession.replace('-', '')
        return len(clean) >= 18 and clean.isdigit()
    except:
        return False
