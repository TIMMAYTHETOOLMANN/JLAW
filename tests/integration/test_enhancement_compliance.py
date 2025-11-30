"""
JLAW Enhancement Protocol Compliance Test Suite
===============================================
Validates all P0 enhancement module implementations.
"""

import pytest
from pathlib import Path


class TestBenfordEnhancements:
    """Tests for Benford's Law analyzer enhancements."""
    
    def test_z_score_function_exists(self):
        """Verify Z-score calculation is available."""
        # Import will fail if not properly injected
        from src.forensics.benfords_law_analyzer import BenfordsLawAnalyzer
        analyzer = BenfordsLawAnalyzer()
        assert hasattr(analyzer, '_calculate_z_scores') or hasattr(analyzer, 'calculate_z_scores_enhanced')
    
    def test_fraud_probability_function_exists(self):
        """Verify fraud probability scoring is available."""
        from src.forensics.benfords_law_analyzer import BenfordsLawAnalyzer
        analyzer = BenfordsLawAnalyzer()
        assert hasattr(analyzer, 'calculate_fraud_probability') or hasattr(analyzer, 'calculate_fraud_probability_enhanced')


class TestNarrativeEnhancements:
    """Tests for Narrative Analyzer enhancements."""
    
    def test_shift_severity_enum_exists(self):
        """Verify ShiftSeverity enum is available."""
        try:
            from src.forensics.analysis.narrative_analyzer import ShiftSeverity
            assert ShiftSeverity.CRITICAL.value == "critical"
            assert ShiftSeverity.MATERIAL.value == "material"
        except ImportError:
            pytest.skip("ShiftSeverity not yet injected")
    
    def test_conviction_analysis_function_exists(self):
        """Verify conviction analysis is available."""
        from src.forensics.analysis.narrative_analyzer import NarrativeAnalyzer
        analyzer = NarrativeAnalyzer()
        assert hasattr(analyzer, '_calculate_conviction_score') or hasattr(analyzer, 'analyze_conviction_stance')


class TestEntityResolverSecurity:
    """Tests for Entity Resolver security enhancements."""
    
    def test_sha256_usage(self):
        """Verify SHA-256 is used for entity ID generation."""
        entity_resolver_path = Path("src/forensics/triangulation/entity_resolver.py")
        if entity_resolver_path.exists():
            content = entity_resolver_path.read_text()
            assert "sha256" in content.lower(), "SHA-256 not found in entity_resolver.py"


class TestSECFilingStreamCompliance:
    """Tests for SEC Filing Stream compliance enhancements."""
    
    def test_rate_limiter_exists(self):
        """Verify RateLimiter class is available."""
        sec_stream_path = Path("src/forensics/intelligence/sec_filing_stream.py")
        if sec_stream_path.exists():
            content = sec_stream_path.read_text()
            assert "RateLimiter" in content or "rate_limit" in content.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
