"""
Event Extractor - Legacy Stub (DEPRECATED)
==========================================

⚠️ This is a legacy stub file maintained for backward compatibility.
   The actual implementation is in src.forensics.temporal_analysis.temporal_parser

For new code, import from:
    from src.forensics.temporal_analysis import TemporalParser
"""

# Forward to actual implementation
from ..temporal_analysis.temporal_parser import (
    TemporalParser,
    TemporalExtractor,
    DateExtractionResult
)

# Legacy alias
EventExtractor = TemporalParser

__all__ = ['EventExtractor', 'TemporalParser', 'TemporalExtractor', 'DateExtractionResult']

