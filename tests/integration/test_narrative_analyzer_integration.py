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
        score = analyzer._calculate_sentiment(text)
        assert score > 0
    
    def test_negative_sentiment(self):
        from src.forensics.analysis.narrative_analyzer import NarrativeAnalyzer
        
        analyzer = NarrativeAnalyzer()
        text = "Revenue declined significantly with challenging conditions."
        score = analyzer._calculate_sentiment(text)
        assert score < 0


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
