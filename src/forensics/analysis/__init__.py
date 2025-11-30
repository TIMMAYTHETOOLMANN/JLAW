"""
Analysis - Advanced Text and Narrative Analysis for Forensic Investigations

This module provides narrative analysis and sentiment detection capabilities
for identifying fraud patterns in management disclosures and earnings calls.
"""

from src.forensics.analysis.narrative_analyzer import (
    NarrativeAnalyzer,
    NarrativeShift,
    NarrativeAnalysisResult,
    SentimentScore,
    HedgingPattern,
    ToneShiftType,
    FraudIndicator,
)

__all__ = [
    "NarrativeAnalyzer",
    "NarrativeShift",
    "NarrativeAnalysisResult",
    "SentimentScore",
    "HedgingPattern",
    "ToneShiftType",
    "FraudIndicator",
]
