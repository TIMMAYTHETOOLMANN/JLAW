"""Node 7: 13F-HR Institutional Holdings Analyzer.

Provides comprehensive analysis of Schedule 13F-HR filings for:
- Institutional investor position tracking
- Wolf pack accumulation detection
- Coordinated trading pattern identification
- Quarter-over-quarter position change analysis
"""

from .institutional_analyzer import InstitutionalHoldingsAnalyzer
from .institutional_analyzer_v2 import InstitutionalHoldingsAnalyzerV2

# Attempt to import SEC client if available
try:
    from .sec_edgar_client import SECEDGARClient
    _HAS_SEC_CLIENT = True
except ImportError:
    SECEDGARClient = None
    _HAS_SEC_CLIENT = False

__all__ = [
    'InstitutionalHoldingsAnalyzer',
    'InstitutionalHoldingsAnalyzerV2',
]

if _HAS_SEC_CLIENT:
    __all__.append('SECEDGARClient')
