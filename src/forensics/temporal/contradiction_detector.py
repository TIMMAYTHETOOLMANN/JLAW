"""
Contradiction Detector - Legacy Stub (DEPRECATED)
=================================================

⚠️ This is a legacy stub file maintained for backward compatibility.
   The actual implementation is in src.forensics.temporal_analysis.timeline_reconstructor
   (TemporalContradiction is a dataclass defined there)

For new code, import from:
    from src.forensics.temporal_analysis import TemporalContradiction
"""

# Forward to actual implementation
from ..temporal_analysis.timeline_reconstructor import (
    TemporalContradiction,
    ContradictionType,
    SeverityLevel
)

__all__ = ['TemporalContradiction', 'ContradictionType', 'SeverityLevel']

