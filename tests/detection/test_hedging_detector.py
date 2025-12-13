"""
Tests for Hedging Language Detection
"""

import pytest
from src.detection.nlp.hedging_detector import HedgingDetector, HedgingResult


def test_hedging_detector_initialization():
    """Test HedgingDetector initialization."""
    detector = HedgingDetector()
    assert detector is not None
    assert len(detector.MODAL_VERBS) > 0
    assert len(detector.UNCERTAINTY_WORDS) > 0


def test_analyze_simple_text():
    """Test hedging analysis on simple text."""
    detector = HedgingDetector()
    
    text = "Revenue may increase substantially in the coming year."
    result = detector.analyze(text)
    
    assert isinstance(result, HedgingResult)
    assert result.total_words > 0
    assert result.hedge_count > 0
    assert result.hedging_density > 0
    assert len(result.hedges_found) > 0


def test_analyze_hedging_phrases():
    """Test detection of hedging phrases."""
    detector = HedgingDetector()
    
    text = "We believe revenue will increase. We expect growth to continue."
    result = detector.analyze(text)
    
    assert result.hedge_count >= 2  # At least "believe" and "expect"
    assert "hedging_phrases" in result.categories


def test_hedging_density_calculation():
    """Test hedging density calculation."""
    detector = HedgingDetector()
    
    # Text with known hedge count
    text = "may could should " * 10  # 30 words with 30 hedges
    result = detector.analyze(text)
    
    # Density should be 1000 (30 hedges per 30 words = 1000 per 1000 words)
    assert result.hedging_density == pytest.approx(1000, abs=10)


def test_compare_filings():
    """Test comparison of hedging between filings."""
    detector = HedgingDetector()
    
    filing1 = "Revenue increased by 20%. Profit grew steadily."
    filing2 = "Revenue may increase. We believe profit could grow."
    
    comparison = detector.compare_filings(filing1, filing2, "10-K 2022", "10-K 2023")
    
    assert "10-K 2022" in comparison
    assert "10-K 2023" in comparison
    assert "comparison" in comparison
    assert "density_change" in comparison["comparison"]


def test_get_risk_level():
    """Test risk level determination."""
    detector = HedgingDetector()
    
    # Low risk
    assert "LOW" in detector.get_risk_level(5.0)
    
    # Moderate risk
    assert "MODERATE" in detector.get_risk_level(15.0)
    
    # High risk
    assert "HIGH" in detector.get_risk_level(25.0)


def test_extract_hedged_statements():
    """Test extraction of hedged statements with context."""
    detector = HedgingDetector()
    
    text = "First sentence. Revenue may increase next year. Last sentence."
    statements = detector.extract_hedged_statements(text, context_window=20)
    
    assert len(statements) > 0
    assert any("may" in s["hedge"] for s in statements)
