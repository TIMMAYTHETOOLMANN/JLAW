"""
Unit tests for Advanced Forensic Analytics Module (Module 1).
Tests graph-based contradiction detection and Beneish M-Score calculation.
"""

import pytest
import asyncio
from typing import Dict, List
import numpy as np

from src.forensics.advanced_forensic_analytics import (
    SemanticContradictionGraph,
    EnhancedFinancialForensics,
    AdvancedForensicAnalyzer,
    ContradictionDetection,
    BeneishMScore,
    AdvancedForensicResult
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_filing_text():
    """Sample filing text with contradictions."""
    return """
    The company reported revenue growth of 25% in Q1 2024. 
    Our gross margins improved significantly due to cost reductions.
    The company experienced a revenue decline of 15% in Q1 2024.
    Operating expenses increased substantially during the period.
    Cash flow from operations was strong and positive.
    The company faced significant cash flow challenges in the quarter.
    Management expects continued growth in the coming year.
    We anticipate further revenue declines in subsequent quarters.
    """


@pytest.fixture
def sample_financial_data():
    """Sample financial data for Beneish M-Score testing."""
    current = {
        'receivables': 500000000,
        'sales': 2000000000,
        'cogs': 1200000000,
        'current_assets': 800000000,
        'ppe': 1000000000,
        'total_assets': 3000000000,
        'depreciation': 100000000,
        'sga': 400000000,
        'debt': 1000000000,
        'income_continuing': 300000000,
        'cash_flow': 280000000
    }
    
    prior = {
        'receivables': 450000000,
        'sales': 1800000000,
        'cogs': 1100000000,
        'current_assets': 750000000,
        'ppe': 950000000,
        'total_assets': 2800000000,
        'depreciation': 95000000,
        'sga': 360000000,
        'debt': 900000000,
        'income_continuing': 280000000,
        'cash_flow': 270000000
    }
    
    return current, prior


@pytest.fixture
def manipulator_financial_data():
    """Financial data designed to trigger high M-Score (manipulator)."""
    current = {
        'receivables': 800000000,  # High receivables growth
        'sales': 2000000000,
        'cogs': 1400000000,  # Deteriorating margins
        'current_assets': 700000000,
        'ppe': 800000000,  # Lower quality assets
        'total_assets': 3000000000,
        'depreciation': 50000000,  # Low depreciation
        'sga': 450000000,  # High SG&A
        'debt': 1500000000,  # High leverage
        'income_continuing': 350000000,
        'cash_flow': 200000000  # High accruals
    }
    
    prior = {
        'receivables': 400000000,
        'sales': 1800000000,
        'cogs': 1100000000,
        'current_assets': 800000000,
        'ppe': 1000000000,
        'total_assets': 2800000000,
        'depreciation': 95000000,
        'sga': 360000000,
        'debt': 900000000,
        'income_continuing': 280000000,
        'cash_flow': 270000000
    }
    
    return current, prior


# ============================================================================
# SEMANTIC CONTRADICTION GRAPH TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_contradiction_graph_initialization():
    """Test SemanticContradictionGraph initialization."""
    try:
        detector = SemanticContradictionGraph()
        assert detector is not None
        assert detector.knowledge_graph is not None
        assert detector.embedder is not None
        assert detector.hash_chain is not None
    except ImportError as e:
        pytest.skip(f"Required dependencies not available: {e}")


@pytest.mark.asyncio
async def test_build_filing_graph(sample_filing_text):
    """Test knowledge graph building from filing text."""
    try:
        detector = SemanticContradictionGraph()
        
        claims_count = await detector.build_filing_graph(
            sample_filing_text,
            section_name="Test_Section"
        )
        
        assert claims_count > 0, "Should extract claims from text"
        assert detector.knowledge_graph.number_of_nodes() == claims_count
        
        # Verify hash chain logging
        assert len(detector.hash_chain.blocks) > 1
        
    except ImportError as e:
        pytest.skip(f"Required dependencies not available: {e}")


@pytest.mark.asyncio
async def test_detect_contradictions(sample_filing_text):
    """Test contradiction detection in filing text."""
    try:
        detector = SemanticContradictionGraph()
        
        await detector.build_filing_graph(sample_filing_text)
        contradictions = await detector.detect_contradictions(threshold=0.70)
        
        # Should detect contradictions in sample text
        assert len(contradictions) > 0, "Should detect contradictions in sample text"
        
        # Verify contradiction structure
        for c in contradictions:
            assert isinstance(c, ContradictionDetection)
            assert c.similarity_score >= 0.70
            assert c.severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
            assert c.contradiction_type == "SEMANTIC_CONTRADICTION"
            
    except ImportError as e:
        pytest.skip(f"Required dependencies not available: {e}")


@pytest.mark.asyncio
async def test_contradiction_severity_assessment():
    """Test contradiction severity levels."""
    try:
        detector = SemanticContradictionGraph()
        
        # Test with financial contradiction
        financial_text = """
        Revenue increased by 50% this quarter.
        The company experienced significant revenue declines.
        """
        
        await detector.build_filing_graph(financial_text)
        contradictions = await detector.detect_contradictions(threshold=0.70)
        
        # Financial contradictions should be high severity
        if contradictions:
            high_severity = any(c.severity in ["HIGH", "CRITICAL"] for c in contradictions)
            assert high_severity, "Financial contradictions should be high severity"
            
    except ImportError as e:
        pytest.skip(f"Required dependencies not available: {e}")


@pytest.mark.asyncio
async def test_graph_metrics():
    """Test knowledge graph metrics calculation."""
    try:
        detector = SemanticContradictionGraph()
        
        sample_text = "The company reported strong results. Revenue grew significantly."
        await detector.build_filing_graph(sample_text)
        
        metrics = detector.get_graph_metrics()
        
        assert 'node_count' in metrics
        assert 'edge_count' in metrics
        assert 'density' in metrics
        assert metrics['node_count'] >= 0
        
    except ImportError as e:
        pytest.skip(f"Required dependencies not available: {e}")


# ============================================================================
# BENEISH M-SCORE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_beneish_mscore_initialization():
    """Test EnhancedFinancialForensics initialization."""
    forensics = EnhancedFinancialForensics()
    assert forensics is not None
    assert forensics.hash_chain is not None


@pytest.mark.asyncio
async def test_calculate_beneish_mscore_normal(sample_financial_data):
    """Test Beneish M-Score calculation with normal company data."""
    forensics = EnhancedFinancialForensics()
    current, prior = sample_financial_data
    
    result = await forensics.calculate_beneish_mscore(current, prior)
    
    assert isinstance(result, BeneishMScore)
    assert isinstance(result.score, float)
    assert 0.0 <= result.probability <= 1.0
    assert result.risk_level in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN", "ERROR"]
    
    # Verify components
    expected_components = ['DSRI', 'GMI', 'AQI', 'SGI', 'DEPI', 'SGAI', 'LVGI', 'TATA']
    for component in expected_components:
        assert component in result.components
        assert isinstance(result.components[component], float)


@pytest.mark.asyncio
async def test_beneish_mscore_manipulator(manipulator_financial_data):
    """Test Beneish M-Score with manipulator-like data."""
    forensics = EnhancedFinancialForensics()
    current, prior = manipulator_financial_data
    
    result = await forensics.calculate_beneish_mscore(current, prior)
    
    # Should flag as potential manipulator
    assert result.score > -2.22 or result.manipulation_flag, \
        "Manipulator data should trigger high M-Score"
    
    assert result.risk_level in ["CRITICAL", "HIGH"], \
        "Manipulator should have high risk level"


@pytest.mark.asyncio
async def test_beneish_mscore_missing_data():
    """Test Beneish M-Score handling of missing data."""
    forensics = EnhancedFinancialForensics()
    
    # Incomplete data
    incomplete_current = {'sales': 1000000, 'receivables': 500000}
    incomplete_prior = {'sales': 900000, 'receivables': 450000}
    
    result = await forensics.calculate_beneish_mscore(
        incomplete_current,
        incomplete_prior
    )
    
    # Should handle gracefully
    assert isinstance(result, BeneishMScore)
    assert "Insufficient data" in result.interpretation or result.risk_level == "UNKNOWN"


@pytest.mark.asyncio
async def test_beneish_mscore_components():
    """Test individual Beneish M-Score components."""
    forensics = EnhancedFinancialForensics()
    
    # Create data with known component triggers
    current = {
        'receivables': 600000000,  # High DSRI
        'sales': 2000000000,
        'cogs': 1300000000,  # Deteriorating GMI
        'current_assets': 800000000,
        'ppe': 1000000000,
        'total_assets': 3000000000,
        'depreciation': 80000000,  # Lower DEPI
        'sga': 450000000,  # High SGAI
        'debt': 1200000000,  # High LVGI
        'income_continuing': 320000000,
        'cash_flow': 250000000  # High TATA (accruals)
    }
    
    prior = {
        'receivables': 450000000,
        'sales': 1800000000,
        'cogs': 1100000000,
        'current_assets': 750000000,
        'ppe': 950000000,
        'total_assets': 2800000000,
        'depreciation': 95000000,
        'sga': 360000000,
        'debt': 900000000,
        'income_continuing': 280000000,
        'cash_flow': 270000000
    }
    
    result = await forensics.calculate_beneish_mscore(current, prior)
    
    # DSRI should be elevated (receivables growing faster than sales)
    assert result.components['DSRI'] > 1.0
    
    # GMI should be elevated (deteriorating margins)
    assert result.components['GMI'] > 1.0


@pytest.mark.asyncio
async def test_beneish_mscore_integrity():
    """Test hash chain integrity for M-Score calculations."""
    forensics = EnhancedFinancialForensics()
    
    current = {
        'receivables': 500000000, 'sales': 2000000000, 'cogs': 1200000000,
        'current_assets': 800000000, 'ppe': 1000000000, 'total_assets': 3000000000,
        'depreciation': 100000000, 'sga': 400000000, 'debt': 1000000000,
        'income_continuing': 300000000, 'cash_flow': 280000000
    }
    prior = {
        'receivables': 450000000, 'sales': 1800000000, 'cogs': 1100000000,
        'current_assets': 750000000, 'ppe': 950000000, 'total_assets': 2800000000,
        'depreciation': 95000000, 'sga': 360000000, 'debt': 900000000,
        'income_continuing': 280000000, 'cash_flow': 270000000
    }
    
    await forensics.calculate_beneish_mscore(current, prior)
    
    # Verify hash chain
    assert len(forensics.hash_chain.blocks) > 1
    is_valid = await forensics.hash_chain.verify_chain()
    assert is_valid, "Hash chain should be valid"


# ============================================================================
# ADVANCED FORENSIC ANALYZER TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_advanced_analyzer_initialization():
    """Test AdvancedForensicAnalyzer initialization."""
    analyzer = AdvancedForensicAnalyzer()
    assert analyzer is not None
    assert analyzer.financial_forensics is not None
    assert analyzer.hash_chain is not None


@pytest.mark.asyncio
async def test_full_analysis(sample_filing_text, sample_financial_data):
    """Test full advanced forensic analysis."""
    analyzer = AdvancedForensicAnalyzer()
    current, prior = sample_financial_data
    
    result = await analyzer.analyze_filing(
        filing_text=sample_filing_text,
        current_financials=current,
        prior_financials=prior,
        cik="0001234567",
        filing_type="10-K"
    )
    
    assert isinstance(result, AdvancedForensicResult)
    assert result.cik == "0001234567"
    assert result.filing_type == "10-K"
    assert 0.0 <= result.overall_risk_score <= 1.0
    assert isinstance(result.contradictions, list)
    assert result.beneish_analysis is not None
    assert isinstance(result.critical_findings, list)


@pytest.mark.asyncio
async def test_analysis_without_financials(sample_filing_text):
    """Test analysis with only text (no financial data)."""
    analyzer = AdvancedForensicAnalyzer()
    
    result = await analyzer.analyze_filing(
        filing_text=sample_filing_text,
        current_financials=None,
        prior_financials=None,
        cik="0001234567",
        filing_type="10-K"
    )
    
    assert isinstance(result, AdvancedForensicResult)
    assert result.beneish_analysis is None  # Should be None without financials
    # Contradiction detection should still work
    if analyzer.contradiction_detector:
        assert isinstance(result.contradictions, list)


@pytest.mark.asyncio
async def test_critical_findings_detection(sample_filing_text, manipulator_financial_data):
    """Test detection of critical findings."""
    analyzer = AdvancedForensicAnalyzer()
    current, prior = manipulator_financial_data
    
    result = await analyzer.analyze_filing(
        filing_text=sample_filing_text,
        current_financials=current,
        prior_financials=prior,
        cik="0001234567",
        filing_type="10-K"
    )
    
    # Should have critical findings with manipulator data and contradictions
    assert len(result.critical_findings) > 0, \
        "Should detect critical findings with high-risk data"


@pytest.mark.asyncio
async def test_overall_risk_calculation():
    """Test overall risk score calculation."""
    analyzer = AdvancedForensicAnalyzer()
    
    # Simple text without contradictions
    simple_text = "The company performed well. Revenue increased."
    
    # Low-risk financials
    current = {
        'receivables': 450000000, 'sales': 2000000000, 'cogs': 1200000000,
        'current_assets': 800000000, 'ppe': 1000000000, 'total_assets': 3000000000,
        'depreciation': 100000000, 'sga': 400000000, 'debt': 900000000,
        'income_continuing': 300000000, 'cash_flow': 295000000
    }
    prior = {
        'receivables': 450000000, 'sales': 1900000000, 'cogs': 1140000000,
        'current_assets': 780000000, 'ppe': 980000000, 'total_assets': 2950000000,
        'depreciation': 98000000, 'sga': 390000000, 'debt': 880000000,
        'income_continuing': 290000000, 'cash_flow': 285000000
    }
    
    result = await analyzer.analyze_filing(
        filing_text=simple_text,
        current_financials=current,
        prior_financials=prior,
        cik="0001234567",
        filing_type="10-K"
    )
    
    # Low-risk data should produce low overall risk
    assert result.overall_risk_score < 0.5, \
        "Low-risk data should produce low overall risk score"


@pytest.mark.asyncio
async def test_integrity_verification():
    """Test integrity verification across all chains."""
    analyzer = AdvancedForensicAnalyzer()
    
    # Perform some analysis
    sample_text = "The company performed well."
    current = {
        'receivables': 500000000, 'sales': 2000000000, 'cogs': 1200000000,
        'current_assets': 800000000, 'ppe': 1000000000, 'total_assets': 3000000000,
        'depreciation': 100000000, 'sga': 400000000, 'debt': 1000000000,
        'income_continuing': 300000000, 'cash_flow': 280000000
    }
    prior = {
        'receivables': 450000000, 'sales': 1800000000, 'cogs': 1100000000,
        'current_assets': 750000000, 'ppe': 950000000, 'total_assets': 2800000000,
        'depreciation': 95000000, 'sga': 360000000, 'debt': 900000000,
        'income_continuing': 280000000, 'cash_flow': 270000000
    }
    
    await analyzer.analyze_filing(
        filing_text=sample_text,
        current_financials=current,
        prior_financials=prior
    )
    
    # Verify integrity
    is_valid = await analyzer.verify_integrity()
    assert is_valid, "All hash chains should be valid"


@pytest.mark.asyncio
async def test_graph_metrics_in_result(sample_filing_text):
    """Test that graph metrics are included in results."""
    analyzer = AdvancedForensicAnalyzer()
    
    result = await analyzer.analyze_filing(
        filing_text=sample_filing_text,
        cik="0001234567",
        filing_type="10-K"
    )
    
    assert isinstance(result.graph_metrics, dict)
    if analyzer.contradiction_detector:
        assert 'node_count' in result.graph_metrics


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_end_to_end_workflow(sample_filing_text, sample_financial_data):
    """Test complete end-to-end workflow."""
    # Initialize all components
    analyzer = AdvancedForensicAnalyzer()
    current, prior = sample_financial_data
    
    # Run full analysis
    result = await analyzer.analyze_filing(
        filing_text=sample_filing_text,
        current_financials=current,
        prior_financials=prior,
        cik="0001318605",
        filing_type="10-K"
    )
    
    # Verify all components present
    assert result is not None
    assert result.cik == "0001318605"
    assert result.filing_type == "10-K"
    assert result.timestamp is not None
    assert isinstance(result.overall_risk_score, float)
    assert isinstance(result.contradictions, list)
    assert isinstance(result.critical_findings, list)
    assert result.evidence_chain_hash is not None
    
    # Verify integrity
    is_valid = await analyzer.verify_integrity()
    assert is_valid


@pytest.mark.asyncio
async def test_backward_compatibility():
    """Test backward compatibility with existing JLAW system."""
    # Should be importable without errors
    from src.forensics import (
        AdvancedForensicAnalyzer,
        SemanticContradictionGraph,
        EnhancedFinancialForensics,
        BeneishMScore,
        ContradictionDetection,
        AdvancedForensicResult
    )
    
    # Should not break existing imports
    from src.forensics import (
        ForensicOrchestrator,
        SECForensicAnalyzer,
        AdvancedFraudDetector
    )
    
    assert True  # If we get here, imports work


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_performance_large_text():
    """Test performance with large text."""
    try:
        analyzer = AdvancedForensicAnalyzer()
        
        # Generate large text
        large_text = " ".join([
            "The company reported revenue growth. Expenses were controlled. "
            "Cash flow improved. Margins expanded. Operations were successful."
        ] * 100)  # 500 sentences
        
        import time
        start = time.time()
        
        result = await analyzer.analyze_filing(
            filing_text=large_text,
            cik="TEST",
            filing_type="10-K"
        )
        
        elapsed = time.time() - start
        
        assert result is not None
        assert elapsed < 30.0, f"Analysis took too long: {elapsed:.2f}s"
        
    except ImportError:
        pytest.skip("Required dependencies not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

