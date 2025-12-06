"""
DocsGPT Parser Adapters
========================

Adapters that bridge DocsGPT's parsers with JLAW's forensic system.
"""

# Adapters are loaded lazily to avoid import errors
# when dependencies are not installed

__all__ = ['SECPDFAdapter', 'SECXBRLAdapter']

def get_pdf_adapter():
    """Get PDF adapter instance."""
    from .pdf_adapter import SECPDFAdapter
    return SECPDFAdapter

def get_xbrl_adapter():
    """Get XBRL adapter instance."""
    from .xbrl_adapter import SECXBRLAdapter
    return SECXBRLAdapter

