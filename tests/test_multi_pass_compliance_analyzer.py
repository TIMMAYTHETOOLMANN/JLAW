"""
Unit tests for Multi-Pass Compliance Analyzer.
Tests 4-pass forensic compliance checking methodology.
"""

import pytest
import asyncio
from typing import Dict, Any

from src.forensics.multi_pass_compliance_analyzer import (
    MultiPassComplianceAnalyzer,
    ComplianceViolation,
    ComplianceSeverity,
    RiskLevel,
    ComplianceAnalysisResult,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def valid_10k_content():
    """Sample valid 10-K filing content."""
    return """
    BUSINESS SECTION
    The company operates in three primary segments...
    
    RISK FACTORS
    Market volatility may impact our results. Competition is intense.
    
    MANAGEMENT'S DISCUSSION AND ANALYSIS
    Revenue increased 15% year-over-year to $10 million.
    Operating expenses decreased by 5%.
    
    FINANCIAL STATEMENTS
    Revenue: $10,000,000
    Cost of Goods Sold: $6,000,000
    Gross Profit: $4,000,000
    Operating Expenses: $2,500,000
    Net Income: $1,500,000
    Total Assets: $25,000,000
    Total Liabilities: $10,000,000
    
    CONTROLS AND PROCEDURES
    Management has evaluated the effectiveness of internal controls.
    
    Forward-looking statements are included herein.
    Safe Harbor: This document contains forward-looking statements.
    
    Exhibit 10.1 - Material Contracts
    Exhibit 31.1 - CEO Certification
    """


@pytest.fixture
def incomplete_10k_content():
    """Sample incomplete 10-K filing (missing required sections)."""
    return """
    BUSINESS SECTION
    The company operates in technology sector.
    
    Some financial information is provided here.
    Revenue was $5 million.
    """


@pytest.fixture
def valid_financial_data():
    """Sample valid financial data."""
    return {
        'revenue': 10000000,
        'earnings': 1500000,
        'total_assets': 25000000,
        'total_liabilities': 10000000,
        'cash_flow': 2000000,
    }


@pytest.fixture
def problematic_financial_data():
    """Sample financial data with red flags."""
    return {
        'revenue': -1000000,  # Negative revenue - critical issue
        'earnings': 8000000,  # Extremely high margin
        'total_assets': 5000000,
        'total_liabilities': 15000000,  # High leverage
    }


@pytest.fixture
def unusual_margin_financial_data():
    """Sample financial data with unusual profit margins."""
    return {
        'revenue': 1000000,
        'earnings': 900000,  # 90% margin - suspicious
        'total_assets': 5000000,
        'total_liabilities': 2000000,
    }


# ============================================================================
# TESTS - Basic Functionality
# ============================================================================

@pytest.mark.asyncio
async def test_analyzer_initialization():
    """Test analyzer initializes correctly."""
    analyzer = MultiPassComplianceAnalyzer()
    
    assert analyzer is not None
    assert len(analyzer.violations) == 0
    assert len(analyzer.pass_results) == 0


@pytest.mark.asyncio
async def test_analyze_valid_10k(valid_10k_content, valid_financial_data):
    """Test analysis of valid 10-K content."""
    analyzer = MultiPassComplianceAnalyzer()
    
    result = await analyzer.analyze(
        content=valid_10k_content,
        financial_data=valid_financial_data,
        filing_type="10-K"
    )
    
    assert isinstance(result, ComplianceAnalysisResult)
    assert result.total_checks > 0
    assert result.passed_checks > 0
    assert result.risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]


@pytest.mark.asyncio
async def test_analyze_incomplete_10k(incomplete_10k_content):
    """Test analysis of incomplete 10-K (should find violations)."""
    analyzer = MultiPassComplianceAnalyzer()
    
    result = await analyzer.analyze(
        content=incomplete_10k_content,
        filing_type="10-K"
    )
    
    # Should detect missing required sections
    assert len(result.violations) > 0
    assert result.failed_checks > 0


