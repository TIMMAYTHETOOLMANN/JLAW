"""
JLAW Analysis Module
====================

Advanced forensic analysis components for narrative and text analysis.

Components:
- NarrativeAnalyzer: Management communication shift detection
"""

from .narrative_analyzer import (
    LinguisticMetrics,
    NarrativeAnalysisResult,
    NarrativeAnalyzer,
    NarrativeCategory,
    NarrativeSegment,
    NarrativeShift,
    ShiftSeverity,
)

__all__ = [
    "NarrativeAnalyzer",
    "NarrativeSegment",
    "NarrativeShift",
    "NarrativeAnalysisResult",
    "LinguisticMetrics",
    "ShiftSeverity",
    "NarrativeCategory",
]

__version__ = "1.0.0"
