"""
Integration Tests: Narrative Analyzer Module
============================================
JLAW Enhancement Protocol Compliance Test Suite
"""

import pytest
from typing import List, Dict, Any


class TestSentimentAnalysis:
    """Tests for sentiment analysis functionality."""
    
    def test_positive_sentiment(self):
        from src.forensics.analysis.narrative_analyzer import NarrativeAnalyzer
        
        analyzer = NarrativeAnalyzer()
        text = "Revenue growth exceeded expectations with strong performance."
        result = analyzer._analyze_sentiment(text)
        assert result.compound_score > 0 or result.positive_score > result.negative_score
    
    def test_negative_sentiment(self):
        from src.forensics.analysis.narrative_analyzer import NarrativeAnalyzer
        
        analyzer = NarrativeAnalyzer()
        text = "Revenue declined significantly with challenging conditions."
        result = analyzer._analyze_sentiment(text)
        assert result.compound_score < 0 or result.negative_score > result.positive_score


class TestConvictionAnalysis:
    """Tests for conviction score calculation."""
    
    def test_high_conviction(self):
        from src.forensics.analysis.narrative_analyzer import NarrativeAnalyzer
        
        analyzer = NarrativeAnalyzer()
        text = "We are confident and certain about our strong robust performance."
        result = analyzer._calculate_conviction_score(text)
        assert result["conviction_score"] > 0
    
    def test_high_hedging(self):
        from src.forensics.analysis.narrative_analyzer import NarrativeAnalyzer
        
        analyzer = NarrativeAnalyzer()
        text = "We might possibly see approximately uncertain results if conditions change."
        result = analyzer._calculate_conviction_score(text)
        assert result["conviction_score"] < 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