# ============================================================================
# TESTS - Pass 1: Structural Validation
# ============================================================================

@pytest.mark.asyncio
async def test_pass1_detects_missing_sections(incomplete_10k_content):
    """Test Pass 1 detects missing required sections."""
    analyzer = MultiPassComplianceAnalyzer()
    
    result = await analyzer.analyze(
        content=incomplete_10k_content,
        filing_type="10-K"
    )
    
    # Should have violations for missing sections
    missing_section_violations = [
        v for v in result.violations 
        if v.violation_type == "missing_required_section"
    ]
    assert len(missing_section_violations) > 0
    
    # Should have pass 1 results
    assert "structural_validation" in result.pass_results
    assert result.pass_results["structural_validation"]["pass_completed"]


@pytest.mark.asyncio
async def test_pass1_detects_short_content():
    """Test Pass 1 detects suspiciously short content."""
    analyzer = MultiPassComplianceAnalyzer()
    
    short_content = "This is a very short document."
    result = await analyzer.analyze(
        content=short_content,
        filing_type="10-K"
    )
    
    # Should detect insufficient content
    insufficient_violations = [
        v for v in result.violations 
        if v.violation_type == "insufficient_content"
    ]
    assert len(insufficient_violations) > 0
    assert insufficient_violations[0].severity == ComplianceSeverity.CRITICAL


@pytest.mark.asyncio
async def test_pass1_validates_all_required_sections():
    """Test Pass 1 validates all required sections for 10-K."""
    analyzer = MultiPassComplianceAnalyzer()
    
    # Content with all required sections
    complete_content = """
    Business: Company overview
    Risk Factors: Various risks
    Management's Discussion and Analysis: Financial analysis
    Financial Statements: Complete financials
    Controls and Procedures: Internal controls
    """ * 100  # Make it long enough
    
    result = await analyzer.analyze(
        content=complete_content,
        filing_type="10-K"
    )
    
    # Should have fewer violations than incomplete content
    missing_violations = [
        v for v in result.violations 
        if v.violation_type == "missing_required_section"
    ]
    assert len(missing_violations) == 0


# ============================================================================
# TESTS - Pass 2: Financial Consistency
# ============================================================================

@pytest.mark.asyncio
async def test_pass2_detects_negative_revenue(problematic_financial_data):
    """Test Pass 2 detects negative revenue."""
    analyzer = MultiPassComplianceAnalyzer()
    
    result = await analyzer.analyze(
        content="Sample content " * 100,
        financial_data=problematic_financial_data,
        filing_type="10-K"
    )
    
    # Should detect negative revenue
    negative_revenue_violations = [
        v for v in result.violations 
        if v.violation_type == "negative_revenue"
    ]
    assert len(negative_revenue_violations) > 0
    assert negative_revenue_violations[0].severity == ComplianceSeverity.CRITICAL


@pytest.mark.asyncio
async def test_pass2_detects_unusual_margins(unusual_margin_financial_data):
    """Test Pass 2 detects unusual profit margins."""
    analyzer = MultiPassComplianceAnalyzer()
    
    result = await analyzer.analyze(
        content="Sample content " * 100,
        financial_data=unusual_margin_financial_data,
        filing_type="10-K"
    )
    
    # Should detect unusual profit margin
    margin_violations = [
        v for v in result.violations 
        if v.violation_type == "unusual_profit_margin"
    ]
    assert len(margin_violations) > 0
    assert margin_violations[0].severity == ComplianceSeverity.MEDIUM


