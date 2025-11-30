"""
Intelligence Module
===================

Real-time intelligence gathering and monitoring capabilities.

Components:
-----------
- SECFilingStream: Real-time SEC EDGAR filing monitoring
- (future) SocialSentimentStream: Social media sentiment monitoring
- (future) NewsAlertStream: News and press release monitoring
"""

from .sec_filing_stream import (
    SECFilingStream,
    SECFiling,
    FilingAlert,
    FilingPriority,
    FormType,
    WatchlistEntry,
    monitor_entities,
    create_webhook_handler
)

__all__ = [
    "SECFilingStream",
    "SECFiling",
    "FilingAlert",
    "FilingPriority",
    "FormType",
    "WatchlistEntry",
    "monitor_entities",
    "create_webhook_handler"
]
