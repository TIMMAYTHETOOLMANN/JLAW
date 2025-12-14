"""Detection Patterns Module - Advanced fraud detection patterns."""

from .advanced_patterns import AdvancedPatternDetector, PatternAlert, PatternSeverity
from .options_backdating_detector import (
    OptionsBackdatingDetector,
    BackdatingAlert,
    BackdatingSeverity,
    GrantAnalysis
)
from .channel_stuffing_detector import (
    ChannelStuffingDetector,
    ChannelStuffingAlert,
    StuffingSeverity,
    QuarterlyMetrics,
    StuffingIndicator
)

__all__ = [
    'AdvancedPatternDetector',
    'PatternAlert',
    'PatternSeverity',
    'OptionsBackdatingDetector',
    'BackdatingAlert',
    'BackdatingSeverity',
    'GrantAnalysis',
    'ChannelStuffingDetector',
    'ChannelStuffingAlert',
    'StuffingSeverity',
    'QuarterlyMetrics',
    'StuffingIndicator'
]
