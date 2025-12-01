"""
Phase 4: Temporal Analysis & Timeline Reconstruction
Advanced forensic timeline construction with contradiction detection.
"""

from .timeline_reconstructor import (
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

from .event_correlator import (
    EventCorrelator,
    EventCorrelation,
    CausalChain
)

from .temporal_parser import (
    TemporalParser,
    TemporalExtractor,
    DateExtractionResult
)

from .anomaly_detector import (
    TemporalAnomalyDetector,
    GapAnomaly,
    ClusterAnomaly,
    PatternBreak,
    AnomalyType
)

# Aliases for blueprint compatibility
AnomalyDetector = TemporalAnomalyDetector

__all__ = [
    'ForensicTimelineReconstructor',
    'TemporalEvent',
    'ForensicTimeline',
    'TemporalContradiction',
    'TemporalAnomaly',
    'NarrativeSequence',
    'CriticalPeriod',
    'EventType',
    'ContradictionType',
    'SeverityLevel',
    'TimelineResolution',
    'EventCorrelator',
    'EventCorrelation',
    'CausalChain',
    'TemporalParser',
    'TemporalExtractor',
    'DateExtractionResult',
    'TemporalAnomalyDetector',
    'AnomalyDetector',
    'GapAnomaly',
    'ClusterAnomaly',
    'PatternBreak',
    'AnomalyType'
]

