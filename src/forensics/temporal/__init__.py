"""
JLAW Phase 4: Temporal Analysis and Timeline Reconstruction (Legacy Stub)
=========================================================================

⚠️ DEPRECATION NOTICE: This module is a legacy stub.
   All implementations have been moved to src.forensics.temporal_analysis
   This module forwards imports to the new location for backward compatibility.

For new code, import directly from:
    from src.forensics.temporal_analysis import (
        ForensicTimelineReconstructor,
        TemporalParser,
        EventCorrelator,
        AnomalyDetector
    )
"""

# Forward all imports to temporal_analysis for backward compatibility
try:
    from ..temporal_analysis import (
        ForensicTimelineReconstructor,
        TemporalParser,
        EventCorrelator,
        AnomalyDetector as TemporalAnomalyDetector,
        TemporalEvent,
        ForensicTimeline,
        TemporalContradiction,
    )
    
    # Legacy aliases
    TimelineReconstructor = ForensicTimelineReconstructor
    TemporalEventExtractor = TemporalParser
    EventExtractor = TemporalParser
    TemporalContradictionDetector = TemporalContradiction  # This is a dataclass
    
except ImportError as e:
    import warnings
    warnings.warn(f"Failed to import from temporal_analysis: {e}", ImportWarning)
    ForensicTimelineReconstructor = None
    TimelineReconstructor = None
    TemporalParser = None
    EventCorrelator = None
    TemporalAnomalyDetector = None

__all__ = [
    'ForensicTimelineReconstructor',
    'TimelineReconstructor',
    'TemporalParser',
    'TemporalEventExtractor',
    'EventExtractor',
    'TemporalContradiction',
    'TemporalContradictionDetector',
    'EventCorrelator',
    'TemporalAnomalyDetector',
]

__version__ = '4.0.0'
__phase__ = 4