@pytest.mark.asyncio
async def test_pass2_detects_high_leverage(problematic_financial_data):
    """Test Pass 2 detects high leverage (debt-to-asset ratio)."""
    analyzer = MultiPassComplianceAnalyzer()
    
    result = await analyzer.analyze(
        content="Sample content " * 100,
        financial_data=problematic_financial_data,
        filing_type="10-K"
    )
    
    # Should detect high leverage
    leverage_violations = [
        v for v in result.violations 
        if v.violation_type == "debt_to_asset_ratio_high"
    ]
    assert len(leverage_violations) > 0
    assert leverage_violations[0].severity == ComplianceSeverity.HIGH


@pytest.mark.asyncio
async def test_pass2_skips_without_financial_data():
    """Test Pass 2 skips when no financial data provided."""
    analyzer = MultiPassComplianceAnalyzer()
    
    result = await analyzer.analyze(
        content="Sample content " * 100,
        financial_data=None,
        filing_type="10-K"
    )
    
    # Should have pass 2 results indicating it was skipped
    assert "financial_consistency" in result.pass_results
    assert not result.pass_results["financial_consistency"]["pass_completed"]


# ============================================================================
# TESTS - Pass 3: Legal Compliance
# ============================================================================

@pytest.mark.asyncio
async def test_pass3_detects_missing_risk_factors():
    """Test Pass 3 detects missing risk factors disclosure."""
    analyzer = MultiPassComplianceAnalyzer()
    
    content_without_risks = """
    Business: Company operations
    Financial data is here
    """ * 50
    
    result = await analyzer.analyze(
        content=content_without_risks,
        filing_type="10-K"
    )
    
    # Should detect missing risk factors
    risk_violations = [
        v for v in result.violations 
        if v.violation_type == "missing_risk_factors"
    ]
    assert len(risk_violations) > 0
    assert risk_violations[0].severity == ComplianceSeverity.HIGH


@pytest.mark.asyncio
async def test_pass3_detects_missing_mda():
    """Test Pass 3 detects missing MD&A section."""
    analyzer = MultiPassComplianceAnalyzer()
    
    content_without_mda = """
    Business section here
    Risk Factors: Various risks
    """ * 50
    
    result = await analyzer.analyze(
        content=content_without_mda,
        filing_type="10-K"
    )
    
    # Should detect missing MD&A
    mda_violations = [
        v for v in result.violations 
        if v.violation_type == "missing_mda"
    ]
    assert len(mda_violations) > 0
    assert mda_violations[0].severity == ComplianceSeverity.CRITICAL


@pytest.mark.asyncio
async def test_pass3_identifies_material_weakness():
    """Test Pass 3 identifies material weakness disclosure."""
    analyzer = MultiPassComplianceAnalyzer()
    
    content_with_weakness = """
    Business operations
    Risk Factors: Various risks
    Management's Discussion and Analysis: Financial review
    We identified a material weakness in our internal controls.
    """ * 25
    
    result = await analyzer.analyze(
        content=content_with_weakness,
        filing_type="10-K"
    )
    
    # Should identify material weakness (INFO level)
    weakness_violations = [
        v for v in result.violations 
        if v.violation_type == "material_weakness_disclosed"
    ]
    assert len(weakness_violations) > 0
    assert weakness_violations[0].severity == ComplianceSeverity.INFO


@pytest.mark.asyncio
async def test_pass3_only_runs_for_periodic_filings():
    """Test Pass 3 legal checks vary by filing type."""
    analyzer = MultiPassComplianceAnalyzer()
    
    content = "Sample content " * 100
    
    # Run for 10-K
    result_10k = await analyzer.analyze(content=content, filing_type="10-K")
    
    # Run for 8-K
    result_8k = await analyzer.analyze(content=content, filing_type="8-K")
    
    # 10-K should have more checks
    assert "legal_compliance" in result_10k.pass_results
    assert "legal_compliance" in result_8k.pass_results


# ============================================================================
# TESTS - Pass 4: Cross-Reference Validation
# ============================================================================

