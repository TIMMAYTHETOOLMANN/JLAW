"""
Event Correlator - Legacy Stub (DEPRECATED)
===========================================

⚠️ This is a legacy stub file maintained for backward compatibility.
   The actual implementation is in src.forensics.temporal_analysis.event_correlator

For new code, import from:
    from src.forensics.temporal_analysis import EventCorrelator
"""

# Forward to actual implementation
from ..temporal_analysis.event_correlator import (
    EventCorrelator,
    EventCorrelation,
    CausalChain
)

__all__ = ['EventCorrelator', 'EventCorrelation', 'CausalChain']

