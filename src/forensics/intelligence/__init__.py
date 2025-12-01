"""
JLAW Phase 2: Omniscient Intelligence Gathering System
======================================================

Next-generation multi-source intelligence aggregation for forensic investigations.

Components:
- OmniscientIntelligenceGatherer: Unified intelligence aggregation orchestrator
- SECEdgarIntegrator: Deep SEC filing extraction and analysis
- SECFilingStream: Real-time SEC EDGAR monitoring with alerts
- SocialMediaIntelligence: Twitter, Reddit, StockTwits sentiment analysis
- FinancialDataCollector: Real-time and historical market data
- EarningsCallAnalyzer: Transcript analysis with tone detection
- StealthBrowser: Undetectable headless browsing
- ProxyRotator: Anti-detection and rate limit management
"""

from .omniscient_gatherer import OmniscientIntelligenceGatherer
from .sec_edgar_integrator import SECEdgarIntegrator
from .social_intelligence import SocialMediaIntelligence
from .financial_collector import FinancialDataCollector
from .earnings_analyzer import EarningsCallAnalyzer
from .proxy_manager import ProxyRotationManager

# Aliases for blueprint compatibility
SocialIntelligence = SocialMediaIntelligence

# Optional - requires aiohttp
try:
    from .sec_filing_stream import (
        SECFilingStream,
        SECFiling,
        FilingAlert,
        AlertPriority,
        WatchlistEntry,
        StreamStats,
    )
    _stream_available = True
except ImportError:
    SECFilingStream = None
    _stream_available = False

# Optional - requires playwright
try:
    from .stealth_browser import StealthBrowser
    _stealth_available = True
except ImportError:
    StealthBrowser = None
    _stealth_available = False

__all__ = [
    'OmniscientIntelligenceGatherer',
    'SECEdgarIntegrator',
    'SocialMediaIntelligence',
    'SocialIntelligence',
    'FinancialDataCollector',
    'EarningsCallAnalyzer',
    'ProxyRotationManager',
]

if _stream_available:
    __all__.extend([
        'SECFilingStream',
        'SECFiling',
        'FilingAlert',
        'AlertPriority',
        'WatchlistEntry',
        'StreamStats',
    ])

if _stealth_available:
    __all__.append('StealthBrowser')

__version__ = '2.1.0'
__phase__ = 2