@pytest.mark.asyncio
async def test_pass4_detects_exhibits():
    """Test Pass 4 detects exhibit references."""
    analyzer = MultiPassComplianceAnalyzer()
    
    content_with_exhibits = """
    Business operations described here.
    See Exhibit 10.1 for material contracts.
    Refer to Exhibit 31.1 for certifications.
    """ * 25
    
    result = await analyzer.analyze(
        content=content_with_exhibits,
        filing_type="10-K"
    )
    
    # Should have cross-reference validation results
    assert "cross_reference_validation" in result.pass_results


@pytest.mark.asyncio
async def test_pass4_detects_missing_safe_harbor():
    """Test Pass 4 detects forward-looking statements without safe harbor."""
    analyzer = MultiPassComplianceAnalyzer()
    
    content_without_safe_harbor = """
    Business operations
    Forward-looking statements about future growth
    We expect revenue to double next year.
    """ * 25
    
    result = await analyzer.analyze(
        content=content_without_safe_harbor,
        filing_type="10-K"
    )
    
    # Should detect missing safe harbor
    safe_harbor_violations = [
        v for v in result.violations 
        if v.violation_type == "missing_safe_harbor"
    ]
    assert len(safe_harbor_violations) > 0
    assert safe_harbor_violations[0].severity == ComplianceSeverity.MEDIUM


@pytest.mark.asyncio
async def test_pass4_accepts_safe_harbor_language():
    """Test Pass 4 accepts forward-looking statements with safe harbor."""
    analyzer = MultiPassComplianceAnalyzer()
    
    content_with_safe_harbor = """
    Business operations
    Forward-looking statements about future growth
    Safe Harbor: These forward-looking statements are subject to risks.
    """ * 25
    
    result = await analyzer.analyze(
        content=content_with_safe_harbor,
        filing_type="10-K"
    )
    
    # Should not have safe harbor violation
    safe_harbor_violations = [
        v for v in result.violations 
        if v.violation_type == "missing_safe_harbor"
    ]
    assert len(safe_harbor_violations) == 0


# ============================================================================
# TESTS - Risk Scoring
# ============================================================================

@pytest.mark.asyncio
async def test_risk_score_calculation_low():
    """Test risk score calculation for low-risk filing."""
    analyzer = MultiPassComplianceAnalyzer()
    
    result = await analyzer.analyze(
        content="""
        Business: Operations
        Risk Factors: Standard risks
        Management's Discussion and Analysis: Review
        Financial Statements: Complete
        Controls and Procedures: Effective
        Safe Harbor language included
        """ * 100,
        financial_data={'revenue': 1000000, 'earnings': 100000, 
                       'total_assets': 5000000, 'total_liabilities': 2000000},
        filing_type="10-K"
    )
    
    assert result.risk_score < 0.4
    assert result.risk_level == RiskLevel.LOW


@pytest.mark.asyncio
async def test_risk_score_calculation_high():
    """Test risk score calculation for high-risk filing."""
    analyzer = MultiPassComplianceAnalyzer()
    
    # Incomplete with problematic financials
    result = await analyzer.analyze(
        content="Minimal content",
        financial_data={'revenue': -1000000, 'earnings': 100000,
                       'total_assets': 1000000, 'total_liabilities': 5000000},
        filing_type="10-K"
    )
    
    assert result.risk_score > 0.4
    assert result.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]


@pytest.mark.asyncio
async def test_risk_level_determination():
    """Test risk level determination from score."""
    analyzer = MultiPassComplianceAnalyzer()
    
    # Test different risk levels
    assert analyzer._determine_risk_level(0.95) == RiskLevel.CRITICAL
    assert analyzer._determine_risk_level(0.75) == RiskLevel.HIGH
    assert analyzer._determine_risk_level(0.50) == RiskLevel.MEDIUM
    assert analyzer._determine_risk_level(0.20) == RiskLevel.LOW


# ============================================================================
# TESTS - Violation Details
# ============================================================================

