"""
JLAW Phase 4: Temporal Analysis and Timeline Reconstruction
===========================================================

Advanced temporal intelligence for forensic investigations.

Components:
- ForensicTimelineReconstructor: Multi-document event ordering and correlation
- TemporalEventExtractor: Date/time extraction from unstructured text
- TemporalContradictionDetector: Cross-document timeline validation
- EventCorrelator: Cross-timeline entity correlation
- CausalChainIdentifier: DAG-based causal inference
- TemporalAnomalyDetector: Gap/clustering/pattern detection
"""

try:
    from .timeline_reconstructor import TimelineReconstructor
    from .event_extractor import EventExtractor
    
    # Aliases for backward compatibility
    ForensicTimelineReconstructor = TimelineReconstructor
    TemporalEventExtractor = EventExtractor
    TemporalContradictionDetector = None
    EventCorrelator = None
    TemporalAnomalyDetector = None
except ImportError:
    TimelineReconstructor = None
    ForensicTimelineReconstructor = None

__all__ = [
    'TimelineReconstructor',
    'ForensicTimelineReconstructor',
    'EventExtractor',
    'TemporalEventExtractor',
    'TemporalContradictionDetector',
    'EventCorrelator',
    'TemporalAnomalyDetector',
]

__version__ = '4.0.0'
__phase__ = 4

