"""
NLP Detection Module
===================

Natural Language Processing for SEC filings analysis.

This module provides advanced NLP capabilities for detecting:
- Contradictions between statements in SEC filings
- Hedging language indicating uncertainty
- Financial sentiment analysis
- SEC filing-specific embeddings

All detectors support both full model mode and mock mode for testing.
"""

from src.detection.nlp.contradiction_detector import (
    ContradictionDetector,
    Statement,
    ContradictionResult
)

from src.detection.nlp.hedging_detector import (
    HedgingDetector,
    HedgingResult
)

from src.detection.nlp.financial_models import (
    FinBERTAnalyzer,
    SECBERTEmbedder,
    Sentiment,
    SentimentResult
)

__all__ = [
    # Contradiction detection
    'ContradictionDetector',
    'Statement',
    'ContradictionResult',
    
    # Hedging detection
    'HedgingDetector',
    'HedgingResult',
    
    # Financial NLP models
    'FinBERTAnalyzer',
    'SECBERTEmbedder',
    'Sentiment',
    'SentimentResult'
]