@pytest.mark.asyncio
async def test_violation_structure():
    """Test violation structure contains required fields."""
    analyzer = MultiPassComplianceAnalyzer()
    
    result = await analyzer.analyze(
        content="Short content",
        filing_type="10-K"
    )
    
    if len(result.violations) > 0:
        violation = result.violations[0]
        assert hasattr(violation, 'violation_type')
        assert hasattr(violation, 'severity')
        assert hasattr(violation, 'description')
        assert hasattr(violation, 'evidence')
        assert hasattr(violation, 'pass_number')
        assert hasattr(violation, 'confidence')
        assert isinstance(violation.severity, ComplianceSeverity)


@pytest.mark.asyncio
async def test_violations_have_pass_numbers():
    """Test all violations have pass numbers assigned."""
    analyzer = MultiPassComplianceAnalyzer()
    
    result = await analyzer.analyze(
        content="Minimal content",
        financial_data={'revenue': -100000},
        filing_type="10-K"
    )
    
    for violation in result.violations:
        assert violation.pass_number in [1, 2, 3, 4]


# ============================================================================
# TESTS - Summary Generation
# ============================================================================

@pytest.mark.asyncio
async def test_summary_generation():
    """Test summary contains key information."""
    analyzer = MultiPassComplianceAnalyzer()
    
    result = await analyzer.analyze(
        content="Sample content " * 100,
        filing_type="10-K"
    )
    
    assert len(result.summary) > 0
    assert "checks" in result.summary.lower()
    assert str(result.total_checks) in result.summary


@pytest.mark.asyncio
async def test_summary_includes_severity_counts():
    """Test summary includes violation severity counts."""
    analyzer = MultiPassComplianceAnalyzer()
    
    result = await analyzer.analyze(
        content="Short",
        financial_data={'revenue': -100000},
        filing_type="10-K"
    )
    
    # Summary should mention different severity levels
    assert any(severity.value in result.summary for severity in ComplianceSeverity)


# ============================================================================
# TESTS - Metadata
# ============================================================================

@pytest.mark.asyncio
async def test_result_includes_metadata():
    """Test result includes metadata when provided."""
    analyzer = MultiPassComplianceAnalyzer()
    
    metadata = {'company': 'Test Corp', 'cik': '0001234567'}
    
    result = await analyzer.analyze(
        content="Sample content " * 100,
        metadata=metadata,
        filing_type="10-K"
    )
    
    assert result.metadata == metadata


@pytest.mark.asyncio
async def test_result_has_timestamp():
    """Test result has timestamp."""
    analyzer = MultiPassComplianceAnalyzer()
    
    result = await analyzer.analyze(
        content="Sample content " * 100,
        filing_type="10-K"
    )
    
    assert result.timestamp is not None
    assert len(result.timestamp) > 0


# ============================================================================
# TESTS - Integration
# ============================================================================

@pytest.mark.asyncio
async def test_all_passes_execute():
    """Test all 4 passes execute in sequence."""
    analyzer = MultiPassComplianceAnalyzer()
    
    result = await analyzer.analyze(
        content="""
        Business, Risk Factors, Management's Discussion and Analysis,
        Financial Statements, Controls and Procedures
        """ * 50,
        financial_data={'revenue': 1000000, 'earnings': 100000},
        filing_type="10-K"
    )
    
    # All 4 passes should have results
    assert "structural_validation" in result.pass_results
    assert "financial_consistency" in result.pass_results
    assert "legal_compliance" in result.pass_results
    assert "cross_reference_validation" in result.pass_results


@pytest.mark.asyncio
async def test_multiple_analyses_independent():
    """Test multiple analyses don't interfere with each other."""
    analyzer = MultiPassComplianceAnalyzer()
    
    result1 = await analyzer.analyze(content="Content 1" * 100, filing_type="10-K")
    result2 = await analyzer.analyze(content="Content 2" * 100, filing_type="10-Q")
    
    # Results should be independent
    assert result1.violations != result2.violations
    assert result1.total_checks != result2.total_checks
