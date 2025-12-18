"""Node 9: 8-K Material Event Correlator.

Provides comprehensive analysis of Form 8-K filings for:
- Material event detection and classification
- Insider trading correlation (pre/post event)
- Market impact assessment
- Cross-filing pattern analysis
"""

from .material_event_correlator import MaterialEventCorrelator

# Attempt to import V2 analyzer if available
try:
    from .material_event_correlator_v2 import MaterialEventCorrelatorV2
    _HAS_V2 = True
except ImportError:
    MaterialEventCorrelatorV2 = None
    _HAS_V2 = False

# Attempt to import market data client if available
try:
    from .market_data_client import MarketDataClient
    _HAS_MARKET_CLIENT = True
except ImportError:
    MarketDataClient = None
    _HAS_MARKET_CLIENT = False

__all__ = [
    'MaterialEventCorrelator',
]

if _HAS_V2:
    __all__.append('MaterialEventCorrelatorV2')
if _HAS_MARKET_CLIENT:
    __all__.append('MarketDataClient')
