"""
Integration Tests: Benford's Law Analyzer Module
===============================================
JLAW Enhancement Protocol Compliance Test Suite
"""

import pytest
from typing import List


class TestBenfordAnalysis:
    """Tests for Benford's Law analysis."""
    
    def test_natural_data_distribution(self):
        from src.forensics.benfords_law_analyzer import BenfordsLawAnalyzer
        
        # Natural data following Benford's Law
        natural_data = [
            123, 234, 156, 178, 189, 145, 167, 198, 212, 256,
            278, 312, 345, 389, 412, 445, 478, 512, 567, 612
        ]
        
        analyzer = BenfordsLawAnalyzer()
        result = analyzer.analyze(natural_data)
        
        assert result is not None
        assert result.sample_size == len(natural_data)
    
    def test_z_score_calculation(self):
        from src.forensics.benfords_law_analyzer import BenfordsLawAnalyzer
        
        analyzer = BenfordsLawAnalyzer()
        
        observed = {1: 0.301, 2: 0.176, 3: 0.125}
        expected = {1: 0.301, 2: 0.176, 3: 0.125}
        
        z_scores = analyzer._calculate_z_scores(observed, expected, 100)
        
        assert z_scores is not None
        for digit, data in z_scores.items():
            assert "z_score" in data
            assert "anomaly_level" in data


class TestFraudProbability:
    """Tests for fraud probability scoring."""
    
    def test_fraud_probability_range(self):
        from src.forensics.benfords_law_analyzer import BenfordsLawAnalyzer
        
        analyzer = BenfordsLawAnalyzer()
        
        # Mock result object
        class MockResult:
            chi_squared_first = 15.0
            chi_squared_second = 12.0
            anomalous_digits = [5, 9]
            z_scores = {1: {"z_score": 2.1}, 2: {"z_score": 1.5}}
        
        result = analyzer.calculate_fraud_probability(MockResult())
        
        assert 0.0 <= result["fraud_probability"] <= 1.0
        assert result["risk_level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
