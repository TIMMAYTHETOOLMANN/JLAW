"""
JLAW Phase 2: Omniscient Intelligence Gathering Module
======================================================

Multi-source intelligence gathering with forensic chain-of-custody.
Supports:
- SEC EDGAR filings
- Public web scraping
- News aggregation
- Social media intelligence
- Financial data streams
"""

from .omniscient_scraper import OmniscientIntelligenceGatherer
from .earnings_call_analyzer import EarningsCallAnalyzer
from .web_intelligence import WebIntelligenceGatherer
from .social_intelligence import SocialMediaIntelligenceGatherer
from .sec_client import SecClient

__all__ = [
    'OmniscientIntelligenceGatherer',
    'EarningsCallAnalyzer',
    'WebIntelligenceGatherer',
    'SocialMediaIntelligenceGatherer',
    'SecClient'
]

