"""
Timeline Reconstructor - Legacy Stub (DEPRECATED)
=================================================

⚠️ This is a legacy stub file maintained for backward compatibility.
   The actual implementation (791 lines) is in src.forensics.temporal_analysis.timeline_reconstructor

For new code, import from:
    from src.forensics.temporal_analysis import ForensicTimelineReconstructor
"""

# Forward to actual implementation
from ..temporal_analysis.timeline_reconstructor import (
    ForensicTimelineReconstructor,
    TemporalEvent,
    ForensicTimeline,
    TemporalContradiction,
    TemporalAnomaly,
    NarrativeSequence,
    CriticalPeriod,
    EventType,
    ContradictionType,
    SeverityLevel,
    TimelineResolution
)

# Legacy alias
TimelineReconstructor = ForensicTimelineReconstructor

__all__ = [
    'ForensicTimelineReconstructor',
    'TimelineReconstructor',
    'TemporalEvent',
    'ForensicTimeline',
    'TemporalContradiction',
    'TemporalAnomaly',
    'NarrativeSequence',
    'CriticalPeriod',
    'EventType',
    'ContradictionType',
    'SeverityLevel',
    'TimelineResolution'
]

